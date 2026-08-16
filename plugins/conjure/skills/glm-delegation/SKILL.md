---
name: glm-delegation
description: Delegates tasks to Z.ai GLM-5.x via the stock claude binary and an endpoint swap. Use when delegation-core selects GLM or a 1M-token context is needed.
alwaysApply: false
category: delegation-implementation
tags:
- glm
- zai
- endpoint-swap
- delegation
- large-context
dependencies:
- delegation-core
tools:
- claude
- delegation_executor.py
usage_patterns:
- endpoint-swap-integration
- large-context-analysis
- coding-plan-routing
complexity: intermediate
model_hint: standard
estimated_tokens: 650
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
- [GLM-Specific Details](#glm-specific-details)
- [Exit Criteria](#exit-criteria)

# GLM Delegation

## Overview

GLM ships no CLI of its own. Z.ai serves an Anthropic-compatible
endpoint, so the stock `claude` binary reaches GLM by changing two
environment variables and nothing else. This is the endpoint-swap
archetype: the redirection is environment, never argv.

GLM-5.3 was released on 2026-08-14 and claims a large coding gain over
GLM-5.2 from post-training alone.

## When To Use

- `delegation-core` selected `glm` for the task
- A 1M-token context is wanted through `glm-5.3[1m]`
- A GLM Coding Plan subscription should absorb the work instead of the
  Anthropic quota

## When NOT To Use

- `ZAI_API_KEY` is unset. Verification refuses rather than sending an
  unauthenticated request
- The `claude` binary is not installed. GLM has no fallback CLI
- A pinned GLM-5.3 identifier is required in a script that must not
  break: see the rollout note below

## Prerequisites

### Installation

Only the stock Claude Code binary is needed:

```bash
npm install -g @anthropic-ai/claude-code
```

### Authentication

```bash
export ZAI_API_KEY="<your-zai-key>"
```

The delegation service builds the child environment from that one
variable. Z.ai requires `ANTHROPIC_AUTH_TOKEN`, not
`ANTHROPIC_API_KEY`. Putting the key in the wrong one is the most
common way to get a 401 here, so the service names the correct
variable and the overlay references `${ZAI_API_KEY}` rather than
storing a secret.

## Quick Start

### Using the shared delegation executor

```bash
uv run python scripts/delegation_executor.py glm "Review this design" \
  --files docs/
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-glm PROMPT='Review this design'
```

### Direct CLI usage

```bash
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic \
ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY" \
claude --model glm-5.3 -p "Review this design"
```

## Smart Delegation

`glm` declares `code_execution` and `large_context` strengths and ranks
behind gemini, qwen and minimax in the candidate order. It declares
`glm-5.3` as its default, `glm-5.3[1m]` for large context, and
`glm-4.7` for fast response.

## GLM-Specific Details

| Property | Value |
|----------|-------|
| Binary | `claude` (stock) |
| Base URL | `https://api.z.ai/api/anthropic` |
| Auth variable | `ANTHROPIC_AUTH_TOKEN`, from `ZAI_API_KEY` |
| Default model | `glm-5.3` |
| Large context | `glm-5.3[1m]` |
| OpenAI-compatible URL | `https://api.z.ai/api/coding/paas/v4` |

The `[1m]` suffix is what unlocks the 1M-token window. Omitting it is
a documented setup mistake. Pair it with
`CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` when driving `claude`
directly.

Two operational notes. Environment changes only take effect in a
freshly launched shell, so an already-open session keeps reaching
Anthropic's real endpoint. And `claude` shows a first-run trust prompt
when it sees a non-Anthropic base URL. The `-p` non-interactive form
this service uses does not block on it.

Rollout caveat: at the time of writing, `docs.z.ai/devpack/latest-model`
documented `glm-5.3` while `docs.z.ai/guides/llm/glm-5.3` still read
"coming soon" and the base connection page still showed `glm-5.2`.
`GLM_52` stays defined for that reason, and `glm-4.7` remains the
fast-response id rather than being promoted on assumption.

The same archetype generalizes: MiniMax, Moonshot/Kimi, DeepSeek and
OpenRouter all expose Anthropic-compatible endpoints, so adding one is
a `ServiceConfig` with a different base URL.

## Exit Criteria

- [ ] `claude` resolves on PATH and answers `claude --version`
- [ ] `ZAI_API_KEY` is set, and `--verify` reports the service
      available rather than naming an unset variable
- [ ] The built command contains no `z.ai` URL: the endpoint travels in
      the child environment, not argv
- [ ] The child environment carries `ANTHROPIC_AUTH_TOKEN`, not
      `ANTHROPIC_API_KEY`
- [ ] Output saved to `delegations/glm/YYYYMMDD_HHMMSS.md`
- [ ] This skill ran because `delegation-core` selected `glm`
