# Conjure

Delegate tasks to external models from Claude Code.
Delegate analysis, bulk work, and summarization to Gemini, Qwen, MiniMax,
GLM, Meta Muse, Codex, OpenCode, or a Muse Glimmer running locally.

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

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/).

### Optional Dependencies

| Package | Purpose | Fallback |
|---------|---------|----------|
| tiktoken | Accurate token estimation | Heuristic (~4 chars/token) |
| leyline | Quota tracking | Stub tracker (disabled) |

For accurate token counts, install tiktoken:
```bash
pip install tiktoken
```

### Why delegation stays opt-in

Per [docs/inclusive-defaults.md][inc] (TRUE-exception
category 3), conjure delegation requires external CLIs
(`gemini`, `qwen`, `mmx`, `muse`, `codex`, `opencode`, `claude`,
`ollama`) that must be separately installed and
authenticated against third-party LLM providers. There is
no reasonable default: flipping is impossible, not merely
unwise.

[inc]: ../../docs/inclusive-defaults.md

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
uv run python scripts/delegation_executor.py --list-services

# Verify a service
uv run python scripts/delegation_executor.py --verify gemini

# Auto-select a service for the task
uv run python scripts/delegation_executor.py auto "Analyze this code" \
  --files src/

# Force a specific service
uv run python scripts/delegation_executor.py gemini "Summarize" \
  --files docs/*.md --model gemini-3-pro
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
make delegate-minimax PROMPT="Summarize" FILES="src/**/*.py"
make delegate-glm     PROMPT="Review this design"
make delegate-muse    PROMPT="Run the tests and summarize failures"
make delegate-codex   PROMPT="Explain this module"
make delegate-opencode PROMPT="Find the bug"
make delegate-glimmer PROMPT="Summarize" FILES="src/"   # local, no quota
make delegate-auto   PROMPT="Best service" FILES="src/"

# Getting set up
make delegate-setup     # which providers are installed and authenticated?
make delegate-doctor    # what is broken, and the command that fixes it
make delegate-install   # install what is missing, one confirmation each

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
Skill(conjure:minimax-delegation)
Skill(conjure:glm-delegation)
Skill(conjure:muse-delegation)
Skill(conjure:codex-delegation)
Skill(conjure:opencode-delegation)
```

Hooks surface delegation suggestions for large tasks.

## Commands

### `delegate-auto`

Select the best external service based on requirements.

### `delegate-<service>`

Force a specific service with optional file globs and model hints.
One target per registered provider: `gemini`, `qwen`, `minimax`,
`glm`, `muse`, `codex`, `opencode`, `glimmer`.

### `delegate-setup` / `delegate-doctor` / `delegate-install`

Report which provider CLIs are present and authenticated, name the
command that fixes each unhealthy one, and install the missing ones
after a confirmation showing the package, publisher, and source URL.
Install commands come only from the vetted provenance map, so an
unrecorded binary is refused rather than guessed at.

### `quota-status`

Display current Gemini quota usage.

### `usage-report`

Summarize recent requests, token counts, and success rate.

### `validate-delegation`

Check configuration integrity.

## Architecture

Conjure is built around a Core Plugin that registers skills, commands,
and hooks within Claude Code. Specialized Skills manage execution paths,
while a Delegation Executor provides a unified interface for task processing
and token estimation. Resource Management is handled by a quota tracker
and usage logger that monitor limits and record outcomes,
with a Makefile coordinating lifecycle automation and development tasks.

## Workflow

Task delegation begins with an **Assessment** by `delegation-core` to determine
if delegation is appropriate,
followed by **Selection** where `delegate-auto` identifies the best external
service. **Execution** is then handled by the `delegation_executor`,
with **Monitoring** provided by quota tracking and logging.
Finally, **Integration** returns the results to the active Claude session.

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

## Stewardship

Ways to leave this plugin better than you found it:

- Service selection criteria in `delegate-auto` are an
  opportunity to document the decision logic so users
  understand why one service was chosen over another
- Quota tracker error messages could guide users toward
  specific fixes when limits are reached
- The delegation executor would benefit from a quick
  troubleshooting section for common API failures
- Token estimation accuracy (tiktoken vs. heuristic)
  could include a comparison table showing divergence

See [STEWARDSHIP.md](../../STEWARDSHIP.md) for the full
stewardship principles guiding this project.

## License

MIT
