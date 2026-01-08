# Plugin Development Guide

## Quick Start

Start by reviewing existing plugins in `plugins/` and the abstract patterns for reference. Follow the standard structure outlined below and ensure you run quality checks before submitting your work.

## Plugin Architecture

### Core Components
```
Plugin Structure
├── Skills          - Interactive capabilities
├── Commands        - Slash commands
├── Agents          - Specialized AI assistants
├── Hooks           - Event-driven automation
├── Scripts         - Python utilities
└── Configuration   - Plugin metadata
```

### Design Principles
Plugins should prioritize predictable behavior over "smart" guessing. Consistent patterns and standard tooling (ruff, mypy) reduce maintenance overhead. We aim for interoperability by strictly defining public APIs and avoiding hidden state.

## Success Metrics

Production-ready plugins meet these quality gates. Code coverage must exceed 80%, confirmed by `pytest-cov`. All Python code must pass `ruff` linting and `mypy` type checking without overrides. Security scans via `bandit` must return zero high-severity issues. Functionally, the documentation must include valid API references and copy-pasteable examples. Performance is capped at a 15K token budget for typical operations.

Good user experience requires discoverability and clear error messages. Plugins should fail gracefully with specific error details rather than generic "something went wrong" messages. Integration requires that plugins follow the versioning scheme (currently 1.1.0 alignment) and do not break existing workflows.

## Development Path

### Phase 1: Foundation
Begin by installing `uv` and `pre-commit` to set up your environment. Review the `plugins/abstract` structure to understand the core patterns, then initialize your plugin using `make create-plugin` and examine the generated files.

### Phase 2: Expansion
Implement your core logic by adding skills in `skills/` and commands in `commands/`. Enhance functionality with automation hooks and ensure reliability by adding comprehensive tests in the `tests/` directory.

### Phase 3: Production
Prepare for release by profiling token usage and running security scans. Document distinct features in `README.md` before submitting a Pull Request to the marketplace.

### Phase 4: Maintenance
Maintain the plugin by monitoring usage logs for errors and fixing reported issues. Add new features as needed and keep dependencies up to date using `uv`.

## Essential Tools

### Development
- **Python 3.10+**: Primary language.
- **uv**: Package manager.
- **Git**: Version control.
- **VS Code/PyCharm**: IDE (recommended).

### Quality Assurance
- **pytest**: Testing framework.
- **ruff**: Linting and formatting.
- **mypy**: Type checking.
- **bandit**: Security scanning.

### Automation
- **pre-commit**: Git hooks.
- **GitHub Actions**: CI/CD.

## Checklists

### Before Release
- [ ] All tests passing (>80% coverage).
- [ ] Code formatted and linted.
- [ ] Security scan passed.
- [ ] Documentation complete.
- [ ] Examples provided.
- [ ] Performance evaluated.
- [ ] Version tagged.
- [ ] Changelog updated.

### Code Review
- [ ] Follows style guidelines.
- [ ] Clear commit messages.
- [ ] Adequate tests.
- [ ] Handles edge cases.
- [ ] Error handling active.
- [ ] No hardcoded secrets.

### Documentation
- [ ] README with examples.
- [ ] Skill descriptions clear.
- [ ] API documented.
- [ ] Installation instructions.
- [ ] Contributing guidelines.

## Common Patterns

### Skill Pattern (Claude Code 2.1.0+)
```markdown
---
name: skill-name
description: Clear description with "Use when..." clause
category: workflow|analysis|generation|utility

# New in 2.1.0 - Optional fields:
context: fork              # Run skill in forked sub-agent context
agent: agent-name          # Specify agent type for execution
user-invocable: false      # Opt-out from slash command menu (default: true)
model: sonnet              # Model override for this skill

# YAML-style allowed-tools (cleaner than comma-separated)
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(npm *)            # Wildcard patterns supported
  - Bash(git * main)       # Wildcards at any position

# Hooks scoped to skill lifecycle (new in 2.1.0)
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "echo 'Pre-validation' >&2"
      once: true           # Run only once per session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./scripts/format-on-save.sh"
  Stop:
    - command: "echo 'Skill completed' >> ~/.claude/skill-log.txt"
---
# Skill Title
## Overview
## What It Does
## When to Use
## How to Use
## Examples
```

