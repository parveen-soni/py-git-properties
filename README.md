# py-git-properties

[![CI](https://github.com/parveen-soni/py-git-properties/actions/workflows/ci.yml/badge.svg)](https://github.com/parveen-soni/py-git-properties/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.1.0-green.svg)](https://github.com/parveen-soni/py-git-properties)

A lightweight, high-performance, **zero-dependency** Python library and CLI tool designed to extract comprehensive Git repository metadata, commit history, build versions, and repository state.

Generates outputs in **Spring Boot Actuator compatible Java `.properties`**, nested **JSON**, and **flat-JSON** formats. Ideal for deployment pipelines, health check endpoints, CI/CD telemetry, and DevOps auditing.

---

## Features

- **Zero External Dependencies**: Implemented entirely with Python standard library modules (`subprocess`, `pathlib`, `json`, `datetime`, `asyncio`, `socket`).
- **Spring Boot Actuator Compatibility**: Produces standard `git.properties` files compliant with Java `.properties` specifications (including multiline escaping).
- **Multiple Output Formats**: Supports `properties`, `json` (deeply nested), and `flat-json` (key=value dictionary).
- **Sync & Async APIs**: Full native support for both synchronous Python workflows and modern asynchronous event loops (`async`/`await`).
- **Pythonic & Parity Naming**: Provides idiomatic `snake_case` functions alongside `camelCase` aliases matching [`npm-git-properties`](https://github.com/parveen-soni/npm-git-properties).
- **CI/CD Resilience**: Built-in fallbacks for detached HEAD states across GitHub Actions, GitLab CI, Vercel, Bitbucket Pipelines, and Jenkins.
- **Submodule & Worktree Support**: Seamlessly traverses submodules and git worktrees, including paths containing spaces.
- **Production CLI**: Inspect git details in the terminal (`--print`) or write directly to output files (`--output`).

---

## Installation

Install using `pip`:

```bash
pip install py-git-properties
```

Or install in editable development mode from the repository:

```bash
git clone https://github.com/parveen-soni/py-git-properties.git
cd py-git-properties
pip install -e .
```

`py-git-properties`, `git-properties`, and `git-contribution-info` CLI commands are all registered.

---

## CLI Usage

### Command Line Interface

```bash
# Display help and options
py-git-properties --help

# Print Java .properties to stdout
py-git-properties -p -f properties

# Print nested JSON to stdout
py-git-properties -p -f json

# Print flat JSON to stdout
py-git-properties -p -f flat-json

# Generate git.properties file (auto-detects format from extension)
py-git-properties -o git.properties

# Generate gitDetails.json file
py-git-properties -o gitDetails.json -f json

# Target another repository directory
py-git-properties -d /path/to/another/repo -p -f properties
```

### Options

| Option | Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `--output` | `-o` | Output file path | `gitDetails.json` (or `git.properties` if format is properties) |
| `--format` | `-f` | Output format: `json`, `flat-json`, `properties` | Auto-detected from file extension, or `json` |
| `--dir` | `-d` | Target git repository directory | Current working directory |
| `--print` | `-p` | Print output to stdout instead of writing to a file | `False` |
| `--version` | `-v` | Print tool version | - |
| `--help` | `-h` | Show help and usage instructions | - |

You can also run the tool directly via Python:

```bash
python -m py_git_properties [options]
# or
python -m git_properties [options]
# or
python git_info.py [options]
```

---

## Python API Usage

### 1. Synchronous API

```python
import py_git_properties as gp
# Note: 'import git_properties as gp' is also supported as an alias

# 1. Retrieve all properties as a flat dictionary
props = gp.get_git_prop()
print(props["git.branch"])
print(props["git.commit.id.full"])
print(props["git.commit.message.short"])

# 2. Retrieve properties formatted as nested JSON
json_obj = gp.git_info_as_json(require_object=True)
print(json_obj["git"]["commit"]["user"]["name"])

# 3. Retrieve properties as a Spring Boot .properties string
properties_str = gp.git_info_as_properties()
print(properties_str)

# 4. Generate an output file
gp.create_git_info_file(file_name="git.properties", format="properties")
gp.create_git_info_file(file_name="gitDetails.json", format="json")
```

### 2. Asynchronous API (`asyncio`)

```python
import asyncio
import py_git_properties as gp

async def main():
    # Asynchronously fetch properties
    props = await gp.get_git_prop_async()
    print(props["git.commit.id.abbrev"])

    # Asynchronously generate properties string
    props_str = await gp.git_info_as_properties_async()

    # Asynchronously write to file
    await gp.create_git_info_file_async(file_name="git.properties", format="properties")

asyncio.run(main())
```

### 3. Granular Property Functions

```python
import py_git_properties as gp

branch = gp.current_branch()
commit_sha = gp.commit_id_full()
short_hash = gp.commit_id_abbrev()
author = gp.commit_user_info(email=False)
author_email = gp.commit_user_info(email=True)
commit_msg = gp.last_commit_msg(short=True)
commit_date = gp.date_of_last_commit()
is_uncommitted = gp.is_dirty()
origin_url = gp.remote_url()
total_commits = gp.count_of_all_commits()
version = gp.build_version()
host = gp.build_host()
```

*(All granular functions also have `_async` equivalents, e.g. `await gp.current_branch_async()`.)*

---

## Standard Generated Properties

| Property Key | Example Value | Description |
| :--- | :--- | :--- |
| `git.branch` | `main` | Current branch name or CI reference |
| `git.build.host` | `builder-worker-1` | Hostname where build was executed |
| `git.build.version` | `2.1.0` | Project version from `pyproject.toml`, `setup.cfg`, or `package.json` |
| `git.build.user.name` | Custom Map / CI | Name of the user running the build |
| `git.build.user.email`| Custom Map / CI | Email of the user running the build |
| `git.commit.id.abbrev`| `6450dbf` | 7-character commit SHA |
| `git.commit.id.full` | `6450dbfe9c84874331425e41f4607cb5e9678a4c` | Full 40-character commit SHA |
| `git.commit.id.describe` | `v2.0.0-1-g6450dbf` | Output of `git describe` |
| `git.commit.message.short` | `Fix issue with build` | Subject line of the latest commit |
| `git.commit.message.full` | `Fix issue with build\n\nDetailed explanation` | Full message of the latest commit |
| `git.commit.user.name` | `Parveen Soni` | Commit author name |
| `git.commit.user.email`| `parveensoni14891@gmail.com` | Commit author email |
| `git.commit.time` | `Fri Nov 29 13:43:03 2024 +0530` | Date string of the latest commit |
| `git.dirty` | `False` | `True` if uncommitted changes exist in working tree |
| `git.remote.origin.url`| `https://github.com/parveen-soni/py-git-properties.git` | Remote origin repository URL |
| `git.tags` | `v2.1.0` | Git tags associated with the current commit |
| `git.closest.tag.name` | `v2.0.0` | Name of the closest tag |
| `git.closest.tag.commit.count` | `1` | Commits since closest tag |
| `git.total.commit.count` | `45` | Total number of commits across the repository |

---

## Spring Boot Actuator Integration

To use the generated `git.properties` in a Spring Boot Actuator or Microservice application:

```bash
py-git-properties -o src/main/resources/git.properties -f properties
```

When deployed, Spring Boot Actuator exposes these details at `/actuator/info`:

```json
{
  "git": {
    "branch": "main",
    "commit": {
      "id": "6450dbf",
      "time": "2024-11-29T13:43:03Z"
    }
  }
```

---

## Web Framework Integrations

`py-git-properties` provides optional, zero-overhead plugins to expose git and build info in Python microservices.

### FastAPI / Starlette

Mount the ready-to-use router to expose an Actuator-style `/actuator/info` or `/info` endpoint:

```python
from fastapi import FastAPI
from py_git_properties.ext.fastapi import get_git_info_router

app = FastAPI(title="My Service")

# Mounts GET /actuator/info (cached in-memory for zero overhead)
app.include_router(get_git_info_router(prefix="/actuator"))
```

### Flask

Register the ready-to-use Blueprint:

```python
from flask import Flask
from py_git_properties.ext.flask import get_git_info_blueprint

app = Flask(__name__)

# Mounts GET /actuator/info
app.register_blueprint(get_git_info_blueprint(url_prefix="/actuator"))
```

---

## Pre-commit Hook Integration

Add `py-git-properties` to your `.pre-commit-config.yaml` to ensure git metadata is generated before committing or pushing:

```yaml
repos:
  - repo: https://github.com/parveen-soni/py-git-properties
    rev: v2.1.0
    hooks:
      - id: py-git-properties
        args: ["-o", "git.properties", "-f", "properties"]
```

---

## GitHub Actions Marketplace

Use `py-git-properties` as an official GitHub Action in your CI/CD workflows:

```yaml
- name: Generate Git Properties
  uses: parveen-soni/py-git-properties@v2
  with:
    format: 'properties'
    output: 'git.properties'
```

---

## Testing

Run the comprehensive unit test suite without needing any external test runner:

```bash
python3 -m unittest discover tests -v
```

---

## License

This project is open-source software licensed under the terms of the [GPL-3.0 License](https://github.com/parveen-soni/py-git-properties/blob/main/LICENSE).

## Author

**Parveen Soni**  
GitHub: [@parveen-soni](https://github.com/parveen-soni)
