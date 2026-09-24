"""Comprehensive unit tests for py-git-properties.

Tests all sync APIs, async APIs, camelCase aliases, CLI modes, formatters,
worktree handling, and CI fallbacks with zero external dependencies.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import py_git_properties as pgp
from py_git_properties.constants import (
    KEY_GIT_BRANCH,
    KEY_GIT_BUILD_HOST,
    KEY_GIT_BUILD_VERSION,
    KEY_GIT_COMMIT_ID,
    KEY_GIT_COMMIT_ID_ABBREVIATED,
    KEY_GIT_COMMIT_FULL_MESSAGE,
    KEY_GIT_COMMIT_SHORT_MESSAGE,
    KEY_GIT_COMMIT_TIME,
    KEY_GIT_COMMIT_USER_EMAIL,
    KEY_GIT_COMMIT_USER_NAME,
    KEY_GIT_DIRTY,
    KEY_GIT_REMOTE_ORIGIN_URL,
    KEY_GIT_TOTAL_COMMIT_COUNT,
)
from py_git_properties.core import (
    _format_property_value,
    _cast_object_to_nested_object,
    _deep_merge,
    _EnvFallback,
    _get_git_dir,
)
from py_git_properties.cli import run_cli, CliResult


class TestGitPropertiesCoreSync(unittest.TestCase):
    """Test core synchronous functions on the current repository."""

    def test_current_branch(self):
        branch = pgp.current_branch()
        self.assertIsInstance(branch, str)
        self.assertTrue(len(branch) > 0)

    def test_build_host(self):
        host = pgp.build_host()
        self.assertIsInstance(host, str)
        self.assertTrue(len(host) > 0)

    def test_build_version(self):
        ver = pgp.build_version()
        self.assertIsInstance(ver, str)
        self.assertEqual(ver, "1.0.0")

    def test_commit_id_abbrev(self):
        abbrev = pgp.commit_id_abbrev()
        self.assertIsInstance(abbrev, str)
        self.assertGreaterEqual(len(abbrev), 4)

    def test_commit_id_full(self):
        full = pgp.commit_id_full()
        self.assertIsInstance(full, str)
        self.assertEqual(len(full), 40)

    def test_commit_messages(self):
        short = pgp.last_commit_msg(short=True)
        full = pgp.last_commit_msg(short=False)
        self.assertIsInstance(short, str)
        self.assertIsInstance(full, str)
        self.assertTrue(len(short) > 0)
        self.assertTrue(full.startswith(short))

    def test_commit_user_info(self):
        name = pgp.commit_user_info(email=False)
        email = pgp.commit_user_info(email=True)
        self.assertIsInstance(name, str)
        self.assertIsInstance(email, str)
        self.assertTrue(len(name) > 0)
        self.assertIn("@", email)

    def test_date_of_last_commit(self):
        date_str = pgp.date_of_last_commit()
        self.assertIsInstance(date_str, str)
        self.assertTrue(len(date_str) > 0)

    def test_is_dirty(self):
        dirty = pgp.is_dirty()
        self.assertIsInstance(dirty, bool)

    def test_remote_url(self):
        url = pgp.remote_url()
        self.assertIsInstance(url, str)
        self.assertIn("py-git-properties", url)

    def test_count_of_all_commits(self):
        count = pgp.count_of_all_commits()
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_get_git_prop_keys(self):
        props = pgp.get_git_prop()
        self.assertIsInstance(props, dict)
        expected_keys = [
            KEY_GIT_BRANCH,
            KEY_GIT_BUILD_HOST,
            KEY_GIT_BUILD_VERSION,
            KEY_GIT_COMMIT_ID,
            KEY_GIT_COMMIT_ID_ABBREVIATED,
            KEY_GIT_COMMIT_SHORT_MESSAGE,
            KEY_GIT_COMMIT_FULL_MESSAGE,
            KEY_GIT_COMMIT_USER_NAME,
            KEY_GIT_COMMIT_USER_EMAIL,
            KEY_GIT_COMMIT_TIME,
            KEY_GIT_DIRTY,
            KEY_GIT_REMOTE_ORIGIN_URL,
            KEY_GIT_TOTAL_COMMIT_COUNT,
        ]
        for key in expected_keys:
            self.assertIn(key, props)

    def test_get_git_prop_with_custom_map(self):
        custom = {"custom.build.number": "42", "custom.env": "production"}
        props = pgp.get_git_prop(custom)
        self.assertEqual(props.get("custom.build.number"), "42")
        self.assertEqual(props.get("custom.env"), "production")

    def test_git_info_as_json(self):
        # As parsed object
        obj = pgp.git_info_as_json(require_object=True)
        self.assertIsInstance(obj, dict)
        self.assertIn("git", obj)
        self.assertIn("branch", obj["git"])
        self.assertIn("commit", obj["git"])
        self.assertIn("id", obj["git"]["commit"])
        self.assertIn("abbrev", obj["git"]["commit"]["id"])
        self.assertIn("full", obj["git"]["commit"]["id"])

        # As JSON string
        json_str = pgp.git_info_as_json(require_object=False)
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["git"]["branch"], obj["git"]["branch"])

    def test_git_info_as_properties(self):
        prop_str = pgp.git_info_as_properties()
        self.assertIsInstance(prop_str, str)
        self.assertIn("git.branch=", prop_str)
        self.assertIn("git.commit.id.full=", prop_str)
        self.assertIn("git.build.version=1.0.0", prop_str)


class TestGitPropertiesCoreAsync(unittest.IsolatedAsyncioTestCase):
    """Test core asynchronous APIs."""

    async def test_async_core_functions(self):
        branch = await pgp.current_branch_async()
        abbrev = await pgp.commit_id_abbrev_async()
        full = await pgp.commit_id_full_async()
        props = await pgp.get_git_prop_async()
        json_obj = await pgp.git_info_as_json_async(require_object=True)
        prop_str = await pgp.git_info_as_properties_async()

        self.assertIsInstance(branch, str)
        self.assertIsInstance(abbrev, str)
        self.assertEqual(len(full), 40)
        self.assertEqual(props[KEY_GIT_BRANCH], branch)
        self.assertEqual(json_obj["git"]["branch"], branch)
        self.assertIn("git.branch=", prop_str)


class TestFileCreation(unittest.TestCase):
    """Test creating output files in JSON, flat-JSON, and properties formats."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="git_props_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_json_file(self):
        target = Path(self.test_dir) / "gitDetails.json"
        res = pgp.create_git_info_file(None, str(target))
        self.assertTrue(res)
        self.assertTrue(target.exists())
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn("git", data)

    def test_create_properties_file_auto_detected(self):
        target = Path(self.test_dir) / "git.properties"
        res = pgp.create_git_info_file(None, str(target))
        self.assertTrue(res)
        self.assertTrue(target.exists())
        content = target.read_text(encoding="utf-8")
        self.assertIn("git.branch=", content)

    def test_create_flat_json_file(self):
        target = Path(self.test_dir) / "flat.json"
        res = pgp.create_git_info_file(None, str(target), format="flat-json")
        self.assertTrue(res)
        data = json.loads(target.read_text(encoding="utf-8"))
        self.assertIn("git.branch", data)
        self.assertIn("git.commit.id.full", data)

    def test_create_file_async(self):
        async def _run():
            target = Path(self.test_dir) / "async.properties"
            res = await pgp.create_git_info_file_async(None, str(target), format="properties")
            self.assertTrue(res)
            self.assertTrue(target.exists())
            self.assertIn("git.branch=", target.read_text(encoding="utf-8"))

        asyncio.run(_run())


