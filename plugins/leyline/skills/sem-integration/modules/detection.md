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

When sem is not detected, present installation options
in priority order:

**Rust toolchain (preferred, works on all platforms):**

```bash
cargo install --locked sem-cli
```

**macOS (Homebrew, if formula exists):**

```bash
brew search sem-cli && brew install sem-cli
```

Note: the Homebrew formula may not exist. If `brew search`
returns no results, fall back to `cargo install` above.

**Linux (binary download):**

```bash
mkdir -p ~/.local/bin && curl -fsSL https://github.com/Ataraxy-Labs/sem/releases/latest/download/sem-x86_64-unknown-linux-gnu -o ~/.local/bin/sem && chmod +x ~/.local/bin/sem
```

## Prompt Template

When sem is missing, say:

> sem (semantic diff tool) can provide entity-level diffs
> instead of line-level diffs. Install it?
>
> - `cargo install --locked sem-cli` (any platform with Rust)
> - `brew install sem-cli` (macOS, if formula available)
> - Linux binary: `mkdir -p ~/.local/bin && curl -fsSL
>   https://github.com/Ataraxy-Labs/sem/releases/latest/download/sem-x86_64-unknown-linux-gnu
>   -o ~/.local/bin/sem && chmod +x ~/.local/bin/sem`
> - Or skip to use standard git diff

If the user declines, write `0` to the cache and
proceed with fallback for the rest of the session.

## Cache Invalidation

The cache file lives in `$CLAUDE_CODE_TMPDIR` which is
per-session. No explicit invalidation needed: each new
Claude Code session starts fresh.
