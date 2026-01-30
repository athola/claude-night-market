# Makefile Dogfooding Command

Ensures every documented command has a corresponding Makefile target.

## Usage
```bash
python3 plugins/abstract/scripts/makefile_dogfooder.py --mode analyze
python3 plugins/abstract/scripts/makefile_dogfooder.py --plugin <name> --mode apply
```

## Demo Targets
- `demo-<command>`: Demonstrates the slash command
- `test-<command>`: Tests the command workflow

Example: `make demo-commit-msg` in sanctum plugin

## Makefile Generation

### Automatic Makefile Creation

The script can now generate Makefiles for plugins that don't have one, following the `attune:makefile-generation` skill pattern:

```bash
# Generate Makefiles for all plugins that are missing them
python3 plugins/abstract/scripts/makefile_dogfooder.py --generate-makefiles --mode analyze

# Generate for a specific plugin
python3 plugins/abstract/scripts/makefile_dogfooder.py --plugin new-plugin --generate-makefiles
```

### Language Detection

The script automatically detects the plugin's language:

- **Python**: Detects `pyproject.toml`
- **Rust**: Detects `Cargo.toml`
- **TypeScript**: Detects `package.json`
- **Default**: Falls back to Python for claude-night-market plugins

### Generated Makefile Features

#### Python Makefiles
- `help` - Show available targets
- `install` - Install dependencies with uv
- `lint` - Run ruff linting
- `format` - Format code with ruff
- `typecheck` - Run mypy type checking
- `test` - Run pytest
- `test-cov` - Run tests with coverage
- `check-all` - Run all quality checks
- `clean` - Remove cache files
- `build` - Build distribution package
- `status` - Show project overview

#### Rust Makefiles
- `help`, `fmt`, `lint`, `check`, `test`, `build`, `clean`

#### TypeScript Makefiles
- `help`, `install`, `lint`, `format`, `typecheck`, `test`, `build`, `dev`, `clean`

### Example Workflow

```bash
# 1. Check which plugins need Makefiles
python3 makefile_dogfooder.py --mode analyze

# 2. Generate missing Makefiles (dry-run first)
python3 makefile_dogfooder.py --generate-makefiles --dry-run

# 3. Generate for real
python3 makefile_dogfooder.py --generate-makefiles

# 4. Verify generated Makefiles
for dir in plugins/*/; do make -C "$dir" help; done
```