class TestCamelCaseAliases(unittest.TestCase):
    """Verify camelCase aliases match snake_case functions exactly."""

    def test_aliases(self):
        self.assertIs(pgp.currentBranch, pgp.current_branch)
        self.assertIs(pgp.commitIdAbbrev, pgp.commit_id_abbrev)
        self.assertIs(pgp.commitIdFull, pgp.commit_id_full)
        self.assertIs(pgp.lastCommitMsg, pgp.last_commit_msg)
        self.assertIs(pgp.commitUserInfo, pgp.commit_user_info)
        self.assertIs(pgp.dateOfLastCommit, pgp.date_of_last_commit)
        self.assertIs(pgp.isDirty, pgp.is_dirty)
        self.assertIs(pgp.remoteUrl, pgp.remote_url)
        self.assertIs(pgp.commitIdDescAndTags, pgp.commit_id_desc_and_tags)
        self.assertIs(pgp.closestTagCommitCount, pgp.closest_tag_commit_count)
        self.assertIs(pgp.countOfAllCommits, pgp.count_of_all_commits)
        self.assertIs(pgp.buildHost, pgp.build_host)
        self.assertIs(pgp.buildVersion, pgp.build_version)
        self.assertIs(pgp.getGitProp, pgp.get_git_prop)
        self.assertIs(pgp.gitInfoAsJson, pgp.git_info_as_json)
        self.assertIs(pgp.gitInfoAsProperties, pgp.git_info_as_properties)
        self.assertIs(pgp.createGitInfoFile, pgp.create_git_info_file)

        # Async aliases
        self.assertIs(pgp.currentBranchAsync, pgp.current_branch_async)
        self.assertIs(pgp.commitIdAbbrevAsync, pgp.commit_id_abbrev_async)
        self.assertIs(pgp.commitIdFullAsync, pgp.commit_id_full_async)
        self.assertIs(pgp.getGitPropAsync, pgp.get_git_prop_async)
        self.assertIs(pgp.gitInfoAsJsonAsync, pgp.git_info_as_json_async)
        self.assertIs(pgp.gitInfoAsPropertiesAsync, pgp.git_info_as_properties_async)
        self.assertIs(pgp.createGitInfoFileAsync, pgp.create_git_info_file_async)


