# Abstract Plugin Infrastructure

Tools for building and evaluating Claude Code skills. Provides modular patterns, quality checks, and plugin validation.

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

**Skills** handle specific tasks: `modular-skills` guides skill architecture and splitting large skills into modules. `skills-eval` scores skill quality and suggests fixes. `hook-scope-guide` helps decide where hooks belong (plugin, project, or global). `validate-plugin-structure` walks through plugin validation step by step.

**Commands**: `/validate-plugin [path]` checks a plugin's structure against Claude Code requirements.

**Agents**: `plugin-validator` validates plugins during development. `meta-architect` advises on plugin design. `skill-auditor` reviews skill quality.

The plugin helps with token usage (keeping skills lean), finding modularization opportunities in existing code, and catching plugin.json errors before they cause problems.

## Structure

The `skills/` directory contains skill implementations. `scripts/` has validation and analysis tools (previously scattered across plugins, now centralized here). `src/abstract/` is the shared Python package. `docs/` holds technical documentation and ADRs.

## Documentation

For migration from older tool locations, see `docs/migration-guide.md`. The Python package structure is documented in `docs/python-structure.md`. Each skill has its own `SKILL.md` with usage details. Run `make status` for a project overview.

Architecture decisions are recorded in `docs/adr/`. The plugin composition model for claude-night-market is explained in `docs/multi-plugin-design.md`.

## Security

The CI pipeline runs Bandit, Safety, and Semgrep on each push. Pre-commit hooks catch issues locally before commits reach the repo. See [SECURITY.md](SECURITY.md) for the vulnerability reporting process.

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

The tests in `test_skill_structure.py` check that skill descriptions contain action verbs, include "Use when..." triggers, and are long enough to be useful. This catches skills that would be hard to discover or understand.
