# Conjure

Delegation to external models for Claude Code. Route long-context analysis, bulk work, and summarization to external LLM services (Gemini, Qwen) while keeping design and review in Claude.

The plugin tracks quotas, logs usage, and provides hooks that suggest delegation when tasks grow large.

## Installation

### As a Claude Code plugin (recommended)

The plugin wires in skills, hooks, and delegation tooling automatically.

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

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/), and `tiktoken`
for accurate token estimates:
`uv add tiktoken`

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

Hooks (`bridge.on_tool_start`, `bridge.after_tool_use`) surface delegation suggestions when tasks grow large or noisy.

## Commands

### `delegate-auto`

Auto-selects the best external service based on requirements (e.g., large context vs. sandbox execution).

### `delegate-gemini` / `delegate-qwen`

Force a specific service with optional file globs and model hints.

### `quota-status`

Shows current Gemini quota usage with warnings for approaching per-minute or daily limits.

### `usage-report`

Summarizes recent Gemini requests, token counts, and success rate from `~/.claude/hooks/gemini/logs/usage.jsonl`.

### `validate-delegation`

Checks configuration integrity for delegation limits and paths.

## Architecture

- **Claude Code plugin** – Registers skills, commands, and Gemini hooks.
- **Skills** – `delegation-core`, `gemini-delegation`, `qwen-delegation` for assessment and execution paths.
- **Delegation executor** – `tools/delegation_executor.py` provides unified command construction, verification, and execution with token estimation.
- **Quota tracker** – `tools/quota_tracker.py` monitors rate/daily limits with warnings.
- **Usage logger** – `tools/usage_logger.py` records requests, tokens, success, and duration with session rollups.
- **Hooks** – `hooks/gemini/bridge.*` recommend delegation when tool output size or volume suggests it.
- **Makefile** – Single entry point for dev, validation, and delegation workflows.

## How It Works

1. **Assess** – `delegation-core` evaluates if a task should delegate based on size, repetition, or sandbox needs.
2. **Select** – `delegate-auto` picks Gemini (large context) or Qwen (sandbox/CLI) using service metadata and requirements.
3. **Execute** – `delegation_executor` builds and runs service-specific commands, capturing stdout/stderr, timing, and estimated tokens.
4. **Monitor** – `quota_tracker` warns on rate/daily limits; `usage_logger` logs outcomes for reports.
5. **Integrate** – Results return to Claude for review, edits, and next actions.

## Configuration & Paths

- Delegation config overrides: `~/.claude/hooks/delegation/config.json`
- Quota data: `~/.claude/hooks/gemini/usage.json`
- Usage logs: `~/.claude/hooks/gemini/logs/usage.jsonl`
- Make targets reference `uv` for dependency management; adjust limits via `DEFAULT_LIMITS` in `tools/quota_tracker.py`.

## Development

```bash
uv sync
make lint typecheck security-check
make test
```

See `CHANGELOG.md` for release notes (current: 1.1.0) and `LICENSE` (MIT).

## License

MIT
