**Prefer rg (ripgrep) over grep for file search!**

When searching file contents from shell commands, prefer
`rg` (ripgrep) as the primary tool with `grep` as
fallback. This applies to code blocks in skills,
commands, agents, and any shell snippets.

**Pattern for scripts and hooks:**
```bash
if command -v rg &>/dev/null; then
  rg "pattern" --type py .
else
  grep -r "pattern" --include="*.py" .
fi
```

**Pattern for inline references:**
Use `rg "pattern"` (or `grep` if rg unavailable).

**Flag mapping (rg equivalents):**

| grep flag | rg equivalent |
|-----------|---------------|
| `grep -r` | `rg` (recursive by default) |
| `grep -rn` | `rg -n` (line numbers by default) |
| `grep -rl` | `rg -l` |
| `grep -c` | `rg -c` |
| `grep -q` | `rg -q` |
| `grep -v` | `rg -v` |
| `grep -E` | `rg -E` or `rg` (ERE by default) |
| `--include="*.py"` | `--type py` or `--glob "*.py"` |
| `grep -oP` | `rg -oP` |

**When grep is acceptable (no rg needed):**

- Piped single-line input: `echo "$var" | grep -q "pat"`
- Inside hook shell commands (minimal PATH)
- Pattern matching on command output (not file search)

**Why rg:** Faster on large codebases (parallel, respects
.gitignore by default), consistent regex syntax, better
defaults for code search.
