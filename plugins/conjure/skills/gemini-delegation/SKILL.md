---
name: gemini-delegation
description: |
  Gemini CLI delegation workflow implementing delegation-core for Google's Gemini models.

  Triggers: gemini cli, gemini delegation, google gemini, 1M context, large file analysis,
  gemini batch, gemini summarization, gemini extraction

  Use when: delegation-core selected Gemini, need Gemini's 1M+ token context window,
  batch processing or large document summarization required

  DO NOT use when: deciding which model to use - use delegation-core first.
  DO NOT use when: gemini CLI not installed or authenticated.

  Consult this skill when implementing Gemini-specific delegation workflows.
category: delegation-implementation
tags: [gemini, cli, delegation, google, large-context]
dependencies: [delegation-core]
tools: [gemini-cli]
usage_patterns:
  - gemini-cli-integration
  - large-context-analysis
  - batch-processing
complexity: intermediate
estimated_tokens: 600
progressive_loading: true
modules:
  - modules/gemini-specifics.md
references:
  - delegation-core/modules/authentication-patterns.md
  - delegation-core/modules/quota-management.md
  - delegation-core/modules/usage-logging.md
  - delegation-core/modules/error-handling.md
---

# Gemini CLI Delegation

## Overview

This skill implements `conjure:delegation-core` for the Gemini CLI. It provides Gemini-specific authentication, quota management, and command construction using shared patterns.

## When to Use
- After `Skill(conjure:delegation-core)` determines Gemini is suitable
- When you need Gemini's large context window (1M+ tokens)
- For batch processing, summarization, or pattern extraction tasks
- If the `gemini` CLI is installed and authenticated

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

## Delegation Flow

Implements standard delegation-core flow with Gemini specifics:

1. `gemini-delegation:auth-verified` - Verify Gemini authentication
2. `gemini-delegation:quota-checked` - Check Gemini API quota
3. `gemini-delegation:command-executed` - Execute via Gemini CLI
4. `gemini-delegation:usage-logged` - Log Gemini API usage

## Quick Start

### Basic Command
```bash
# File analysis
gemini -p "@path/to/file Analyze this code"

# Multiple files
gemini -p "@src/**/*.py Summarize these files"

# With specific model
gemini --model gemini-2.5-pro-exp -p "..."

# JSON output
gemini --output-format json -p "..."
```

### Save Output
```bash
gemini -p "..." > delegations/gemini/$(date +%Y%m%d_%H%M%S).md
```

## Shared Patterns

This skill uses shared modules from delegation-core:
- **Authentication**: See `delegation-core/modules/authentication-patterns.md`
- **Quota Management**: See `delegation-core/modules/quota-management.md`
- **Usage Logging**: See `delegation-core/modules/usage-logging.md`
- **Error Handling**: See `delegation-core/modules/error-handling.md`

## Gemini-Specific Details

For Gemini-specific models, CLI options, cost reference, and troubleshooting, see `modules/gemini-specifics.md`.

## Exit Criteria
- Authentication confirmed working
- Quota checked and sufficient
- Command executed successfully
- Usage logged for tracking
