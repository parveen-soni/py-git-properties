"""Core implementation of py-git-properties in pure Python (zero external dependencies).

Extracts repository git details, commit metadata, build info, and exports in
JSON, flat-JSON, or Java .properties format (Spring Boot Actuator compatible).
"""

import asyncio
import functools
import json
import os
import platform
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .constants import (
    KEY_GIT_BRANCH,
    KEY_GIT_BUILD_HOST,
    KEY_GIT_BUILD_USER_EMAIL,
    KEY_GIT_BUILD_USER_NAME,
    KEY_GIT_BUILD_VERSION,
    KEY_GIT_CLOSEST_TAG_COMMIT_COUNT,
    KEY_GIT_CLOSEST_TAG_NAME,
    KEY_GIT_COMMIT_FULL_MESSAGE,
    KEY_GIT_COMMIT_ID,
    KEY_GIT_COMMIT_ID_ABBREVIATED,
    KEY_GIT_COMMIT_ID_DESCRIBE,
    KEY_GIT_COMMIT_SHORT_MESSAGE,
    KEY_GIT_COMMIT_TIME,
    KEY_GIT_COMMIT_USER_EMAIL,
    KEY_GIT_COMMIT_USER_NAME,
    KEY_GIT_DIRTY,
    KEY_GIT_REMOTE_ORIGIN_URL,
    KEY_GIT_TAGS,
    KEY_GIT_TOTAL_COMMIT_COUNT,
)

REPO_NAME = "PY-GIT-PROPERTIES"
DETACHED_AT_HEAD_PREFIX = "Detached At Head: "
REF_BRANCH_REGEX = re.compile(r"^ref: refs/heads/(.*)\n?")
DEFAULT_FILE_NAME = "gitDetails.json"

try:
    to_thread = asyncio.to_thread
