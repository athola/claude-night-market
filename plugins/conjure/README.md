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

Conjure components include:
- **Core Plugin:** Registers skills, commands, and hooks in Claude Code.
- **Specialized Skills:** Manage execution paths.
- **Delegation Executor:** Provides a unified interface for task processing and token estimation.
- **Resource Management:** Quota tracker and usage logger monitor limits and record outcomes.
- **Makefile:** Coordinates lifecycle automation and development tasks.

## Workflow

Task delegation follows a five-step process:
1.  **Assessment:** `delegation-core` determines if delegation is appropriate.
2.  **Selection:** `delegate-auto` identifies the best external service.
3.  **Execution:** `delegation_executor` processes the task.
4.  **Monitoring:** Quota tracking and logging record outcomes.
5.  **Integration:** Results return to the active Claude session.

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
