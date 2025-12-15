# Conjure

Delegation to external models for Claude Code. Route long-context analysis, bulk work, and summarization to external LLM services (Gemini, Qwen) while keeping design and review in Claude.

The plugin tracks quotas, logs usage, and suggests delegation when tasks grow large.

## Installation

### As a Claude Code plugin (recommended)

```bash
/plugin install athola@claude-night-market
/status
```

### Development setup

```bash
uv sync             # install deps (or: make deps)
make install-hooks  # pre-commit hooks
make test           # lint + type + security checks
```

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/), and `tiktoken`.

## Usage

### Quick Start

```bash
# Check delegation readiness (auth + CLI availability)
make delegate-verify

# Auto-pick best service for a task
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

Hooks surface delegation suggestions when tasks grow large.

## Commands

### `delegate-auto`

Auto-selects the best external service based on requirements.

### `delegate-gemini` / `delegate-qwen`

Force a specific service with optional file globs and model hints.

### `quota-status`

Shows current Gemini quota usage with warnings.

### `usage-report`

Summarizes recent requests, token counts, and success rate.

### `validate-delegation`

Checks configuration integrity.

## Architecture

- **Claude Code plugin**: Registers skills, commands, and hooks.
- **Skills**: Assessment and execution paths.
- **Delegation executor**: Unified execution with token estimation.
- **Quota tracker**: Monitors limits.
- **Usage logger**: Records outcomes.
- **Hooks**: Recommend delegation based on output size.
- **Makefile**: Entry point for dev and validation.

## How It Works

1. **Assess**: Evaluate if a task should delegate (`delegation-core`).
2. **Select**: Pick Gemini or Qwen (`delegate-auto`).
3. **Execute**: Run commands and capture output (`delegation_executor`).
4. **Monitor**: Track limits and log outcomes.
5. **Integrate**: Return results to Claude.

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
