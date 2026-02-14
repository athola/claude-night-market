# Plugin Development Guide

## Quick Start

Initialize a new plugin with `make create-plugin NAME=my-plugin`. This command generates the standard directory structure and configuration files. Before writing code, review the patterns in `plugins/abstract` to understand how existing plugins handle state and tool calls. Once you have a basic implementation, run `make validate` to check the structure, followed by `make lint` and `make test` to verify code quality.

## Structure

Plugins use a standard directory structure so Claude Code can reliably discover capabilities without manual configuration.

```
plugins/my-plugin/
├── skills/         # YAML/Markdown skill definitions
├── commands/       # Slash command definitions
├── agents/         # Specialized sub-agent configurations
├── hooks/          # Event-driven automation scripts
├── scripts/        # Python utility logic
└── plugin.json     # Metadata and entry points
```

### Design Standards

Public APIs should be strict to prevent hidden state and support interoperability. We use `ruff` and `mypy` to catch errors early. When handling user input, fail with specific error messages rather than guessing intent. This reduces debugging time and prevents unexpected behavior.

## Success Metrics

We enforce strict quality gates to catch bugs before they reach production. Plugins must achieve 80% code coverage via `pytest-cov`, and Python code must pass `ruff` linting and `mypy` type checking without overrides. Security scans via `bandit` must report zero high-severity issues.

To maintain responsiveness, we limit token usage to a 15K budget per operation. Error messages must be specific to help users resolve issues quickly. Versioning follows the 1.1.0 scheme to maintain compatibility across the ecosystem.

## Development Path

### Foundation
Start by installing dependencies with `uv` and setting up `pre-commit` hooks. The `make create-plugin` command generates the necessary scaffold. We recommend examining `plugins/abstract` to understand core patterns for state management and tool calls before starting your implementation.

### Implementation
Add logic to `skills/` and commands to `commands/`. Tests in `tests/` should cover both success paths and edge cases. If your plugin requires automation, implement hooks to intercept tool usage or lifecycle events.

### Production & Maintenance
If performance lags, profile token usage with `python -m cProfile`. Documentation in `README.md` should include copy-pasteable examples to help users get started quickly. Once released, monitor logs for runtime errors and update dependencies using `uv`.

## Tooling

We use Python 3.10+ for plugin packages, managed by `uv`. `pytest` handles testing, while `ruff` manages linting and formatting. `mypy` enforces type checking, and `bandit` performs security analysis. `pre-commit` and GitHub Actions handle automation tasks.

### Python Version Requirements

The ecosystem has a two-tier Python requirement:

| Code Type | Minimum Python | Reason |
|-----------|---------------|--------|
| **Hooks** | **3.9+** | Execute under macOS system Python (3.9.6), outside virtual environments |
| Plugin packages & scripts | 3.10+ | Run inside `uv`-managed virtual environments |
| Root project & CI tooling | 3.12+ | Development-only, not user-facing |

**Hook compatibility is critical.** If a hook imports from a `src/` package, the entire transitive import chain must be 3.9-compatible. Avoid these patterns in hook code:

| Avoid | Python Version | Use Instead |
|-------|---------------|-------------|
| `X \| Y` union types | 3.10+ | `from __future__ import annotations` |
| `@dataclass(slots=True)` | 3.10+ | `@dataclass` (omit `slots`) |
| `match/case` statements | 3.10+ | `if/elif` chains |
| `datetime.UTC` | 3.11+ | `datetime.timezone.utc` |
| `import tomllib` | 3.11+ | `import tomli` with fallback |
| `type X = ...` aliases | 3.12+ | `TypeAlias` from `typing` |
| `import yaml` (pyyaml) | not stdlib | `try/except ImportError` with `yaml = None` fallback |

## Release Checklist

Before release, verify that tests pass with over 80% coverage and that `ruff`, `mypy`, and `bandit` checks are clean. The README must include clear usage examples. Verify that token usage remains within the 15K limit and that version tags and the changelog are updated.

## Common Patterns

### Skill Pattern
```markdown
---
name: skill-name
description: Clear description with "Use when..." clause
category: workflow|analysis|generation|utility
context: fork              # Run in isolated sub-agent context
agent: agent-name          # Specify agent type for execution
user-invocable: false      # Hide from slash command menu (default: true)
model: sonnet              # Model override

allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(npm *)            # Wildcard patterns supported

hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "echo 'Pre-validation' >&2"
      once: true           # Run once per session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./scripts/format-on-save.sh"
  Stop:
    - command: "echo 'Skill completed' >> ~/.claude/skill-log.txt"
---
# Skill Title
## Overview
## How to Use
## Examples
```