class TestCli(unittest.TestCase):
    """Test CLI flags, output formats, and error handling."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="git_props_cli_")
        self.silent_log = lambda _: None
        self.silent_err = lambda _: None

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run(self, args):
        return run_cli(args, log=self.silent_log, err_log=self.silent_err)

    def test_cli_help(self):
        res = self._run(["--help"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Usage:", res.output)
        self.assertIn("--output", res.output)

    def test_cli_version(self):
        res = self._run(["--version"])
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output, "1.0.0")

    def test_cli_print_properties(self):
        res = self._run(["-p", "-f", "properties"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("git.branch=", res.output)
        self.assertIn("git.build.version=1.0.0", res.output)

    def test_cli_print_flat_json(self):
        res = self._run(["-p", "-f", "flat-json"])
        self.assertEqual(res.exit_code, 0)
        parsed = json.loads(res.output)
        self.assertIn("git.branch", parsed)

    def test_cli_print_nested_json(self):
        res = self._run(["-p", "-f", "json"])
        self.assertEqual(res.exit_code, 0)
        parsed = json.loads(res.output)
        self.assertIn("git", parsed)
        self.assertIn("branch", parsed["git"])

    def test_cli_file_output(self):
        out_file = str(Path(self.test_dir) / "custom.properties")
        res = self._run(["-o", out_file, "-f", "properties"])
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(Path(out_file).exists())
        self.assertIn("git.branch=", Path(out_file).read_text(encoding="utf-8"))

    def test_cli_invalid_format(self):
        res = self._run(["-f", "invalid_format"])
        self.assertEqual(res.exit_code, 1)
        self.assertIn("Unknown format", res.error)

    def test_cli_invalid_directory(self):
        res = self._run(["-d", "/nonexistent_dir_999999"])
        self.assertEqual(res.exit_code, 1)
        self.assertIn("Directory does not exist", res.error)

    def test_cli_missing_flag_value(self):
        res = self._run(["-o"])
        self.assertEqual(res.exit_code, 1)
        self.assertIn("requires a value", res.error)

    def test_cli_unknown_option(self):
        res = self._run(["--invalid-option"])
        self.assertEqual(res.exit_code, 1)
        self.assertIn("Unknown option", res.error)

    def test_module_invocation(self):
        import subprocess
        res0 = subprocess.run([sys.executable, "-m", "py_git_properties", "--version"], stdout=subprocess.PIPE, text=True)
        self.assertEqual(res0.returncode, 0)
        self.assertEqual(res0.stdout.strip(), "1.0.0")


class TestEdgeCasesAndFallbacks(unittest.TestCase):
    """Test edge cases: worktree spaces, property escaping, and CI fallbacks."""

    def test_properties_escaping(self):
        self.assertEqual(_format_property_value(None), "")
        self.assertEqual(_format_property_value("hello world"), "hello world")
        self.assertEqual(_format_property_value("line1\nline2"), "line1\\nline2")
        self.assertEqual(_format_property_value("line1\r\nline2"), "line1\\r\\nline2")
        self.assertEqual(_format_property_value("path\\to\\file"), "path\\\\to\\\\file")

    def test_cast_object_to_nested(self):
        flat = {
            "git.branch": "main",
            "git.commit.id.full": "abcdef123456",
            "git.dirty": True,
            "custom.deep.val": 99,
        }
        nested = _cast_object_to_nested_object(flat)
        self.assertEqual(nested["git"]["branch"], "main")
        self.assertEqual(nested["git"]["commit"]["id"]["full"], "abcdef123456")
        self.assertEqual(nested["git"]["dirty"], True)
        self.assertEqual(nested["custom"]["deep"]["val"], 99)

    def test_worktree_with_spaces_in_path(self):
        temp_dir = tempfile.mkdtemp(prefix="git test space_")
        try:
            repo_dir = Path(temp_dir) / "fake repo with space"
            repo_dir.mkdir(parents=True)
            fake_git = repo_dir / "target_git"
            fake_git.mkdir()
            (fake_git / "HEAD").write_text("ref: refs/heads/feature/space-branch\n", encoding="utf-8")

            worktree_dir = Path(temp_dir) / "worktree with spaces"
            worktree_dir.mkdir(parents=True)
            dot_git_file = worktree_dir / ".git"
            dot_git_file.write_text(f"gitdir: {fake_git}\n", encoding="utf-8")

            resolved = _get_git_dir(str(worktree_dir))
            self.assertEqual(resolved, fake_git.resolve())

            branch = pgp.current_branch(str(worktree_dir))
            self.assertEqual(branch, "feature/space-branch")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ci_fallbacks_isolated(self):
        clean_env = {
            "GIT_BRANCH": "",
            "GITHUB_HEAD_REF": "",
            "GITHUB_REF_NAME": "",
            "CI_COMMIT_REF_NAME": "",
            "VERCEL_GIT_COMMIT_REF": "",
            "BITBUCKET_BRANCH": "",
            "HEAD": "",
            "GIT_COMMIT": "",
            "GITHUB_SHA": "",
            "CI_COMMIT_SHA": "",
            "GIT_URL": "",
            "GITHUB_REPOSITORY": "",
            "CI_COMMIT_MESSAGE": "",
            "GIT_AUTHOR_NAME": "",
            "GITHUB_ACTOR": "",
        }
        with patch.dict(os.environ, clean_env, clear=False):
            # Test branch fallback
            with patch.dict(os.environ, {"GITHUB_HEAD_REF": "ci-pr-branch"}):
                self.assertEqual(_EnvFallback.branch(), "ci-pr-branch")

            # Test commit SHA fallback
            with patch.dict(os.environ, {"GITHUB_SHA": "1234567890abcdef1234567890abcdef12345678"}):
                self.assertEqual(_EnvFallback.commit_id(), "1234567890abcdef1234567890abcdef12345678")

            # Test remote url fallback
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": "parveen-soni/py-git-properties"}):
                self.assertEqual(
                    _EnvFallback.remote_url(),
                    "https://github.com/parveen-soni/py-git-properties",
                )

            # Test commit message fallback
            with patch.dict(os.environ, {"CI_COMMIT_MESSAGE": "Initial CI commit\nMore details"}):
                self.assertEqual(_EnvFallback.commit_message(short=True), "Initial CI commit")
                self.assertEqual(_EnvFallback.commit_message(short=False), "Initial CI commit\nMore details")

            # Test commit author fallback
            with patch.dict(os.environ, {"GITHUB_ACTOR": "parveen-soni"}):
                self.assertEqual(_EnvFallback.commit_user(email=False), "parveen-soni")


class TestFrameworkExtensions(unittest.TestCase):
    """Test optional framework integrations in py_git_properties.ext."""

    def test_fastapi_extension_import_error(self):
        from py_git_properties.ext.fastapi import get_git_info_router
        with patch.dict(sys.modules, {"fastapi": None}):
            with self.assertRaises(ImportError) as ctx:
                get_git_info_router()
            self.assertIn("FastAPI is required", str(ctx.exception))

    def test_flask_extension_import_error(self):
        from py_git_properties.ext.flask import get_git_info_blueprint
        with patch.dict(sys.modules, {"flask": None}):
            with self.assertRaises(ImportError) as ctx:
                get_git_info_blueprint()
            self.assertIn("Flask is required", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
