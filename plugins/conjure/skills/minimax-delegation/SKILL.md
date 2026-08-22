---
name: minimax-delegation
description: Delegates tasks to the MiniMax CLI (mmx) via delegation-core. Use when delegation-core selects MiniMax or large-context batch work is needed.
alwaysApply: false
category: delegation-implementation
tags:
- minimax
- cli
- delegation
- large-context
dependencies:
- delegation-core
tools:
- mmx-cli
- delegation_executor.py
usage_patterns:
- mmx-cli-integration
- large-context-analysis
- bulk-processing
complexity: intermediate
model_hint: standard
estimated_tokens: 600
progressive_loading: true
modules:
- modules/minimax-specifics.md
references:
- delegation-core/shared-shell-execution.md
---
## Table of Contents

- [Overview](#overview)
- [When to Use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Smart Delegation](#smart-delegation)
- [MiniMax-Specific Details](#minimax-specific-details)

# MiniMax CLI Delegation

## Overview

This skill implements `conjure:delegation-core` for the official MiniMax
CLI, `mmx`. It provides MiniMax-specific authentication, quota
management, and command construction.

For shared delegation patterns, see `Skill(conjure:delegation-core)`.

## When To Use

- After `Skill(conjure:delegation-core)` determines MiniMax is suitable
- When you need MiniMax-M3's large context window (1M tokens)
- For batch processing, summarization, or multi-file analysis
- If the `mmx` CLI is installed and authenticated

## When NOT To Use

- Choosing which provider to delegate to (use `conjure:delegation-core`)
- Another provider was selected (use that provider's delegation skill)

## Prerequisites

**Installation:**

Install the official CLI, published as `mmx-cli` and maintained by
MiniMax at `https://github.com/MiniMax-AI/cli`. It requires Node.js 18
or later and installs a binary named `mmx`.

```bash
npm install -g mmx-cli
mmx --version
```

Install `mmx-cli` by that exact name. Unrelated third-party packages
publish a binary called `minimax`, and this skill never invokes that
name.

**Authentication:**

Credentials are managed by the CLI, not by an environment variable.
`mmx` stores them in `~/.mmx/config.json`.

```bash
mmx auth login                      # interactive: OAuth or an API key
mmx auth login --api-key sk-xxxxx   # non-interactive, for CI
mmx auth status                     # canonical readiness check
```

`mmx auth status` is what `delegation_executor.py --verify` runs. A
successful `mmx --version` alone does not mean the CLI is authenticated.

**Regions:** MiniMax serves a global region (`api.minimax.io`) and a
mainland China region (`api.minimaxi.com`). API keys are issued per
region and are not interchangeable. API-key login detects the matching
region by probing both, so no manual base URL is normally needed. Set
the region explicitly with `mmx config set --key region --value cn` or
the `MINIMAX_REGION` environment variable.

## Quick Start

### Using Shared Delegation Executor

```bash
# Basic file analysis
python scripts/delegation_executor.py minimax "Analyze this code" --files src/main.py

# With specific model
python scripts/delegation_executor.py minimax "Summarize" --files src/ --model MiniMax-M3

# Verify the CLI is installed and authenticated
python scripts/delegation_executor.py minimax --verify
```

The executor reads the requested files and inlines their contents into
the prompt, because `mmx` has no `@path` context syntax. Inlined context
is capped at 96 KiB to stay inside the operating system limit on a
single argument, and any remainder is reported in the prompt and the
log.

### Direct CLI Usage

```bash
# Basic command
mmx text chat --message "Analyze this code"

# Specific model
mmx text chat --model MiniMax-M3 --message "Summarize this design"

# JSON output
mmx text chat --message "Extract the function names" --output json

# File contents must be passed in, not referenced
mmx text chat --message "Review this: $(cat src/main.py)"
```

### Save Output

```bash
mmx text chat --message "..." > delegations/minimax/$(date +%Y%m%d_%H%M%S).md
```

## Smart Delegation

The shared delegation executor can auto-select the best service:

```bash
uv run python scripts/delegation_executor.py auto "Analyze large codebase" \
  --files src/
```

## MiniMax-Specific Details

For MiniMax-specific models, CLI options, cost reference,
and troubleshooting, see `modules/minimax-specifics.md`.

## Exit Criteria

- [ ] `mmx --version` and `mmx auth status` both exit 0 before any task is
  delegated. A missing installation or failed authentication is reported and
  stops execution.
- [ ] Every spawned command starts with the `mmx` binary. No command in this
  skill or in `Delegator.SERVICES["minimax"]` invokes a binary named `minimax`.
- [ ] File context reaches the model as inlined contents. No `@path` reference
  appears in a prompt sent to `mmx`.
- [ ] The delegated task output is saved to
  `delegations/minimax/YYYYMMDD_HHMMSS.md` (timestamp format matching the
  Quick Start example), and that file exists on disk after delegation.
- [ ] If `conjure:delegation-core` selected a different provider, this skill is
  not invoked. MiniMax delegation only runs when delegation-core routes to it.
