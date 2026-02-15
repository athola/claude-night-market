# Abstract Plugin Infrastructure

Tools for building and evaluating Claude Code skills. Includes modular patterns, quality checks, and plugin validation.

## Quick Start

```bash
make check          # Install dependencies
make test           # Run quality checks
make install-hooks  # Set up git hooks
```

## Installation

Add to `marketplace.json`:

```json
{
  "name": "abstract",
  "source": { "source": "url", "url": "https://github.com/athola/abstract.git" },
  "description": "Meta-skills infrastructure - modular design and evaluation",
  "version": "1.4.3",
  "strict": true
}
```

Claude loads the plugin on startup.

## What's Included

Abstract provides skills, commands, and agents for plugin development. `methodology-curator` surfaces expert frameworks, while `modular-skills` provides architectural guidance. Use `skills-eval` to score and improve skill quality.

The `/validate-plugin` command checks structures against requirements. Specialized agents like `plugin-validator` and `meta-architect` assist during review.

## Structure

*   `skills/`: Skill implementations.
*   `scripts/`: Validation and analysis tools.
*   `src/abstract/`: Shared Python package.
*   `shared-modules/`: Reusable enforcement patterns for cross-skill reference.
    *   `iron-law-interlock.md`: Hard gate for TDD compliance in creation workflows.
    *   `enforcement-language.md`: Language intensity calibration.
    *   `anti-rationalization.md`: Bypass prevention patterns.
    *   `trigger-patterns.md`: Skill trigger design patterns.
*   `docs/`: Technical documentation, ADRs, and examples.
    *   `docs/examples/modular-skills/`: Implementation examples for modular skill patterns.

## Documentation

- **Skill Observability & Continual Learning**: `../../docs/guides/skill-observability-guide.md` - zero-dependency skill tracking with PreToolUse/PostToolUse hooks and stability gap detection
- **Skill Assurance Framework**: `docs/skill-assurance-framework.md` - patterns for reliable skill discovery (frontmatter-only triggers, enforcement language, migration guide)
- **Migration Guide**: `docs/migration-guide.md` - updating skills to new patterns
- **Python Structure**: `docs/python-structure.md` - package organization
- **ADRs**: `docs/adr/` - architecture decisions
- **Multi-Plugin Design**: `docs/multi-plugin-design.md` - composition model

Each skill has its own `SKILL.md` with usage details. Run `make status` for a project overview.

## Security

The CI pipeline runs Bandit, Safety, and Semgrep on each push. Pre-commit hooks catch issues locally.

```bash
make security   # Run security scans locally
```

## Development

```bash
make format        # Format code
make test          # Run all checks
make security      # Security scans
make clean         # Clean cache
make unit-tests    # Run tests
make test-coverage # Coverage report
```

Tests validate skill discoverability and structure.
