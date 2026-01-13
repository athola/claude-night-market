# Sanctum Scripts

Utility scripts for sanctum plugin operations.

## update_versions.py

Bulk update version strings across all version files in the repository.

### Features

- **Recursive search**: Finds all pyproject.toml, Cargo.toml, and package.json files
- **Nested support**: Handles nested version files (e.g., `plugins/memory-palace/hooks/pyproject.toml`)
- **Smart exclusion**: Automatically excludes virtual environments and build directories
- **Safe operation**: Dry-run mode to preview changes before applying

### Usage

```bash
# Preview changes (recommended first step)
./plugins/sanctum/scripts/update_versions.py 1.2.5 --dry-run

# Apply changes
./plugins/sanctum/scripts/update_versions.py 1.2.5

# Specify custom root directory
./plugins/sanctum/scripts/update_versions.py 1.2.5 --root /path/to/repo

# Include cache directories (rarely needed, use with caution)
./plugins/sanctum/scripts/update_versions.py 1.2.5 --include-cache --dry-run
```

**Note**: By default, cache and temporary directories are **automatically excluded**. Only use `--include-cache` if you explicitly need to update version files in those locations.

### Example Output

```
Searching for version files in: /home/user/claude-night-market

Found 16 version file(s):
  - plugins/abstract/pyproject.toml
  - plugins/memory-palace/pyproject.toml
  - plugins/memory-palace/hooks/pyproject.toml
  - plugins/sanctum/pyproject.toml
  ...

Updating to version: 1.2.5
  ✓ Updated: plugins/abstract/pyproject.toml
  ✓ Updated: plugins/memory-palace/pyproject.toml
  ✓ Updated: plugins/memory-palace/hooks/pyproject.toml
  ...

Updated 16/16 file(s)
```

### Excluded Directories

The script automatically excludes the following directories **by default** (use `--include-cache` to override):

**Python:**
- `.venv`, `venv`, `.virtualenv`, `virtualenv` - Virtual environments
- `__pycache__` - Python bytecode cache
- `.pytest_cache`, `.mypy_cache`, `.ruff_cache` - Tool caches
- `.tox` - Tox environments
- `.eggs`, `*.egg-info` - Package metadata
- `.uv-cache` - uv package cache

**JavaScript/Node:**
- `node_modules` - Node.js dependencies
- `.npm`, `.yarn`, `.pnp` - Package manager caches
- `.cache` - Generic cache directory

**Rust:**
- `target` - Rust build artifacts
- `.cargo` - Cargo cache
- `.rustup` - Rustup toolchains

**Build/Version Control:**
- `dist`, `build`, `_build`, `out` - Build artifacts
- `.git`, `.hg`, `.svn` - Version control
- `.worktrees` - Git worktrees

**IDEs/Editors:**
- `.vscode`, `.idea`, `.vs` - IDE settings

**OS:**
- `.DS_Store`, `Thumbs.db` - OS metadata

These exclusions prevent the script from recursing into temporary, cache, and dependency directories which often contain thousands of files.

### Testing

Tests are located in `plugins/sanctum/tests/test_update_versions.py`:

```bash
# Run tests
python3 plugins/sanctum/tests/test_update_versions.py

# Or via pytest
pytest plugins/sanctum/tests/test_update_versions.py -v
```

## update_plugin_registrations.py

Audit and sync plugin.json files with disk contents.

See the script's `--help` output for detailed usage.