except AttributeError:
    async def to_thread(func, /, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


def _exe_cmd(cmd: str, args: List[str], cwd: Optional[str] = None) -> str:
    """Execute a system command and return stdout trimmed, or an error string."""
    try:
        working_dir = cwd or os.getcwd()
        result = subprocess.run(
            [cmd] + args,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            return f"{REPO_NAME} has failed to execute command: {err}"
        return (result.stdout or "").strip()
    except Exception as err:
        return f"{REPO_NAME} has failed to execute command: {err}"


async def _exe_cmd_async(cmd: str, args: List[str], cwd: Optional[str] = None) -> str:
    """Execute a system command asynchronously in a worker thread."""
    return await to_thread(_exe_cmd, cmd, args, cwd)


def _get_git_dir(dir_path: Optional[Union[str, Path]] = None) -> Path:
    """Find the .git directory starting from dir_path, walking up directory hierarchy.

    Supports standard repositories, git submodules, and git worktrees (including
    paths containing spaces).
    """
    if dir_path is None:
        curr = Path.cwd().resolve()
    else:
        curr = Path(dir_path).resolve()

    start = curr
    while True:
        candidate = curr / ".git"
        if candidate.exists():
            if candidate.is_dir():
                return candidate.resolve()
            # candidate is a file (git submodule or git worktree)
            try:
                content = candidate.read_text(encoding="utf-8").strip()
                match = re.search(r"^gitdir:\s*(.+)$", content, re.MULTILINE)
                parent_repo_path = match.group(1).strip() if match else content.replace("gitdir:", "").strip()
                target_path = Path(parent_repo_path)
                if not target_path.is_absolute():
                    target_path = curr / target_path
                target_path = target_path.resolve()
                if target_path.exists():
                    return target_path
                raise RuntimeError(f"{REPO_NAME} could not find repository from path {parent_repo_path}")
            except Exception as e:
                raise RuntimeError(f"{REPO_NAME} could not read gitdir file: {e}") from e

        parent = curr.parent
        if parent == curr:
            # Reached root of file system
            raise RuntimeError(f"Current directory {start} is not a git repository")
        curr = parent


class _EnvFallback:
    """Environment variable fallbacks for CI/CD environments (GitHub Actions, GitLab, Vercel)."""

    @staticmethod
    def branch() -> Optional[str]:
        return (
            os.getenv("GIT_BRANCH")
            or os.getenv("GITHUB_HEAD_REF")
            or os.getenv("GITHUB_REF_NAME")
            or os.getenv("CI_COMMIT_REF_NAME")
            or os.getenv("VERCEL_GIT_COMMIT_REF")
            or os.getenv("BITBUCKET_BRANCH")
            or os.getenv("HEAD")
        )

    @staticmethod
    def commit_id() -> Optional[str]:
        return (
            os.getenv("GIT_COMMIT")
            or os.getenv("GITHUB_SHA")
            or os.getenv("CI_COMMIT_SHA")
            or os.getenv("VERCEL_GIT_COMMIT_SHA")
            or os.getenv("BITBUCKET_COMMIT")
        )

    @staticmethod
    def remote_url() -> Optional[str]:
        if os.getenv("GIT_URL"):
            return os.getenv("GIT_URL")
        if os.getenv("GITHUB_REPOSITORY"):
            return f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}"
        if os.getenv("CI_REPOSITORY_URL"):
            return os.getenv("CI_REPOSITORY_URL")
        return None

    @staticmethod
    def commit_message(short: bool = False) -> Optional[str]:
        msg = os.getenv("CI_COMMIT_MESSAGE") or os.getenv("VERCEL_GIT_COMMIT_MESSAGE")
        if not msg:
            return None
        return msg.split("\n")[0] if short else msg

    @staticmethod
    def commit_user(email: bool = False) -> Optional[str]:
        if email:
            return os.getenv("GIT_AUTHOR_EMAIL") or os.getenv("CI_COMMIT_AUTHOR_EMAIL")
        return os.getenv("GIT_AUTHOR_NAME") or os.getenv("GITHUB_ACTOR") or os.getenv("CI_COMMIT_AUTHOR")


def _normalize_custom_prop_map(custom_git_prop: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not custom_git_prop:
        return None
    return dict(custom_git_prop)


def _deep_merge(target: Dict[str, Any], *sources: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge sources into target dictionary."""
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, val in source.items():
            if key in ("__proto__", "constructor", "prototype"):
                continue
            if isinstance(val, dict) and isinstance(target.get(key), dict):
                _deep_merge(target[key], val)
            else:
                target[key] = val
    return target


def _prepare_object(key: str, value: Any) -> Dict[str, Any]:
    """Prepare a nested dictionary from a dot-separated key."""
    json_obj: Dict[str, Any] = {}
    first_dot_index = key.find(".")
    if first_dot_index > -1:
        first_key = key[:first_dot_index]
        nested_key = key[first_dot_index + 1 :]
        json_obj[first_key] = _prepare_object(nested_key, value)
    else:
        json_obj[key] = value
    return json_obj


def _cast_object_to_nested_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a flat dot-separated dictionary into a deeply nested structure."""
    result: Dict[str, Any] = {}
    for key, value in obj.items():
        nested = _prepare_object(key, value)
        result = _deep_merge({}, result, nested)
    return result


def _format_property_value(val: Any) -> str:
    """Format property value escaping newlines and backslashes according to Java .properties specification."""
    if val is None:
        return ""
    return str(val).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")


# -------------------------------------------------------------------------
# Synchronous Core APIs
# -------------------------------------------------------------------------

def current_branch(dir: Optional[str] = None) -> str:
    """Get the name of the current git branch, or fallback to CI environment/detached HEAD."""
    try:
        git_dir = _get_git_dir(dir)
        head_path = git_dir / "HEAD"
        head_content = head_path.read_text(encoding="utf-8")
        match = REF_BRANCH_REGEX.match(head_content)
        if match:
            return match.group(1).strip()
        env_branch = _EnvFallback.branch()
        if env_branch:
            return env_branch
        return DETACHED_AT_HEAD_PREFIX + head_content.strip()
    except Exception as err:
        env_branch = _EnvFallback.branch()
        if env_branch:
            return env_branch
        raise err


def build_host() -> str:
    """Get the machine hostname where the script is executed."""
    return socket.gethostname()


def build_version(dir: Optional[str] = None) -> str:
    """Get project version by inspecting pyproject.toml, setup.cfg, setup.py, or package.json."""
    # 1. Search git repo root
    try:
        git_dir = _get_git_dir(dir)
        repo_root = git_dir.parent
        # Try pyproject.toml
        pyproject = repo_root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
            if match:
                return match.group(1)
        # Try setup.cfg
        setup_cfg = repo_root / "setup.cfg"
        if setup_cfg.exists():
            text = setup_cfg.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*([^\s\n]+)', text)
            if match:
                return match.group(1)
        # Try package.json
        pkg_json = repo_root / "package.json"
        if pkg_json.exists():
            parsed = json.loads(pkg_json.read_text(encoding="utf-8"))
            if parsed.get("version"):
                return str(parsed["version"])
    except Exception:
        pass

    # 2. Search current working directory
    cwd = Path.cwd()
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        try:
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8"))
            if match:
                return match.group(1)
        except Exception:
            pass

    pkg_json = cwd / "package.json"
    if pkg_json.exists():
        try:
            parsed = json.loads(pkg_json.read_text(encoding="utf-8"))
            if parsed.get("version"):
                return str(parsed["version"])
        except Exception:
            pass

    # 3. Fallback to package __version__ if installed
    try:
        from . import __version__
        return __version__
    except Exception:
        return "1.0.0"


def _build_user_name() -> str:
    return (
        f"{REPO_NAME} could not determine this property, please pass this info via custom "
        f"property map with key {KEY_GIT_BUILD_USER_NAME}"
    )


def _build_user_email() -> str:
    return (
        f"{REPO_NAME} could not determine this property, please pass this info via custom "
        f"property map with key {KEY_GIT_BUILD_USER_EMAIL}"
    )


def commit_id_abbrev(dir: Optional[str] = None) -> str:
    """Get the 7-character abbreviated commit hash of HEAD."""
    res = _exe_cmd("git", ["rev-parse", "--short", "HEAD"], dir)
    if res.startswith(REPO_NAME):
        env_id = _EnvFallback.commit_id()
        if env_id:
            return env_id[:7]
        return ""
    return res


def commit_id_full(dir: Optional[str] = None) -> str:
    """Get the full 40-character commit SHA of HEAD."""
    res = _exe_cmd("git", ["rev-parse", "HEAD"], dir)
    if res.startswith(REPO_NAME):
        env_id = _EnvFallback.commit_id()
        if env_id:
            return env_id
        return ""
    return res


def last_commit_msg(short: bool = False, dir: Optional[str] = None) -> str:
    """Get the commit message of the last commit. If short=True, return only the subject line."""
    pretty_arg = "--pretty=%s" if short else "--pretty=%B"
    res = _exe_cmd("git", ["log", "-1", pretty_arg], dir)
    if res.startswith(REPO_NAME):
        env_msg = _EnvFallback.commit_message(short)
        if env_msg:
            return env_msg
        return ""
    return res


def commit_user_info(email: bool = False, dir: Optional[str] = None) -> str:
    """Get author name (or email if email=True) of the last commit."""
    pretty_arg = "--pretty=format:%ae" if email else "--pretty=format:%an"
    res = _exe_cmd("git", ["log", "-1", pretty_arg], dir)
    if res.startswith(REPO_NAME):
        env_user = _EnvFallback.commit_user(email)
        if env_user:
            return env_user
        return ""
    return res


def date_of_last_commit(dir: Optional[str] = None) -> str:
    """Get the date string of the last commit."""
    res = _exe_cmd("git", ["log", "--no-color", "-n", "1", "--pretty=format:%ad"], dir)
    if res.startswith(REPO_NAME):
        return datetime.now().ctime()
    return res


def is_dirty(dir: Optional[str] = None) -> bool:
    """Check if the git repository has any uncommitted changes."""
    res = _exe_cmd("git", ["diff-index", "HEAD", "--"], dir)
    if res.startswith(REPO_NAME):
        return False
    return len(res) > 0


def remote_url(dir: Optional[str] = None) -> str:
    """Get the git remote origin URL."""
    res = _exe_cmd("git", ["ls-remote", "--get-url"], dir)
    if res.startswith(REPO_NAME):
        env_url = _EnvFallback.remote_url()
        return env_url or ""
    return res


def commit_id_desc_and_tags(flag_dirty: bool = False, dir: Optional[str] = None) -> str:
    """Get the tag description of HEAD using git describe."""
    cmd_args = ["describe", "--tags"] if flag_dirty else ["describe", "--tag", "--abbrev=0"]
    cmd_result = _exe_cmd("git", cmd_args, dir)
    if cmd_result.startswith(REPO_NAME):
        return ""
    return f"{cmd_result}-dirty" if flag_dirty else cmd_result


def closest_tag_commit_count(dir: Optional[str] = None) -> str:
    """Get the number of commits from the closest tag."""
    tag_name = commit_id_desc_and_tags(False, dir)
    if tag_name.startswith(REPO_NAME) or not tag_name:
        return "0"
    count = _exe_cmd("git", ["rev-list", "--count", tag_name], dir)
    return "0" if count.startswith(REPO_NAME) else count


def count_of_all_commits(dir: Optional[str] = None) -> int:
    """Get total count of all commits in the repository."""
    result = _exe_cmd("git", ["rev-list", "--all", "--count"], dir)
    try:
        return int(result)
    except (ValueError, TypeError):
        return 0


# -------------------------------------------------------------------------
# Asynchronous Equivalents
# -------------------------------------------------------------------------

async def current_branch_async(dir: Optional[str] = None) -> str:
    return await to_thread(current_branch, dir)


async def commit_id_abbrev_async(dir: Optional[str] = None) -> str:
    return await to_thread(commit_id_abbrev, dir)


async def commit_id_full_async(dir: Optional[str] = None) -> str:
    return await to_thread(commit_id_full, dir)


async def last_commit_msg_async(short: bool = False, dir: Optional[str] = None) -> str:
    return await to_thread(last_commit_msg, short, dir)


async def commit_user_info_async(email: bool = False, dir: Optional[str] = None) -> str:
    return await to_thread(commit_user_info, email, dir)


async def date_of_last_commit_async(dir: Optional[str] = None) -> str:
    return await to_thread(date_of_last_commit, dir)


async def is_dirty_async(dir: Optional[str] = None) -> bool:
    return await to_thread(is_dirty, dir)


async def remote_url_async(dir: Optional[str] = None) -> str:
    return await to_thread(remote_url, dir)


async def commit_id_desc_and_tags_async(flag_dirty: bool = False, dir: Optional[str] = None) -> str:
    return await to_thread(commit_id_desc_and_tags, flag_dirty, dir)


async def closest_tag_commit_count_async(dir: Optional[str] = None) -> str:
    return await to_thread(closest_tag_commit_count, dir)


async def count_of_all_commits_async(dir: Optional[str] = None) -> int:
    return await to_thread(count_of_all_commits, dir)


# -------------------------------------------------------------------------
# Aggregation & Serialization Functions
# -------------------------------------------------------------------------

def get_git_prop(
    custom_git_prop: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve all git properties as a flat dictionary of key=value pairs."""
    normalized = _normalize_custom_prop_map(custom_git_prop)
    git_prop: Dict[str, Any] = {
        KEY_GIT_BRANCH: current_branch(dir),
        KEY_GIT_BUILD_HOST: build_host(),
        KEY_GIT_BUILD_VERSION: build_version(dir),
        KEY_GIT_BUILD_USER_NAME: _build_user_name(),
        KEY_GIT_BUILD_USER_EMAIL: _build_user_email(),
        KEY_GIT_COMMIT_ID_ABBREVIATED: commit_id_abbrev(dir),
        KEY_GIT_COMMIT_ID_DESCRIBE: commit_id_desc_and_tags(True, dir),
        KEY_GIT_COMMIT_ID: commit_id_full(dir),
        KEY_GIT_COMMIT_SHORT_MESSAGE: last_commit_msg(True, dir),
        KEY_GIT_COMMIT_FULL_MESSAGE: last_commit_msg(False, dir),
        KEY_GIT_COMMIT_USER_NAME: commit_user_info(False, dir),
        KEY_GIT_COMMIT_USER_EMAIL: commit_user_info(True, dir),
        KEY_GIT_COMMIT_TIME: date_of_last_commit(dir),
        KEY_GIT_DIRTY: is_dirty(dir),
        KEY_GIT_REMOTE_ORIGIN_URL: remote_url(dir),
        KEY_GIT_TAGS: commit_id_desc_and_tags(False, dir),
        KEY_GIT_CLOSEST_TAG_NAME: commit_id_desc_and_tags(False, dir),
        KEY_GIT_CLOSEST_TAG_COMMIT_COUNT: closest_tag_commit_count(dir),
        KEY_GIT_TOTAL_COMMIT_COUNT: count_of_all_commits(dir),
    }
    if normalized:
        git_prop.update(normalized)
    return git_prop


async def get_git_prop_async(
    custom_git_prop: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve all git properties asynchronously as a flat dictionary."""
    normalized = _normalize_custom_prop_map(custom_git_prop)
    (
        branch,
        commit_abbrev,
        commit_desc,
        commit_full,
        short_msg,
        full_msg,
        user_name,
        user_email,
        commit_time,
        dirty,
        remote,
        tags,
        closest_tag_name,
        closest_count,
        total_count,
    ) = await asyncio.gather(
        current_branch_async(dir),
        commit_id_abbrev_async(dir),
        commit_id_desc_and_tags_async(True, dir),
        commit_id_full_async(dir),
        last_commit_msg_async(True, dir),
        last_commit_msg_async(False, dir),
        commit_user_info_async(False, dir),
        commit_user_info_async(True, dir),
        date_of_last_commit_async(dir),
        is_dirty_async(dir),
        remote_url_async(dir),
        commit_id_desc_and_tags_async(False, dir),
        commit_id_desc_and_tags_async(False, dir),
        closest_tag_commit_count_async(dir),
        count_of_all_commits_async(dir),
    )

    git_prop: Dict[str, Any] = {
        KEY_GIT_BRANCH: branch,
        KEY_GIT_BUILD_HOST: build_host(),
        KEY_GIT_BUILD_VERSION: build_version(dir),
        KEY_GIT_BUILD_USER_NAME: _build_user_name(),
        KEY_GIT_BUILD_USER_EMAIL: _build_user_email(),
        KEY_GIT_COMMIT_ID_ABBREVIATED: commit_abbrev,
        KEY_GIT_COMMIT_ID_DESCRIBE: commit_desc,
        KEY_GIT_COMMIT_ID: commit_full,
        KEY_GIT_COMMIT_SHORT_MESSAGE: short_msg,
        KEY_GIT_COMMIT_FULL_MESSAGE: full_msg,
        KEY_GIT_COMMIT_USER_NAME: user_name,
        KEY_GIT_COMMIT_USER_EMAIL: user_email,
        KEY_GIT_COMMIT_TIME: commit_time,
        KEY_GIT_DIRTY: dirty,
        KEY_GIT_REMOTE_ORIGIN_URL: remote,
        KEY_GIT_TAGS: tags,
        KEY_GIT_CLOSEST_TAG_NAME: closest_tag_name,
        KEY_GIT_CLOSEST_TAG_COMMIT_COUNT: closest_count,
        KEY_GIT_TOTAL_COMMIT_COUNT: total_count,
    }
    if normalized:
        git_prop.update(normalized)
    return git_prop


def git_info_as_properties(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
) -> str:
    """Format git properties as standard Java key=value properties string."""
    final_git_prop = get_git_prop(custom_git_prop_map, dir)
    lines: List[str] = []
    for key in sorted(final_git_prop.keys()):
        val = final_git_prop[key]
        lines.append(f"{key}={_format_property_value(val)}")
    return "\n".join(lines) + "\n"


async def git_info_as_properties_async(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
) -> str:
    """Format git properties asynchronously as standard Java properties string."""
    final_git_prop = await get_git_prop_async(custom_git_prop_map, dir)
    lines: List[str] = []
    for key in sorted(final_git_prop.keys()):
        val = final_git_prop[key]
        lines.append(f"{key}={_format_property_value(val)}")
    return "\n".join(lines) + "\n"


def git_info_as_json(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    require_object: bool = False,
    dir: Optional[str] = None,
) -> Union[str, Dict[str, Any]]:
    """Retrieve git info formatted into nested JSON.

    If require_object=True, returns a dict; otherwise returns a formatted JSON string.
    """
    final_git_prop = get_git_prop(custom_git_prop_map, dir)
    git_info_obj = _cast_object_to_nested_object(final_git_prop)
    return git_info_obj if require_object else json.dumps(git_info_obj, indent=2)


async def git_info_as_json_async(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    require_object: bool = False,
    dir: Optional[str] = None,
) -> Union[str, Dict[str, Any]]:
    """Retrieve git info asynchronously formatted into nested JSON."""
    final_git_prop = await get_git_prop_async(custom_git_prop_map, dir)
    git_info_obj = _cast_object_to_nested_object(final_git_prop)
    return git_info_obj if require_object else json.dumps(git_info_obj, indent=2)


def create_git_info_file(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    file_name: Optional[str] = None,
    format: Optional[str] = None,
    dir: Optional[str] = None,
) -> bool:
    """Write git info to file. Auto-detects .properties format by extension or format argument."""
    target_file = file_name or DEFAULT_FILE_NAME
    is_props = format == "properties" or (not format and target_file.endswith(".properties"))
    is_flat_json = format == "flat-json"

    if is_props:
        content = git_info_as_properties(custom_git_prop_map, dir)
    elif is_flat_json:
        normalized = _normalize_custom_prop_map(custom_git_prop_map)
        content = json.dumps(get_git_prop(normalized, dir), indent=2)
    else:
        content = str(git_info_as_json(custom_git_prop_map, False, dir))

    target_path = Path(target_file)
    try:
        if target_path.exists():
            target_path.unlink()
        target_path.write_text(content, encoding="utf-8")
        return True
    except Exception as error:
        raise RuntimeError(f"{REPO_NAME} has failed to create {target_file} due to {error}") from error


async def create_git_info_file_async(
    custom_git_prop_map: Optional[Dict[str, Any]] = None,
    file_name: Optional[str] = None,
    format: Optional[str] = None,
    dir: Optional[str] = None,
) -> bool:
    """Write git info to file asynchronously."""
    target_file = file_name or DEFAULT_FILE_NAME
    is_props = format == "properties" or (not format and target_file.endswith(".properties"))
    is_flat_json = format == "flat-json"

    if is_props:
        content = await git_info_as_properties_async(custom_git_prop_map, dir)
    elif is_flat_json:
        normalized = _normalize_custom_prop_map(custom_git_prop_map)
        props = await get_git_prop_async(normalized, dir)
        content = json.dumps(props, indent=2)
    else:
        content = str(await git_info_as_json_async(custom_git_prop_map, False, dir))

    def _write() -> bool:
        target_path = Path(target_file)
        if target_path.exists():
            target_path.unlink()
        target_path.write_text(content, encoding="utf-8")
        return True

    try:
        return await to_thread(_write)
    except Exception as error:
        raise RuntimeError(f"{REPO_NAME} has failed to create {target_file} due to {error}") from error
