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
  "version": "1.0.1",
  "strict": true
}
```

Claude loads the plugin on startup.

## What's Included

*   **Skills**:
    *   `methodology-curator`: Surfaces expert frameworks before creating skills/hooks/agents. Includes 6 domain modules (instruction design, code review, debugging, testing, knowledge management, decision making).
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
