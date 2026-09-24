"""Command Line Interface for py-git-properties.

Can be run via:
  py-git-properties [options]
  python -m py_git_properties [options]
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .core import (
    build_version,
    create_git_info_file,
    get_git_prop,
    git_info_as_json,
    git_info_as_properties,
)


@dataclass
class CliResult:
    exit_code: int
    output: Optional[str] = None
    error: Optional[str] = None


def get_help_text() -> str:
    return """
py-git-properties CLI

Usage:
  py-git-properties [options]

Options:
  -o, --output <file>    Output file path (default: gitDetails.json or git.properties)
  -f, --format <format>  Output format: json, flat-json, properties (default: auto-detected by extension or json)
  -d, --dir <directory>  Target git repository directory (default: current directory)
  -p, --print            Print output to stdout instead of writing to a file
  -v, --version          Print version
  -h, --help             Show help
"""


def run_cli(
    args: Optional[List[str]] = None,
    log: Optional[Callable[[str], None]] = None,
    err_log: Optional[Callable[[str], None]] = None,
) -> CliResult:
    """Execute the CLI with arguments and optional log captures.

    Does not invoke sys.exit(), allowing programmatic usage and automated testing.
    """
    if args is None:
        args = sys.argv[1:]

    _log = log or print
    _err_log = err_log or (lambda msg: print(msg, file=sys.stderr))

    output: Optional[str] = None
    fmt: Optional[str] = None
    target_dir: Optional[str] = None
    print_stdout = False

    def get_opt_value(index: int, flag: str) -> Tuple[Optional[str], Optional[str]]:
        if index + 1 >= len(args) or args[index + 1].startswith("-"):
            return None, f"Error: Option '{flag}' requires a value."
        return args[index + 1], None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-h", "--help"):
            help_text = get_help_text()
            _log(help_text)
            return CliResult(0, output=help_text)
        elif arg in ("-v", "--version"):
            ver = build_version(target_dir)
            _log(ver)
            return CliResult(0, output=ver)
        elif arg in ("-o", "--output"):
            val, err = get_opt_value(i, arg)
            if err:
                _err_log(err)
                return CliResult(1, error=err)
            output = val
            i += 1
        elif arg in ("-f", "--format"):
            val, err = get_opt_value(i, arg)
            if err:
                _err_log(err)
                return CliResult(1, error=err)
            if val in ("json", "flat-json", "properties"):
                fmt = val
            else:
                msg = f"Unknown format: {val}. Supported formats: json, flat-json, properties"
                _err_log(msg)
                return CliResult(1, error=msg)
            i += 1
        elif arg in ("-d", "--dir"):
            val, err = get_opt_value(i, arg)
            if err:
                _err_log(err)
                return CliResult(1, error=err)
            target_dir = val
            i += 1
        elif arg in ("-p", "--print"):
            print_stdout = True
        elif arg.startswith("-"):
            msg = f"Unknown option: {arg}. See --help for available options."
            _err_log(msg)
            return CliResult(1, error=msg)
        i += 1

    if target_dir:
        resolved = Path(target_dir).resolve()
        if not resolved.exists() or not resolved.is_dir():
            msg = f"Error: Directory does not exist: {target_dir}"
            _err_log(msg)
            return CliResult(1, error=msg)

    if print_stdout:
        if fmt == "properties":
            content = git_info_as_properties(None, target_dir)
        elif fmt == "flat-json":
            import json
            content = json.dumps(get_git_prop(None, target_dir), indent=2)
        else:
            content = str(git_info_as_json(None, False, target_dir))
        _log(content)
        return CliResult(0, output=content)

    output_file = output or ("git.properties" if fmt == "properties" else "gitDetails.json")
    if target_dir and not Path(output_file).is_absolute():
        target_path = str(Path(target_dir).resolve() / output_file)
    else:
        target_path = output_file

    try:
        create_git_info_file(None, target_path, fmt, target_dir)
        msg = f"Generated git properties file at: {target_path}"
        _log(msg)
        return CliResult(0, output=msg)
    except Exception as err:
        err_msg = str(err)
        _err_log(err_msg)
        return CliResult(1, error=err_msg)


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for command line scripts."""
    result = run_cli(argv)
    if result.exit_code != 0:
        sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
