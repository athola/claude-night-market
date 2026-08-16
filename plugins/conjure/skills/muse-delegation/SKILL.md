---
name: muse-delegation
description: Delegates tasks to Meta's Muse Code CLI (muse) via delegation-core. Use when delegation-core selects Muse or repository-scale work needs a 1M-token context.
alwaysApply: false
category: delegation-implementation
tags:
- muse
- meta
- cli
- delegation
- large-context
dependencies:
- delegation-core
tools:
- muse
- delegation_executor.py
usage_patterns:
- muse-cli-integration
- repository-scale-analysis
- headless-ci-execution
complexity: intermediate
model_hint: standard
estimated_tokens: 600
references:
- delegation-core/shared-shell-execution.md
---

## Table of Contents

- [Overview](#overview)
- [When To Use](#when-to-use)
- [When NOT To Use](#when-not-to-use)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Smart Delegation](#smart-delegation)
- [Muse-Specific Details](#muse-specific-details)
- [Exit Criteria](#exit-criteria)

# Muse Code Delegation

## Overview

Muse Code is Meta's terminal coding agent, released August 2026 and
built on Muse Spark 1.2. It runs either as an interactive TUI or as a
one-shot headless command, and the headless form is what delegation
uses.

The binary is `muse`. Meta publishes no npm or PyPI package for it:
the documented install is a script served from Meta's own domain.

## When To Use

- `delegation-core` selected `muse` for the task
- Repository-scale reading where Muse Spark 1.2's 1M-token context
  helps
- Work that should run unattended, since `muse exec` is designed for
  CI

## When NOT To Use

- `META_API_KEY` is unset and the run cannot be interactive
- A specific model must be selected. Meta documents no `--model` flag
  for `exec`, so the CLI default stands
- Structured output is required. No output-format flag is documented
  for `exec`

## Prerequisites

### Installation

```bash
curl -fsSL https://dev.meta.ai/install.sh | sh
```

This pipes a remote script into a shell. Read
<https://dev.meta.ai/docs/muse-code> before running it. The guided
installer offers the same command and shows its source first:

```bash
make -C plugins/conjure delegate-setup
```

### Authentication

Meta documents the environment variable as the CI path:

```bash
export META_API_KEY="<your-key>"
muse exec "Run the test suite and summarize failures."
```

A bare `muse` prompts for browser sign-in on first run, which is not
usable unattended. There is no `muse auth status` command, so the
service declares an empty auth probe and verification checks
`META_API_KEY` instead.

## Quick Start

### Using the shared delegation executor

```bash
uv run python scripts/delegation_executor.py muse "Summarize this module" \
  --files src/
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-muse PROMPT='Explain this design'
```

### Direct CLI usage

```bash
muse exec "Explain the retry logic in this package"
```

## Smart Delegation

`muse` declares the strengths `code_execution` and `large_context`,
and sits behind gemini, qwen, minimax and glm in the candidate order.
It declares no model ids, so `smart_delegate` leaves model selection
to the CLI rather than passing a flag Meta does not document.

## Muse-Specific Details

| Property | Value |
|----------|-------|
| Binary | `muse` |
| Headless form | `muse exec <prompt>` |
| Prompt delivery | positional, no flag |
| Version probe | `muse --version` |
| Auth probe | none published |
| Auth | `META_API_KEY` |
| File context | inlined, no `@path` syntax |

The prompt is positional. A command ending in a flag would consume the
prompt as that flag's value, which is why the service config sets
`prompt_flag=None` and the War Room expert's command ends at
`muse exec`.

Two claims circulating in third-party guides are not in Meta's own
documentation and are not relied on here: a `--json` flag streaming
JSONL events to stdout, and `muse auth set --api-key-stdin`. The
confirmed JSONL reference is to on-disk session logs. Treat both as
unverified until Meta documents them.

## Exit Criteria

- [ ] `muse` resolves on PATH and `muse --version` answers
- [ ] `META_API_KEY` is set, or the operator accepted an interactive
      sign-in
- [ ] The built command is `muse exec <prompt>` with the prompt as the
      final argument and no prompt flag before it
- [ ] File context was inlined into the prompt rather than passed as
      `@path` references
- [ ] Output saved to `delegations/muse/YYYYMMDD_HHMMSS.md`
- [ ] This skill ran because `delegation-core` selected `muse`, not by
      default
