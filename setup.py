#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="py-git-properties",
    version="2.1.0",
    packages=find_packages(include=["py_git_properties*"]),
    entry_points={
        "console_scripts": [
            "py-git-properties = py_git_properties.cli:main",
        ],
    },
)
