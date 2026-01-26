# Claude Code LSP - Native Support Guide

> **Status:** ✅ **FULLY OPERATIONAL** (Claude Code 2.1.16+)
>
> LSP support is confirmed working with active language server processes. Semantic queries for "find references", "go to definition", and similar operations trigger the appropriate LSP servers.
>
> **Verified Working:**
> - `ENABLE_LSP_TOOL=1` environment variable properly configured
> - Active LSP server processes (pyright-langserver, typescript-language-server)
> - Semantic queries trigger language servers as expected
>
> **Configuration:** `.cclsp.json` + `~/.claude/settings.json` environment setup

## Configuration (Settings-Level)

LSP is enabled globally in `~/.claude/settings.json`:

```json
{
  "env": {
    "ENABLE_LSP_TOOL": "1",
    "CLAUDE_DEBUG": "lsp"
  }
}
```

**No command-line flags or aliases needed.** Just run `claude`.

---

## Quick Proof of LSP Usage

**Live Verification (2026-01-25):**

```bash
# Check environment variables
$ echo "ENABLE_LSP_TOOL=$ENABLE_LSP_TOOL"
ENABLE_LSP_TOOL=1

# Check for active LSP processes
$ ps aux | grep -E "pyright-langserver|typescript-language-server" | grep -v grep | wc -l
10  # Multiple LSP servers active

# Verify language servers installed
$ which pylsp typescript-language-server
/home/alext/.local/bin/pylsp
/home/alext/.nvm/versions/node/v25.2.1/bin/typescript-language-server
```

**Result:** LSP is fully operational with 10 active server processes.

---

## Available Tools

| Script | Purpose |
|--------|---------|
| `watch-lsp` | Real-time LSP process monitoring |
| `scripts/lsp-diagnostic.sh` | Full system health check |
| `scripts/lsp-vs-grep-comparison.sh` | Compare LSP vs grep performance |
| `scripts/test-lsp-manually.sh` | Verify language servers work |

---

## Semantic vs Text Queries

**LSP-triggering (semantic):**
```
"Find all references to X"
"Go to definition of Y"
"Show all call sites of Z"
```

**Grep-triggering (text):**
```
"Search for text 'X'"
"Find files containing Y"
```

---

## Troubleshooting

```bash
# Run diagnostic
$ ./scripts/lsp-diagnostic.sh

# Check settings
$ grep -A 3 '"env"' ~/.claude/settings.json

# Verify language servers
$ which pyright typescript-language-server

# Check logs
$ ls ~/.claude/debug/
```

---

## Requirements

- Claude Code 2.0.74+ (verified working on 2.1.16+)
- `pyright` or `pylsp` installed
- `typescript-language-server` installed for TypeScript/JavaScript/Markdown

All requirements are met and verified operational.

---

**Created:** 2026-01-05
**Last Verified:** 2026-01-25 (LSP fully operational)
