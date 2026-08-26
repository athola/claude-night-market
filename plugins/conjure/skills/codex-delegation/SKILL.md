---
name: codex-delegation
description: Delegates tasks to the OpenAI Codex CLI (codex exec) via delegation-core. Use when delegation-core selects Codex or OpenAI credentials are already configured.
alwaysApply: false
category: delegation-implementation
tags:
- codex
- openai
- cli
- delegation
dependencies:
- delegation-core
tools:
- codex
- delegation_executor.py
usage_patterns:
- codex-cli-integration
- headless-ci-execution
complexity: intermediate
model_hint: standard
estimated_tokens: 550
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
- [Codex-Specific Details](#codex-specific-details)
- [Exit Criteria](#exit-criteria)

# Codex CLI Delegation

## Overview

OpenAI's Codex CLI ships as npm `@openai/codex` and installs a `codex`
binary. Its headless entry point is `codex exec`, which takes the
prompt as a positional argument and reuses saved CLI credentials.

## When To Use

- `delegation-core` selected `codex` for the task
- OpenAI credentials are already configured on the machine
- The work suits a second opinion from a non-Anthropic, non-Google
  model

## When NOT To Use

- The host is headless and `codex login` has never succeeded there.
  See the login caveat below
- The job checks out untrusted repository code. OpenAI's own docs warn
  against exposing the key as a job-level environment variable in that
  case

## Prerequisites

### Installation

```bash
npm install -g @openai/codex
```

Homebrew and a curl installer are also documented upstream.

### Authentication

Either persist an API key or log in interactively:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

Verification runs `codex login status`, which reports one of "Logged
in using an API key", "Logged in using ChatGPT", "Logged in using
Agent Identity", or "Not logged in". The service uses that probe
rather than checking a single variable, because either credential
path is valid and only the probe sees both.

`CODEX_API_KEY` scopes a credential to a single `codex exec` run.

## Quick Start

### Using the shared delegation executor

```bash
uv run python scripts/delegation_executor.py codex "Explain this module" \
  --files src/
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-codex PROMPT='Explain this module'
```

### Direct CLI usage

```bash
codex exec "Explain the retry logic in this package"
```

## Smart Delegation

`codex` declares the `code_execution` strength and ranks behind gemini,
qwen, minimax, glm and muse in the candidate order. It declares no
model ids, so `smart_delegate` leaves model selection to the CLI.

## Codex-Specific Details

| Property | Value |
|----------|-------|
| Binary | `codex` |
| Package | `@openai/codex` |
| Headless form | `codex exec <prompt>` |
| Prompt delivery | positional, stdin also supported |
| Version probe | `codex --version` |
| Auth probe | `codex login status` |
| Structured output | `codex exec --json` |

Login caveat worth knowing before scripting this: an open issue
(openai/codex#9253) reports that `codex login` fails outright on
headless hosts, over SSH or in containers, unless a workspace
administrator has separately enabled device-code auth. That is a
single reporter's account with no maintainer confirmation, but it is
the failure mode to check first when `codex exec` will not run
unattended. Persisting an API key beforehand avoids it.

## Exit Criteria

- [ ] `codex` resolves on PATH and answers `codex --version`
- [ ] `codex login status` reports a logged-in state rather than "Not
      logged in"
- [ ] The built command is `codex exec <prompt>` with the prompt last
      and no prompt flag before it
- [ ] File context was inlined into the prompt
- [ ] Output saved to `delegations/codex/YYYYMMDD_HHMMSS.md`
- [ ] This skill ran because `delegation-core` selected `codex`