### Skill Configuration

Set `context: fork` to run skills in an isolated sub-agent context. This prevents output from polluting the main conversation thread. Use the `agent` field to route skills to specific sub-agents, such as `python-tester`. Tool permissions use YAML lists for `allowed-tools`, supporting wildcards like `Bash(npm *)` or `Bash(* install)`. Lifecycle hooks (`PreToolUse`, `PostToolUse`, `Stop`) defined in the frontmatter automate validations or cleanup.

### Command Pattern
```yaml
---
name: command-name
description: Action-oriented description
context: fork              # Optional: Run in forked sub-agent context
agent: agent-name          # Optional: Specify agent type

hooks:
  PreToolUse:
    - matcher: "Edit"
      command: "./validate.sh"
  Stop:
    - command: "echo 'Command completed'"

parameters:
  - name: required-param
    type: string
    required: true
examples:
  - "command-name --value example"
---
```

### Agent Pattern
```yaml
---
name: agent-name
description: |
  Agent purpose and specialization.
  Triggers: keyword1, keyword2, keyword3
  Use when: specific use cases for this agent
  DO NOT use when: when other tools are better suited

tools: [Read, Write, Bash, Glob, Grep]
model: haiku                    # Model for this agent
permissionMode: acceptEdits     # Permission handling
skills: [skill-name-1, skill-name-2] # Skills to auto-load

hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./validate-command.sh"
      once: true                # Run once per session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./post-edit-hook.sh"
  Stop:
    - command: "./cleanup.sh"

escalation:
  to: sonnet                    # Escalate to stronger model
  hints:
    - ambiguous_input
---
# Agent Name
Agent body content...
```

### Agent Configuration

Control the model by setting `model` to `haiku`, `sonnet`, or `opus`. Define how the agent handles tool approvals via `permissionMode` (e.g., `acceptEdits`, `dontAsk`). List skills to auto-load in the `skills` field. Note that agents do not inherit skills from their parents. Configure `escalation` to move tasks to a more capable model when specific `hints` (like `ambiguous_input`) are detected.

## Error Handling

Catch specific exceptions to provide actionable feedback. Log expected errors as warnings and use `PluginError` for failures that require user intervention.

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.warning(f"Operation skipped: {e}")
    result = default_value
except Exception as e:
    logger.error(f"Critical failure: {e}")
    raise PluginError("Failed to complete operation. Check network or permissions.") from e
```

## Debugging

### Common Issues

*   **Plugin not loading:** Verify syntax and paths in `.claude-plugin/plugin.json` and entry points in `marketplace.json`.
*   **Tests failing:** Run `make install` to check dependencies, then `pytest tests/test_specific.py -v` to isolate.
*   **Performance:** Profile with `python -m cProfile`. Consider caching or lazy loading for heavy modules.

### Utility Commands

```bash
make validate              # Check plugin structure
uv pip list                # Verify installed dependencies
uv run python scripts/complexity_calculator.py
```

## Advanced Features

### Skill Hot-Reload
Skills located in `~/.claude/skills` or `.claude/skills` reload immediately upon saving. This removes the need to restart the session to test changes.

### Agent-Aware Hooks
SessionStart hooks receive an `agent_type` field in their input. You can use this to skip heavy context loading for lightweight agents. For example, skipping context for a `quick-query` agent can save between 200 and 800 tokens per session.

### Environment Overrides
Specific environment variables control behavior:
- `CLAUDE_CODE_HIDE_ACCOUNT_INFO` - Sanitize recordings by hiding account info
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` - Force synchronous execution in CI environments
- `CLAUDE_CODE_TMPDIR` - Override temp directory for restricted environments (e.g., Termux)

**Temp Directory Best Practice**: When writing to temp files in hooks, use `${CLAUDE_CODE_TMPDIR:-/tmp}` to respect user configuration:
```bash
echo "log entry" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/my-audit.log
```

## Resources

*   [Official Claude Code Docs](https://code.claude.com/docs)
*   [Abstract Plugin Patterns](../plugins/abstract/)
*   [Existing Implementations](../plugins/)
