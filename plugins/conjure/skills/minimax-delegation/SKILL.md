---
name: minimax-delegation
description: Delegates tasks to the MiniMax CLI via delegation-core for MiniMax-M3 and MiniMax-M2.7. Use when delegation-core selects MiniMax or large-context batch processing is needed.
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
- minimax-cli
- delegation_executor.py
usage_patterns:
- minimax-cli-integration
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

This skill implements `conjure:delegation-core` for the MiniMax CLI.
It provides MiniMax-specific authentication, quota management,
and command construction.

For shared delegation patterns, see `Skill(conjure:delegation-core)`.

## When To Use

- After `Skill(conjure:delegation-core)` determines MiniMax is suitable
- When you need MiniMax-M3's large context window (1M tokens)
- For batch processing, summarization, or multi-file analysis
- If the `minimax` CLI is installed and configured

## When NOT To Use

- Choosing which provider to delegate to (use `conjure:delegation-core`)
- Another provider was selected (use that provider's delegation skill)

## Prerequisites

**Installation:**

Install the MiniMax CLI, then verify it is on `PATH`:

```bash
# Verify installation
minimax --version

# Or set API key
export MINIMAX_API_KEY="your-key"
```

**Regional endpoints:** MiniMax serves two regions. Configure the
endpoint your account uses before delegating:

- Global: `https://api.minimax.io/v1`
- China: `https://api.minimaxi.com/v1`

Point the `minimax` CLI at the matching base URL per its configuration
guide. Both regions accept the same `MINIMAX_API_KEY` auth header.

**Verification:** Run the command with `--help` to confirm availability.

## Quick Start

### Using Shared Delegation Executor

```bash
# Basic file analysis
python ~/conjure/tools/delegation_executor.py minimax "Analyze this code" --files src/main.py

# With specific model
python ~/conjure/tools/delegation_executor.py minimax "Summarize" --files src/**/*.py --model MiniMax-M3

# With output format
python ~/conjure/tools/delegation_executor.py minimax "Extract functions" --files src/main.py --format json
```

### Direct CLI Usage

```bash
# Basic command
minimax -p "@path/to/file Analyze this code"

# Multiple files
minimax -p "@src/**/*.py Summarize these files"

# Specific model
minimax --model MiniMax-M3 -p "..."
```

### Save Output

```bash
minimax -p "..." > delegations/minimax/$(date +%Y%m%d_%H%M%S).md
```

## Smart Delegation

The shared delegation executor can auto-select the best service:

```bash
# Auto-select based on requirements
python ~/conjure/tools/delegation_executor.py auto "Analyze large codebase" \
  --files src/**/* --requirement large_context
```

## MiniMax-Specific Details

For MiniMax-specific models, CLI options, cost reference,
and troubleshooting, see `modules/minimax-specifics.md`.

## Exit Criteria

- [ ] `minimax --version` (and `MINIMAX_API_KEY` env var set) both exit 0 before any task is
  delegated; missing installation or failed authentication is reported and stops execution.
- [ ] The delegated task output is saved to `delegations/minimax/YYYYMMDD_HHMMSS.md` (timestamp
  format matching the Quick Start example), and that file exists on disk after delegation.
- [ ] If `conjure:delegation-core` selected a different provider, this skill is not invoked;
  MiniMax delegation only runs when delegation-core explicitly routes to MiniMax.
- [ ] Smart delegation via `delegation_executor.py auto` logs which provider was selected and
  why before executing the task, so the selection is auditable.
