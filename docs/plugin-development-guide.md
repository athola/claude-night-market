# Plugin Development Guide

## Quick Start

1. Initialize a new plugin: `make create-plugin NAME=my-plugin`.
2. Review existing patterns in `plugins/abstract`.
3. Run `make validate` to check structure.
4. Verify code with `make lint` (ruff/mypy) and `make test`.

## Plugin Architecture

Plugins follow a standard directory structure to ensure Claude Code can discover capabilities:

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

Define strict public APIs to prevent hidden state and support interoperability between plugins. Use `ruff` for linting and `mypy` for type checking to identify errors early. Do not guess user intent; fail with specific error messages when inputs are invalid.

## Success Metrics

Plugins require at least 80% code coverage, verified by `pytest-cov`. Python code must pass `ruff` linting and `mypy` type checking without overrides. Security scans via `bandit` should report no high-severity issues.

Keep operations within a 15K token budget to stay within system prompt limits. Plugins should provide specific error details instead of generic messages. Align versions with the current 1.1.0 scheme to maintain compatibility with existing workflows.

## Development Path

### 1. Foundation
Install dependencies with `uv` and set up `pre-commit` hooks. Use `make create-plugin` to generate the scaffold, then examine `plugins/abstract` to understand core patterns for state management and tool calls.

### 2. Implementation
Add logic to `skills/` and commands to `commands/`. Write tests in `tests/` covering both success paths and edge cases. If your plugin requires automation, implement hooks to intercept tool usage or lifecycle events.

### 3. Production & Maintenance
Profile token usage with `python -m cProfile` if performance lags. Document features in `README.md` with copy-pasteable examples. Once released, monitor logs for runtime errors and update dependencies using `uv`.

## Tooling

The development environment relies on Python 3.10 or higher, managed by `uv` for dependency and environment isolation. We use `pytest` for unit and integration testing, while `ruff` handles both linting and formatting. Type checking is enforced by `mypy`, and security analysis is performed by `bandit`. Automation is provided by `pre-commit` for local checks and GitHub Actions for continuous integration.

## Release Checklist

- Tests passing with >80% coverage.
- `ruff` and `mypy` checks pass.
- `bandit` security scan reports zero high-severity issues.
- README includes clear usage examples.
- Token usage stays within the 15K limit.
- Version tags and changelog updated.

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

*   **Context Forking**: Set `context: fork` to run skills in an isolated sub-agent context, preventing output from polluting the main conversation thread.
*   **Agent Targeting**: Use the `agent` field to route skills to specific sub-agents (e.g., `python-tester`).
*   **Tool Permissions**: Use YAML lists for `allowed-tools`. Wildcards are supported (e.g., `Bash(npm *)`, `Bash(* install)`).
*   **Lifecycle Hooks**: Define `PreToolUse`, `PostToolUse`, or `Stop` hooks in frontmatter to automate validations or cleanup.

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

*   **Model Control**: Set the `model` to `haiku`, `sonnet`, or `opus`.
*   **Permissions**: `permissionMode` defines how the agent handles tool approvals (e.g., `acceptEdits`, `dontAsk`).
*   **Auto-loading Skills**: List skills in the `skills` field. Note that agents do not inherit skills from their parents.
*   **Escalation**: Configure `escalation` to move tasks to a more capable model when specific `hints` (like `ambiguous_input`) are detected.

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

If a plugin is not loading, verify the syntax and file paths in `.claude-plugin/plugin.json`, and check `marketplace.json` for any entry point mismatches. When tests fail, confirm that all dependencies are installed using `make install` and use `pytest tests/test_specific.py -v` to isolate the failing cases. For performance bottlenecks, profile the code with `python -m cProfile` and consider implementing caching or lazy loading for heavy modules.

### Utility Commands

```bash
make validate              # Check plugin structure
uv pip list                # Verify installed dependencies
uv run python scripts/complexity_calculator.py
```

## Advanced Features

### Skill Hot-Reload
Skills located in `~/.claude/skills` or `.claude/skills` reload immediately upon saving, removing the need to restart the session to test changes.

### Agent-Aware Hooks
SessionStart hooks receive an `agent_type` field in their input, allowing you to skip heavy context loading for lightweight agents. For example, skipping context for a `quick-query` agent can save between 200 and 800 tokens per session.

### Environment Overrides
Specific environment variables can be used to control behavior, such as `CLAUDE_CODE_HIDE_ACCOUNT_INFO` for sanitizing recordings or `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` to force synchronous execution in CI environments.

## Resources

*   [Official Claude Code Docs](https://code.claude.com/docs)
*   [Abstract Plugin Patterns](../plugins/abstract/)
*   [Existing Implementations](../plugins/)
