# Abstract Plugin Infrastructure

Tools for building and evaluating Claude Code skills. Includes modular patterns, quality checks, and plugin validation.

## Quick Start

```bash
make check          # Install dependencies
make test           # Run quality checks
make install-hooks  # Set up git hooks
```

## Installation

Add to your `marketplace.json`:

```json
{
  "name": "abstract",
  "source": {
    "source": "url",
    "url": "https://github.com/athola/abstract.git"
  },
  "description": "Meta-skills infrastructure for Claude Code plugin ecosystem - modular design patterns and evaluation frameworks",
  "version": "1.0.0",
  "strict": true
}
```

Claude loads the plugin on startup.

## What's Included

*   **Skills**:
    *   `modular-skills`: Guides skill architecture and module splitting.
    *   `skills-eval`: Scores skill quality and suggests fixes.
    *   `hook-scope-guide`: Helps decide where hooks belong.
    *   `validate-plugin-structure`: Step-by-step plugin validation.
*   **Commands**:
    *   `/validate-plugin [path]`: Checks plugin structure against requirements.
*   **Agents**:
    *   `plugin-validator`: Validates plugins during development.
    *   `meta-architect`: Advises on plugin design.
    *   `skill-auditor`: Reviews skill quality.

Use this plugin to manage token usage (keep skills lean), find modularization opportunities, and catch `plugin.json` errors.

## Structure

*   `skills/`: Skill implementations.
*   `scripts/`: Validation and analysis tools.
*   `src/abstract/`: Shared Python package.
*   `docs/`: Technical documentation and ADRs.

## Documentation

For migration info, see `docs/migration-guide.md`. The Python package structure is documented in `docs/python-structure.md`. Each skill has its own `SKILL.md` with usage details. Run `make status` for a project overview.

Architecture decisions are recorded in `docs/adr/`. The plugin composition model is explained in `docs/multi-plugin-design.md`.

## Security

The CI pipeline runs Bandit, Safety, and Semgrep on each push. Pre-commit hooks catch issues locally.

```bash
make security   # Run security scans locally
```

## Development

```bash
make format        # Format code
make test          # Run all checks (includes security)
make security      # Security scans only
make clean         # Clean cache
make unit-tests    # Run tests
make test-coverage # Tests with coverage report
```

Tests in `test_skill_structure.py` check that skill descriptions contain action verbs, include "Use when..." triggers, and are detailed enough to be useful. This ensures skills are discoverable and understandable.
