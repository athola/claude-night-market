# Conjure

Delegate tasks to external models from Claude Code. Delegate analysis, bulk work, and summarization to services like Gemini or Qwen.

Track quotas, log usage, and suggest delegation for large tasks.

## Installation

### As a Claude Code plugin

```bash
/plugin install athola@claude-night-market
/status
```

### Development setup

```bash
uv sync             # install deps
make install-hooks  # pre-commit hooks
make test           # lint + type + security checks
```

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/), and `tiktoken`.

## Usage

### Quick Start

```bash
# Check delegation readiness
make delegate-verify

# Select best service for a task
make delegate-auto PROMPT="Summarize src" FILES="src/"

# Monitor limits and usage
make quota-status
make usage-report
```

### Delegation Executor

```bash
# List services
uv run python tools/delegation_executor.py --list-services

# Verify a service
uv run python tools/delegation_executor.py --verify gemini

# Auto-select based on requirements
uv run python tools/delegation_executor.py auto "Analyze this code" \
  --files src/ --requirement large_context

# Force a specific service
uv run python tools/delegation_executor.py gemini "Summarize" \
  --files docs/*.md --model gemini-2.5-pro-exp
```

### Make Commands

```bash
# Development
make format          # ruff format + check --fix
make lint            # ruff check
make typecheck       # mypy + ty
make security-check  # bandit
make test            # lint + type + security bundle
make validate-all    # full validation including hooks
make clean           # remove caches/venv

# Delegation lifecycle
make delegate-status
make delegate-verify
make delegate-usage
make delegate-test
make delegate-gemini PROMPT="Analyze" FILES="src/main.py"
make delegate-qwen   PROMPT="Extract" FILES="src/**/*.py"
make delegate-auto   PROMPT="Best service" FILES="src/"

# Quota & usage
make quota-status
make usage-report
```

### Quota & Usage Tools

```bash
# Quota tracker (Gemini)
uv run python tools/quota_tracker.py --status
uv run python tools/quota_tracker.py --estimate src/ docs/
uv run python tools/quota_tracker.py --validate-config

# Usage logger (Gemini)
uv run python tools/usage_logger.py --report
uv run python tools/usage_logger.py --validate
uv run python tools/usage_logger.py --status
```

### In Claude Code

Use skills directly in chat:

```
Skill(conjure:delegation-core)
Skill(conjure:gemini-delegation)
Skill(conjure:qwen-delegation)
```

Hooks surface delegation suggestions for large tasks.

## Commands

### `delegate-auto`

Select the best external service based on requirements.

### `delegate-gemini` / `delegate-qwen`

Force a specific service with optional file globs and model hints.

### `quota-status`

Display current Gemini quota usage.

### `usage-report`

Summarize recent requests, token counts, and success rate.

### `validate-delegation`

Check configuration integrity.

## Architecture

The Conjure plugin is structured around several interconnected components that handle task delegation. The core plugin registers skills, commands, and hooks within Claude Code to provide access to delegation features. Execution paths are managed through specialized skills, while the delegation executor provides a unified interface for task processing and token estimation. Resource management is handled by the quota tracker and usage logger, which monitor limits and record outcomes respectively. Lifecycle automation and development tasks are coordinated through the project Makefile.

## Workflow

The task delegation process follows a systematic five-step workflow. First, the task is assessed through the `delegation-core` skill to determine if delegation is appropriate. Next, the `delegate-auto` command identifies the most suitable external service based on current requirements. The chosen task is then executed via the `delegation_executor`, and its progress is monitored through quota tracking and outcome logging. Finally, the results are integrated back into the active Claude session for the user.

## Configuration & Paths

- Delegation config: `~/.claude/hooks/delegation/config.json`
- Quota data: `~/.claude/hooks/gemini/usage.json`
- Usage logs: `~/.claude/hooks/gemini/logs/usage.jsonl`

## Development

```bash
uv sync
make lint typecheck security-check
make test
```

See `CHANGELOG.md` for release notes and `LICENSE` (MIT).

## License

MIT
