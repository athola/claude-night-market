---
name: opencode-delegation
description: Delegates tasks to OpenCode (opencode run) via delegation-core. Use when delegation-core selects OpenCode or a provider-agnostic harness is wanted.
alwaysApply: false
category: delegation-implementation
tags:
- opencode
- cli
- delegation
- provider-agnostic
dependencies:
- delegation-core
tools:
- opencode
- delegation_executor.py
usage_patterns:
- opencode-cli-integration
- provider-agnostic-routing
complexity: intermediate
model_hint: standard
estimated_tokens: 550
references:
- delegation-core/shared-shell-execution.md
---

# OpenCode Delegation

## Overview

OpenCode is an open-source, provider-agnostic terminal agent published
as npm `opencode-ai`. Its scripting entry point is `opencode run`,
which takes the prompt as positional arguments.

Being provider-agnostic makes it the most flexible entry in the
registry: the model behind it is whatever the local OpenCode config
selects, including a local one.

## When To Use

- `delegation-core` selected `opencode` for the task
- A provider the registry does not model directly is wanted, and
  OpenCode already has it configured
- A local or self-hosted model should serve the request

## When NOT To Use

- No provider credentials are configured. `opencode auth list` shows
  what is present
- A specific model must be pinned from this side. Model choice belongs
  to OpenCode's own config, not to the delegation call

## Prerequisites

### Installation

```bash
npm install -g opencode-ai@latest
```

Homebrew, pnpm, bun, scoop and chocolatey are also documented
upstream.

### Authentication

Credentials resolve per provider through environment variables such as
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, through a `.env` file, or
through `opencode auth login`. Stored credentials are written to
`~/.local/share/opencode/auth.json`, and the config file supports
`{env:VARIABLE_NAME}` interpolation.

Verification runs `opencode auth list`, because there is no single
variable to check when the provider set is open-ended.

## Quick Start

### Using the shared delegation executor

```bash
uv run python scripts/delegation_executor.py opencode "Find the bug" \
  --files src/
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-opencode PROMPT='Find the bug'
```

### Direct CLI usage

```bash
opencode run "Explain the use of context in this package"
```

## Smart Delegation

`opencode` declares the `code_execution` strength and ranks last among
the network providers in the candidate order, ahead only of the local
`glimmer` service. It declares no model ids, since model choice
belongs to OpenCode's own configuration.

## OpenCode-Specific Details

| Property | Value |
|----------|-------|
| Binary | `opencode` |
| Package | `opencode-ai` |
| Headless form | `opencode run <prompt>` |
| Prompt delivery | positional |
| Version probe | `opencode --version` |
| Auth probe | `opencode auth list` |

`opencode run --file <path>` attaches a file upstream, but this
service inlines file context into the prompt instead, which keeps one
delivery path across every provider that lacks an `@path` syntax.

`opencode serve` starts a headless HTTP server that `opencode run
--attach <url>` can target, and it honors `OPENCODE_SERVER_PASSWORD`.
That path is not modeled here: the registry spawns a process per
delegation rather than holding a server.

An output-format flag is documented for the `session list`, `export`
and `db` subcommands, but not confirmed for `run`, so none is
declared.

## Exit Criteria

- [ ] `opencode` resolves on PATH and answers `opencode --version`
- [ ] `opencode auth list` shows at least one configured provider
- [ ] The built command is `opencode run <prompt>` with the prompt last
      and no prompt flag before it
- [ ] File context was inlined into the prompt rather than passed with
      `--file`
- [ ] Output saved to `delegations/opencode/YYYYMMDD_HHMMSS.md`
- [ ] This skill ran because `delegation-core` selected `opencode`
