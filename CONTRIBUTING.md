# Contributing to py-git-properties

Thank you for your interest in contributing to **py-git-properties**! We welcome community contributions, bug reports, feature requests, and documentation improvements.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Development Setup

### 1. Prerequisites
- Python 3.8 or higher.
- Git.
- **Zero external runtime dependencies**: The core engine must remain free of third-party runtime dependencies.

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/py-git-properties.git
cd py-git-properties
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Install in Editable Mode
```bash
pip install -e .
```

---

## Running Tests

We use Python's built-in `unittest` framework so no external test dependencies are required:

```bash
python3 -m unittest discover tests -v
```

Verify CLI invocations:
```bash
python3 -m py_git_properties --help
python3 -m py_git_properties --print --format properties
python3 -m py_git_properties --print --format json
python3 -m py_git_properties --print --format flat-json
```

---

## Pull Request Guidelines

1. **Keep dependencies at zero**: Any new core feature must use the Python standard library. Optional framework integrations should live in `py_git_properties/ext/` and use lazy imports.
2. **Add unit tests**: Ensure all new features or bug fixes are covered by tests in `tests/test_py_git_properties.py`.
3. **Multi-platform compatibility**: Code should work consistently on macOS, Linux, and Windows.
4. **Descriptive PR title & description**: Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.).