#### New Frontmatter Fields (2.1.0)

| Field | Type | Description |
|-------|------|-------------|
| `context` | `fork` | Run in forked sub-agent context (isolated context window) |
| `agent` | string | Specify agent type for skill execution |
| `user-invocable` | boolean | Show in slash command menu (default: true, set false to hide) |
| `hooks` | object | PreToolUse/PostToolUse/Stop hooks scoped to skill lifecycle |
| `allowed-tools` | list | YAML-style list (cleaner than comma-separated strings) |

#### Wildcard Permission Patterns

Claude Code 2.1.0 supports wildcards at any position in Bash tool permissions:

```yaml
# Pattern examples
allowed-tools:
  - Bash(npm *)       # All npm commands
  - Bash(* install)   # Any install command
  - Bash(git * main)  # Git commands with main branch
  - Bash(python:*)    # Python with any argument
```

### Command Pattern
```yaml
---
name: command-name
description: Action-oriented description

# New in 2.1.0 - Optional fields:
context: fork              # Run in forked sub-agent context
agent: agent-name          # Specify agent type

# Hooks scoped to command lifecycle
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

### Agent Pattern (Claude Code 2.1.0+)
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

# Hooks scoped to agent lifecycle (new in 2.1.0)
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./validate-command.sh"
      once: true                # Run only once per agent session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./post-edit-hook.sh"
  Stop:
    - command: "./cleanup.sh"   # Runs when agent completes

# Skills to auto-load (must be explicit, not inherited)
skills: [skill-name-1, skill-name-2]

# Escalation configuration
escalation:
  to: sonnet                    # Escalate to stronger model
  hints:
    - ambiguous_input
    - high_stakes
---

# Agent Name

Agent body content...
```

#### Agent Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (lowercase, hyphens) |
| `description` | string | Purpose, triggers, use cases |
| `tools` | list | Allowed tools (if omitted, inherits all) |
| `model` | string | Model alias (`haiku`, `sonnet`, `opus`) or `inherit` |
| `permissionMode` | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`, `ignore` |
| `skills` | list | Skills to auto-load (NOT inherited from parent) |
| `hooks` | object | PreToolUse/PostToolUse/Stop hooks scoped to agent lifecycle |
| `escalation` | object | Model escalation configuration |

### Error Handling Pattern
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.warning(f"Expected error: {e}")
    result = default_value
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise PluginError("Operation failed") from e
```

## Debugging Guide

### Common Issues

#### Plugin Not Loading
1. Check `.claude-plugin/plugin.json` syntax.
2. Verify paths are correct.
3. Check marketplace.json configuration.
4. Review Claude Code logs.

#### Tests Failing
1. Install dependencies: `make install`.
2. Check Python version: `python3 --version`.
3. Clear cache: `make clean`.
4. Run specific test: `pytest tests/test_specific.py -v`.

#### Performance Issues
1. Profile with: `python -m cProfile script.py`.
2. Check token usage estimates.
3. Implement caching.
4. Use lazy loading.

### Debug Tools
```bash
# Validate plugin structure
make validate

# Run with debug output
uv run python -m debugpy --listen 5678 script.py

# Check dependencies
uv pip list

# Analyze complexity
uv run python scripts/complexity_calculator.py
```

## Resources

### Official Documentation
- [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)

