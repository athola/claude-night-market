---
name: qwen-delegation
description: Delegates tasks to Qwen CLI via delegation-core for Alibaba's models. Use when delegation-core selects Qwen or large-context batch processing is needed.
alwaysApply: false
category: delegation-implementation
tags:
- qwen
- cli
- delegation
- alibaba
- large-context
dependencies:
- delegation-core
tools:
- qwen-cli
- delegation_executor.py
usage_patterns:
- qwen-cli-integration
- large-context-analysis
- bulk-processing
complexity: intermediate
model_hint: standard
estimated_tokens: 600
progressive_loading: true
modules:
- modules/qwen-specifics.md
references:
- delegation-core/shared-shell-execution.md
---
## Table of Contents

- [Overview](#overview)
- [When to Use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Smart Delegation](#smart-delegation)
- [Qwen-Specific Details](#qwen-specific-details)


# Qwen CLI Delegation

## Overview

This skill implements `conjure:delegation-core` for the Qwen CLI.
It provides Qwen-specific authentication, quota management,
and command construction.

For shared delegation patterns, see `Skill(conjure:delegation-core)`.

## When To Use

- After `Skill(conjure:delegation-core)` determines Qwen is suitable
- When you need Qwen's large context window (100K+ tokens)
- For batch processing, summarization, or multi-file analysis
- If the `qwen` CLI is installed and configured

## When NOT To Use

- Choosing which provider to delegate to (use `conjure:delegation-core`)
- Gemini was the selected provider (use `conjure:gemini-delegation`)

## Prerequisites

**Installation:**
```bash
# Install Qwen CLI
npm install -g @qwen-code/qwen-code

# Verify installation
qwen --version

# Authenticate: run qwen once and complete the flow it offers
qwen
```

**There is no `qwen auth` subcommand.** `qwen --help` lists none, and
this file documented three that do not exist: `qwen auth status`,
`qwen auth login` and `QWEN_API_KEY`.
Anything after `qwen` that is not a recognized flag is delivered to the
model as the prompt, so `qwen auth status` asked Qwen the question
"auth status" and was billed for it.
Probed on 2026-08-22 it answered
`[API Error: 401 Incorrect API key provided]` and exited 0, which is
why the delegation registry now declares no auth probe for qwen.

Credentials land in `~/.qwen/oauth_creds.json`, which carries its own
`expiry_date`.
`~/.qwen/settings.json` exists without credentials, so it is not the
file to test.
The delegator reads the stated expiry and skips qwen without spawning
it, which is what stopped every chain walk paying for a rejected call.

**Verification:** `make -C plugins/conjure delegate-doctor` reports
qwen's credential state, including an expiry that has passed.

## Quick Start

### Using Shared Delegation Executor
```bash
# Basic file analysis
uv run python scripts/delegation_executor.py qwen "Analyze this code" \
  --files src/main.py

# With specific model
uv run python scripts/delegation_executor.py qwen "Summarize" \
  --files src/**/*.py --model qwen-max

# With output format
uv run python scripts/delegation_executor.py qwen "Extract functions" \
  --files src/main.py --format json
```

### Direct CLI Usage
```bash
# Basic command
qwen -p "@path/to/file Analyze this code"

# Multiple files
qwen -p "@src/**/*.py Summarize these files"

# Specific model
qwen --model qwen-max -p "..."
```

### Save Output
```bash
qwen -p "..." > delegations/qwen/$(date +%Y%m%d_%H%M%S).md
```

## Smart Delegation

The shared delegation executor can auto-select the best service:
```bash
# Auto-select a service for the task
uv run python scripts/delegation_executor.py auto "Analyze large codebase" \
  --files src/**/*
```

## Qwen-Specific Details

For Qwen-specific models, CLI options, cost reference,
and troubleshooting, see `modules/qwen-specifics.md`.

## Exit Criteria

- [ ] `qwen --version` exits 0 and `~/.qwen/oauth_creds.json` exists with
  an `expiry_date` in the future before any task is delegated. A missing
  installation or an expired credential is reported and stops execution.
  There is no `qwen auth status` to run, and asking for one bills a
  completion.
- [ ] The delegated task output is saved to `delegations/qwen/YYYYMMDD_HHMMSS.md` (timestamp
  format matching the Quick Start example), and that file exists on disk after delegation.
- [ ] If `conjure:delegation-core` selected a different provider (Gemini or local), this skill
  is not invoked; Qwen delegation only runs when delegation-core explicitly routes to Qwen.
- [ ] Smart delegation via `delegation_executor.py auto` logs which provider was selected and
  why before executing the task, so the selection is auditable.
