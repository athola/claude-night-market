# Claude Code LSP - Native Support Guide

**Status:** ✅ Configured via `~/.claude/settings.json`

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

```bash
# Terminal 1: Start Claude normally
$ claude

# Terminal 2: Watch for language server processes
$ watch-lsp
# or: watch -n 1 'ps aux | grep pyright | grep -v grep'

# In Claude: Ask semantic question
> "Find all references to AsyncAnalysisSkill"

# Terminal 2 shows: pyright-langserver process = PROOF!
```

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

- Claude Code 2.0.74+ (you have 2.0.76)
- `pyright` installed (`npm install -g pyright`)
- `pyright-lsp@claude-plugins-official` plugin enabled

All requirements are met on this system.

---

**Created:** 2026-01-05
**Configuration:** Settings-level (`~/.claude/settings.json`)
