---
name: detection
description: sem CLI detection and install-on-first-use
parent_skill: leyline:sem-integration
estimated_tokens: 250
---

# sem Detection and Installation

## Detection Logic

1. Check session cache at
   `$CLAUDE_CODE_TMPDIR/sem-available`
2. If cache exists, use cached value
3. If no cache, run `command -v sem`
4. Write result to cache

## Install-on-First-Use

When sem is not detected, present installation options:

**macOS (Homebrew):**

```bash
brew install sem-cli
```

**Linux (binary download):**

```bash
curl -fsSL https://github.com/Ataraxy-Labs/sem/releases/latest/download/sem-x86_64-unknown-linux-gnu -o /usr/local/bin/sem && chmod +x /usr/local/bin/sem
```

**Rust toolchain available:**

```bash
cargo install --locked sem-cli
```

## Prompt Template

When sem is missing, say:

> sem (semantic diff tool) can provide entity-level diffs
> instead of line-level diffs. Install it?
>
> - `brew install sem-cli` (macOS)
> - `cargo install --locked sem-cli` (Rust toolchain)
> - Or skip to use standard git diff

If the user declines, write `0` to the cache and
proceed with fallback for the rest of the session.

## Cache Invalidation

The cache file lives in `$CLAUDE_CODE_TMPDIR` which is
per-session. No explicit invalidation needed: each new
Claude Code session starts fresh.
