# sem Integration: Semantic Diffs for Night Market Git Workflows

**Date:** 2026-04-05
**Status:** Implemented
**Branch:** fix/issues-359-377

## Problem

Night market git workflows parse raw `git diff` output to
understand what changed. This works but loses semantic
meaning: a 47-line diff doesn't tell you "2 functions
modified, 1 class added." Five modules across three plugins
manually reconstruct entity-level understanding from
line-level diffs.

[sem](https://github.com/Ataraxy-Labs/sem) provides
entity-level diffs natively via tree-sitter parsing of
21 languages. It outputs JSON with function/class/method
changes categorized as added, modified, deleted, or renamed.

## Decision

Refactor all five diff-consuming modules to use sem as the
primary engine with existing git diff + grep logic as
fallback. A new leyline foundation skill provides shared
detection, install-on-first-use, and output normalization.

## Architecture

```
leyline:sem-integration (foundation)
  +-- sem detection + install-on-first-use
  +-- fallback routing (sem -> git diff)
  +-- output normalization (sem JSON -> standard schema)

Consumers:
  imbue:diff-analysis          <- sem diff --json
  imbue:catchup                <- sem diff --json + sem log
  pensive:blast-radius         <- sem impact --json
  sanctum:git-workspace-review <- sem diff (entity summary)
  sanctum:commit-messages      <- sem diff --json
```

### Dependency Direction

leyline (foundation) provides the capability.
imbue, pensive, sanctum (higher layers) consume it.
This follows the existing layer dependency rule:
domain/utility plugins depend on foundation plugins.

## Foundation Skill: leyline:sem-integration

### Detection and Installation

1. Check `command -v sem` on first invocation per session
2. Cache result in `$CLAUDE_CODE_TMPDIR/sem-available`
3. If missing, offer installation:
   - macOS: `brew install sem-cli`
   - Linux/other: download binary from GitHub Releases
   - Rust toolchain available: `cargo install --locked sem-cli`
4. If user declines or install fails, set `SEM_FALLBACK=1`
   for the session and use existing git diff logic

### Wrapper Interface

The skill defines shell patterns that consumers copy
into their modules (not a shared script, since skills
are markdown-based):

```bash
# Detection (cache per session)
_sem_available() {
  local cache="${CLAUDE_CODE_TMPDIR:-/tmp}/sem-available"
  if [ -f "$cache" ]; then
    cat "$cache"
    return
  fi
  if command -v sem &>/dev/null; then
    echo "1" | tee "$cache"
  else
    echo "0" | tee "$cache"
  fi
}
```

### Output Schema

sem's JSON output is used directly. Consumers parse
the `entities` array, where each entry has:

```json
{
  "name": "validate_webhook_url",
  "kind": "function",
  "change_type": "modified",
  "file": "plugins/herald/scripts/notify.py",
  "old_span": {"start": 45, "end": 72},
  "new_span": {"start": 45, "end": 68}
}
```

Fallback produces the same shape by parsing
`git diff --diff-filter` output and inferring entity
names from `+def`, `+class`, `-def`, `-class` patterns.

## Consumer Changes

### 1. imbue:diff-analysis + semantic-categorization

**File:** `plugins/imbue/skills/diff-analysis/modules/semantic-categorization.md`

**Current:** Instructs Claude to run `git diff --diff-filter=A`,
`--diff-filter=M`, `--diff-filter=D`, `--diff-filter=R` and
manually categorize changes.

**With sem:** Replace the Git Diff-Filter Examples section.
Primary path runs `sem diff --json <baseline>` and groups
entities by `change_type`. Fallback path preserves current
`--diff-filter` commands.

**Behavioral change:** Categories become entity-level
("function `foo` added") instead of file-level
("file `foo.py` added").

### 2. pensive:blast-radius

**File:** `plugins/pensive/skills/blast-radius/SKILL.md`

**Current:** Three-tier impact analysis:
1. gauntlet graph (best)
2. rg/grep caller tracing (fallback)

**With sem:** Insert sem as middle tier:
1. gauntlet graph (best, full knowledge graph)
2. sem impact (good, cross-file dependency tracing)
3. rg/grep (basic, filename matching only)

**Behavioral change:** When gauntlet graph is unavailable
but sem is installed, impact analysis traces real
function-level dependencies instead of filename matches.

### 3. sanctum:git-workspace-review

**File:** `plugins/sanctum/skills/git-workspace-review/SKILL.md`

**Current:** Step 4 runs `git diff --cached --stat`.
Step 5 runs `git diff --cached` for detailed review.

**With sem:** Add entity-level summary to Step 4.
When sem is available, also run
`sem diff --staged --format plain` to show
"3 functions modified, 1 class added" alongside
the stat output. Step 5 unchanged (raw diff still
useful for line-level review).

**Behavioral change:** Additive only. Entity summary
appears alongside existing stat output.

### 4. sanctum:commit-messages

**File:** `plugins/sanctum/skills/commit-messages/SKILL.md`

**Current:** Reads `git diff --cached` to understand
staged changes for commit message generation.

**With sem:** When available, `sem diff --staged --json`
provides structured entity data. The commit message
skill can reference "added function X" and
"modified class Y" instead of parsing raw diff hunks.

**Behavioral change:** Commit messages become more
precise about what entities changed. Falls back to
current diff parsing when sem unavailable.

### 5. imbue:catchup

**File:** `plugins/imbue/skills/catchup/modules/git-catchup-patterns.md`

**Current:** Uses `git log --oneline` and `git diff --stat`
to summarize recent changes.

**With sem:** When available, `sem diff <base>..HEAD --json`
provides entity-level change summary across all commits.
Optional `sem log <entity>` tracks specific entity evolution.

**Behavioral change:** Catchup summaries include
"function X was modified in 3 commits" instead of
just file-level change counts.

## Testing Strategy

### Foundation Skill Tests

`plugins/leyline/tests/unit/test_sem_integration.py`:

- `test_detection_caches_result` - verify session caching
- `test_fallback_when_sem_missing` - verify graceful fallback
- `test_output_normalization` - verify fallback produces
  same schema as sem JSON
- `test_install_prompt_on_first_use` - verify installation
  offer when sem missing

### Consumer Tests

Each consumer gets tests for both paths:

- `test_with_sem_available` - mock sem JSON output,
  verify consumer processes it correctly
- `test_with_sem_unavailable` - verify existing fallback
  behavior unchanged

### Test Fixture

A shared `conftest.py` fixture toggles sem availability:

```python
@pytest.fixture(params=["sem", "fallback"])
def sem_mode(request, monkeypatch, tmp_path):
    cache = tmp_path / "sem-available"
    if request.param == "sem":
        cache.write_text("1")
    else:
        cache.write_text("0")
    monkeypatch.setenv("CLAUDE_CODE_TMPDIR", str(tmp_path))
    return request.param
```

## File Changes

| Plugin | File | Action |
|--------|------|--------|
| leyline | `skills/sem-integration/SKILL.md` | Create |
| leyline | `skills/sem-integration/modules/detection.md` | Create |
| leyline | `skills/sem-integration/modules/fallback.md` | Create |
| leyline | `tests/unit/test_sem_integration.py` | Create |
| imbue | `skills/diff-analysis/modules/semantic-categorization.md` | Modify |
| imbue | `skills/catchup/modules/git-catchup-patterns.md` | Modify |
| pensive | `skills/blast-radius/SKILL.md` | Modify |
| sanctum | `skills/git-workspace-review/SKILL.md` | Modify |
| sanctum | `skills/commit-messages/SKILL.md` | Modify |

**Total:** 4 files created, 5 files modified.

## Risks

1. **sem binary availability**: Not packaged in all Linux
   distros. Mitigated by install-on-first-use with multiple
   install methods and graceful fallback.
2. **sem output format changes**: sem is pre-1.0. JSON schema
   may change. Mitigated by pinning to a known version in
   install commands and testing against fixture data.
3. **Tree-sitter parsing gaps**: sem may not parse all
   languages in a polyglot repo. Mitigated by fallback to
   git diff for unsupported file types (sem does this
   internally with chunk-based diffing).

## Out of Scope

- MCP server integration (`sem-mcp`): evaluated but deferred.
  The CLI integration covers all current needs. MCP can be
  added later if Claude Code gains native sem-mcp support.
- `sem setup` (global git diff replacement): too invasive.
  We call sem explicitly where needed.
- `sem blame` integration: no current skill uses blame data.
  Can be added to a future code-archaeology skill.
- `sem context` (token-budgeted LLM context): interesting
  for context optimization but orthogonal to diff workflows.

## Success Criteria

1. All five consumers produce entity-level output when sem
   is installed
2. All five consumers work identically to today when sem
   is not installed
3. Install-on-first-use prompts exactly once per session
4. Tests pass for both sem and fallback paths
5. No new required dependencies added to any plugin
