---
name: gemini-delegation
description: Delegates tasks to Gemini CLI implementing delegation-core for Google's models. Use when delegation-core selects Gemini or 1M+ token context is needed.
alwaysApply: false
category: delegation-implementation
tags:
- gemini
- cli
- delegation
- google
- large-context
dependencies:
- delegation-core
tools:
- gemini-cli
usage_patterns:
- gemini-cli-integration
- large-context-analysis
- batch-processing
complexity: intermediate
model_hint: standard
estimated_tokens: 600
progressive_loading: true
modules:
- modules/gemini-specifics.md
references:
- delegation-core/../../leyline/skills/authentication-patterns/SKILL.md
- delegation-core/../../leyline/skills/quota-management/SKILL.md
- delegation-core/../../leyline/skills/usage-logging/SKILL.md
- delegation-core/../../leyline/skills/error-patterns/SKILL.md
---
## Table of Contents

- [Overview](#overview)
- [When to Use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Gemini-Specific Details](#gemini-specific-details)


# Gemini CLI Delegation

## Overview

This skill implements `conjure:delegation-core` for the Gemini CLI.
It provides Gemini-specific authentication, quota management,
and command construction.

For shared delegation patterns, see `Skill(conjure:delegation-core)`.

## When To Use

- After `Skill(conjure:delegation-core)` determines Gemini is suitable
- When you need Gemini's large context window (1M+ tokens)
- For batch processing, summarization, or pattern extraction tasks
- If the `gemini` CLI is installed and authenticated

## When NOT To Use

- Choosing which provider to delegate to (use `conjure:delegation-core`)
- Qwen was the selected provider (use `conjure:qwen-delegation`)

## Prerequisites

**Installation:**
```bash
# Verify installation
gemini --version

# Check authentication
gemini auth status

# Login if needed
gemini auth login

# Or set API key
export GEMINI_API_KEY="your-key"
```
**Verification:** Run the command with `--help` flag to verify availability.

## Quick Start

### Basic Command
```bash
# File analysis
gemini -p "@path/to/file Analyze this code"

# Multiple files
gemini -p "@src/**/*.py Summarize these files"

# With specific model
gemini --model gemini-3-pro -p "..."

# JSON output
gemini --output-format json -p "..."
```

### Save Output
```bash
gemini -p "..." > delegations/gemini/$(date +%Y%m%d_%H%M%S).md
```

## Gemini-Specific Details

For Gemini-specific models, CLI options, cost reference,
and troubleshooting, see `modules/gemini-specifics.md`.

## Exit Criteria

- [ ] `gemini --version` exits 0 before any task is delegated, and a missing
  installation is reported and stops execution.
- [ ] Authentication is judged from `GEMINI_API_KEY` and from the delegation's
  own exit code, never from `gemini auth status`. That command exits 0 while
  printing `Error authenticating: ProjectIdRequiredError` over a credential
  that cannot be used, so its status is not evidence. `delegation-core`'s
  shared module states the rule: authentication is never decided by running a
  provider's own CLI.
- [ ] The delegated task output is saved to
  `delegations/gemini/YYYYMMDD_HHMMSS.md` (timestamp format matching the Quick Start example),
  and that file exists on disk after the delegation completes.
- [ ] If `conjure:delegation-core` selected a different provider (Qwen or local), this skill
  is not invoked; Gemini delegation only runs when delegation-core explicitly routes to Gemini.
- [ ] Tasks requiring > 1M tokens in context are flagged before submission; the skill reports
  the estimated token count and confirms it falls within Gemini's supported window.
