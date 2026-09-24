"""git_info.py - Backward-compatible wrapper for py-git-properties.

Allows importing git properties functions or running directly:
    python git_info.py [options]
"""

from py_git_properties import *
from py_git_properties import __version__
from py_git_properties.cli import main

if __name__ == "__main__":
    main()