### Repository
- [GitHub Repository](https://github.com/athola/claude-night-market)
- [Issue Tracker](https://github.com/athola/claude-night-market/issues)
- [Discussions](https://github.com/athola/claude-night-market/discussions)

### Learning Resources
- [Abstract Plugin](../plugins/abstract/) - Meta-infrastructure and patterns.
- [Existing Plugins](../plugins/) - Real-world implementations.

## Contributing

Night Market welcomes contributions through issue reporting, pull requests, documentation improvements, and examples. When contributing, fork the repository, create a feature branch, and ensure all quality checks pass before submitting a PR.

### Development Workflow
1. Fork the repository.
2. Create feature branch.
3. Make changes with tests.
4. Run quality checks.
5. Submit pull request.

## Getting Help

If you encounter issues, check the issue tracker and documentation first. Discussion forums are open for questions. When reporting bugs, please use the provided template and include a minimal reproduction with environment details.

## Claude Code 2.1.0 Features

Key features in Claude Code 2.1.0 relevant to plugin development:

### Skill Hot-Reload

Skills created or modified in `~/.claude/skills` or `.claude/skills` are now **immediately available** without restarting the session. This enables rapid skill iteration during development.

**Development workflow:**
1. Edit SKILL.md
2. Save changes
3. Skill is immediately available (no restart needed)

### Context Forking

Use `context: fork` to run skills or commands in an isolated sub-agent context:

```yaml
---
name: isolated-analysis
description: Run analysis in isolated context
context: fork  # Creates fresh context window
---
```

**Benefits:**
- Isolated context prevents pollution of main conversation
- Failed operations don't affect main thread
- Parallel execution without context conflicts

### Agent Field in Skills

Specify which agent type should execute a skill:

```yaml
---
name: python-analysis
description: Python code analysis
agent: python-tester  # Use specific agent for execution
---
```

### Hooks in Frontmatter

Define lifecycle hooks directly in skill, command, or agent frontmatter:

```yaml
---
name: validated-skill
hooks:
  PreToolUse:
    - matcher: "Bash"
      command: "./validate.sh"
      once: true  # Run only once per session
  PostToolUse:
    - matcher: "Write|Edit"
      command: "./format.sh"
  Stop:
    - command: "./cleanup.sh"
---
```

**Hook Configuration:**
- `once: true` - Execute hook only once per session (useful for setup)
- `matcher` - Tool pattern to match (supports `|` for OR, `*` for wildcards)
- `command` - Shell command to execute

### YAML-Style Allowed-Tools

Use clean YAML lists instead of comma-separated strings:

```yaml
# Old style (still supported)
allowed-tools: Read, Grep, Bash(npm:*)

# New YAML-style (2.1.0+)
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(npm *)
  - Bash(* install)
```

### Wildcard Permission Patterns

Claude Code 2.1.0 supports wildcards at any position:

| Pattern | Matches |
|---------|---------|
| `Bash(npm *)` | All npm commands |
| `Bash(* install)` | Any install command |
| `Bash(git * main)` | Git commands with main branch |
| `Bash(python:*)` | Python with any argument |

### Skill Visibility Control

Skills are now visible in the slash command menu by default. Opt out with:

```yaml
---
name: internal-skill
user-invocable: false  # Hide from slash command menu
---
```

### Disabling Specific Agents

Use `Task(AgentName)` syntax in settings.json or `--disallowedTools` to disable specific agents:

```json
{
  "permissions": {
    "deny": ["Task(expensive-agent)", "Task(dangerous-agent)"]
  }
}
```

Or via CLI:
```bash
claude --disallowedTools "Task(expensive-agent)"
```

### Subagent Improvements

**Subagents now continue after permission denial**, allowing them to try alternative approaches instead of failing completely. This enables more resilient agent workflows.

**Skills show progress while executing** - tool uses display as they happen, giving visibility into skill execution.

### New Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_HIDE_ACCOUNT_INFO` | Hide email/org from UI (for streaming/recording) |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | Override default file read token limit |

### New Commands

- `/plan` - Shortcut to enable plan mode directly from prompt
- `/teleport` - Resume remote sessions (claude.ai subscribers)
- `/remote-env` - Configure remote sessions

## See Also

- [Cross-Plugin Collaboration](./cross-plugin-collaboration.md)
- [Skill Integration Guide](./skill-integration-guide.md)
- [Superpowers Integration](./superpowers-integration.md)
- [Claude Code Documentation](https://code.claude.com/docs)
