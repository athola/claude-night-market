# sem Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Integrate sem (semantic diff CLI) into five
night-market git workflow modules with install-on-first-use
and graceful fallback.

**Architecture:** A leyline foundation skill provides sem
detection, installation prompting, and output normalization.
Five consumer modules in imbue, pensive, and sanctum call
sem when available and fall back to git diff + grep when not.

**Tech Stack:** Markdown skills, Bash shell patterns, Python
(pytest for tests), sem CLI (Rust binary, externally installed)

**Spec:** `docs/superpowers/specs/2026-04-05-sem-integration-design.md`

---

## File Structure

| File | Purpose |
|------|---------|
| `plugins/leyline/skills/sem-integration/SKILL.md` | Foundation skill: detection, install, wrapper patterns |
| `plugins/leyline/skills/sem-integration/modules/detection.md` | Detection and install-on-first-use logic |
| `plugins/leyline/skills/sem-integration/modules/fallback.md` | Fallback output normalization patterns |
| `plugins/leyline/tests/unit/test_sem_integration.py` | Foundation skill tests |
| `plugins/imbue/skills/diff-analysis/modules/semantic-categorization.md` | Modify: add sem diff primary path |
| `plugins/imbue/skills/catchup/modules/git-catchup-patterns.md` | Modify: add sem diff + sem log |
| `plugins/pensive/skills/blast-radius/SKILL.md` | Modify: insert sem impact as middle tier |
| `plugins/sanctum/skills/git-workspace-review/SKILL.md` | Modify: add entity summary to Step 4 |
| `plugins/sanctum/skills/commit-messages/SKILL.md` | Modify: add sem diff for structured changes |

---

## Task 1: Create leyline:sem-integration Foundation Skill

**Files:**
- Create: `plugins/leyline/skills/sem-integration/SKILL.md`
- Test: `plugins/leyline/tests/unit/test_sem_integration.py`

- [ ] **Step 1: Write the failing test for sem detection**

```python
# plugins/leyline/tests/unit/test_sem_integration.py
"""Tests for leyline:sem-integration foundation skill."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSemDetection:
    """Feature: Detect sem CLI availability.

    As a night-market skill consumer
    I want to know if sem is installed
    So that I can choose semantic or fallback diff paths.
    """

    @pytest.mark.unit
    def test_detection_returns_true_when_sem_installed(
        self, tmp_path: Path
    ) -> None:
        """Given sem is on PATH, detection returns true."""
        cache = tmp_path / "sem-available"
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["which", "sem"], returncode=0,
                stdout="/usr/local/bin/sem\n"
            ),
        ):
            # Simulate detection logic
            result = subprocess.run(
                ["which", "sem"], capture_output=True, text=True
            )
            available = result.returncode == 0
            cache.write_text("1" if available else "0")

        assert cache.read_text() == "1"

    @pytest.mark.unit
    def test_detection_returns_false_when_sem_missing(
        self, tmp_path: Path
    ) -> None:
        """Given sem is not on PATH, detection returns false."""
        cache = tmp_path / "sem-available"
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["which", "sem"], returncode=1, stdout=""
            ),
        ):
            result = subprocess.run(
                ["which", "sem"], capture_output=True, text=True
            )
            available = result.returncode == 0
            cache.write_text("1" if available else "0")

        assert cache.read_text() == "0"

    @pytest.mark.unit
    def test_detection_caches_result(self, tmp_path: Path) -> None:
        """Given detection ran once, second call reads cache."""
        cache = tmp_path / "sem-available"
        cache.write_text("1")
        # No subprocess call needed: cache hit
        assert cache.read_text() == "1"


class TestFallbackNormalization:
    """Feature: Produce normalized output from git diff fallback.

    As a consumer module
    I want fallback output in the same schema as sem JSON
    So that I can use one code path for processing.
    """

    @pytest.mark.unit
    def test_parse_diff_filter_added(self) -> None:
        """Given git diff --diff-filter=A output, parse as additions."""
        raw = "plugins/leyline/skills/sem-integration/SKILL.md\n"
        entities = []
        for line in raw.strip().splitlines():
            entities.append({
                "name": Path(line).stem,
                "kind": "file",
                "change_type": "added",
                "file": line,
            })
        assert len(entities) == 1
        assert entities[0]["change_type"] == "added"
        assert entities[0]["name"] == "SKILL"

    @pytest.mark.unit
    def test_parse_diff_filter_modified(self) -> None:
        """Given git diff --diff-filter=M output, parse as modifications."""
        raw = "src/app.py\nsrc/utils.py\n"
        entities = []
        for line in raw.strip().splitlines():
            entities.append({
                "name": Path(line).stem,
                "kind": "file",
                "change_type": "modified",
                "file": line,
            })
        assert len(entities) == 2
        assert all(e["change_type"] == "modified" for e in entities)

    @pytest.mark.unit
    def test_empty_diff_produces_empty_list(self) -> None:
        """Given empty git diff output, produce empty entity list."""
        raw = ""
        entities = []
        for line in raw.strip().splitlines():
            if line:
                entities.append({
                    "name": Path(line).stem,
                    "kind": "file",
                    "change_type": "modified",
                    "file": line,
                })
        assert entities == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/leyline && uv run pytest tests/unit/test_sem_integration.py -v --no-cov`
Expected: PASS (these are self-contained tests that don't
import from the skill — they test the detection and
normalization logic patterns directly)

- [ ] **Step 3: Create the SKILL.md foundation skill**

```markdown
---
name: sem-integration
description: >
  Foundation skill for sem (semantic diff CLI) integration.
  Provides detection, install-on-first-use, and output
  normalization patterns for consumer skills.
version: 1.8.1
alwaysApply: false
category: infrastructure
tags:
- sem
- semantic-diff
- git
- foundation
provides:
  infrastructure:
  - sem-detection
  - sem-fallback
  patterns:
  - install-on-first-use
  - graceful-degradation
estimated_tokens: 400
progressive_loading: true
module_strategy: reference-based
modules:
- modules/detection.md
- modules/fallback.md
---

# sem Integration

Foundation patterns for using
[sem](https://github.com/Ataraxy-Labs/sem) semantic
diffs in night-market skills.

## When To Use

Consult this skill when building or modifying skills that
consume git diff output. It provides the detection,
installation, and fallback patterns.

## When NOT To Use

- Direct sem CLI usage (just run `sem diff` yourself)
- Skills that don't consume diff output

## Detection Pattern

Check sem availability once per session:

\`\`\`bash
# Detection (cache per session)
_sem_check() {
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
\`\`\`

When `_sem_check` returns `0`, offer installation.
See `modules/detection.md` for install-on-first-use
logic and platform-specific commands.

## Semantic Diff Pattern

Primary path (sem available):

\`\`\`bash
sem diff --json <baseline>
\`\`\`

Fallback path (sem unavailable):

\`\`\`bash
git diff --name-only --diff-filter=A <baseline>
git diff --name-only --diff-filter=M <baseline>
git diff --name-only --diff-filter=D <baseline>
git diff --name-only --diff-filter=R <baseline>
\`\`\`

See `modules/fallback.md` for output normalization
that produces the same entity schema from both paths.

## Impact Analysis Pattern

Primary path (sem available):

\`\`\`bash
sem impact --json <file-or-entity>
\`\`\`

Fallback path (sem unavailable): use rg/grep to trace
callers by filename. See `modules/fallback.md`.
```

- [ ] **Step 4: Create detection module**

Write `plugins/leyline/skills/sem-integration/modules/detection.md`:

```markdown
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
\`\`\`bash
brew install sem-cli
\`\`\`

**Linux (binary download):**
\`\`\`bash
curl -fsSL https://github.com/Ataraxy-Labs/sem/releases/latest/download/sem-x86_64-unknown-linux-gnu -o /usr/local/bin/sem && chmod +x /usr/local/bin/sem
\`\`\`

**Rust toolchain available:**
\`\`\`bash
cargo install --locked sem-cli
\`\`\`

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
```

- [ ] **Step 5: Create fallback module**

Write `plugins/leyline/skills/sem-integration/modules/fallback.md`:

```markdown
---
name: fallback
description: Output normalization for git diff fallback path
parent_skill: leyline:sem-integration
estimated_tokens: 250
---

# Fallback Output Normalization

When sem is unavailable, produce entity-like output from
standard git commands.

## Entity Schema

Both sem and fallback paths produce entries with:

\`\`\`json
{
  "name": "entity_or_filename",
  "kind": "function|class|file",
  "change_type": "added|modified|deleted|renamed",
  "file": "path/to/file.py"
}
\`\`\`

sem populates `kind` with function/class/method.
Fallback uses `file` as the kind since git diff
operates at file level.

## Fallback Commands

\`\`\`bash
# Collect changes by type
added=$(git diff --name-only --diff-filter=A <baseline>)
modified=$(git diff --name-only --diff-filter=M <baseline>)
deleted=$(git diff --name-only --diff-filter=D <baseline>)
renamed=$(git diff --name-only --diff-filter=R <baseline>)
\`\`\`

## Entity Extraction from Diff Hunks

For richer fallback (optional), parse diff hunks for
function/class definitions:

\`\`\`bash
# Extract added functions from diff
git diff <baseline> | grep '^+def \|^+class ' | \
  sed 's/^+//' | sed 's/(.*//'
\`\`\`

This gives function-level granularity without sem,
though it misses renames and cross-file dependencies.

## Impact Fallback

When `sem impact` is unavailable, trace callers with rg:

\`\`\`bash
# For each changed file, find importers
git diff --name-only HEAD | while read f; do
  module=$(basename "$f" .py)
  if command -v rg &>/dev/null; then
    rg -l "import.*$module|from.*$module" --type py .
  else
    grep -rl "import.*$module\|from.*$module" \
      --include="*.py" .
  fi
done | sort -u
\`\`\`
```

- [ ] **Step 6: Commit foundation skill**

```bash
git add plugins/leyline/skills/sem-integration/ \
  plugins/leyline/tests/unit/test_sem_integration.py
git commit -m "$(cat <<'EOF'
feat(leyline): add sem-integration foundation skill

Provides detection, install-on-first-use, and output
normalization patterns for integrating sem semantic
diffs into night-market git workflows.
EOF
)"
```

---

## Task 2: Refactor imbue:diff-analysis Semantic Categorization

**Files:**
- Modify: `plugins/imbue/skills/diff-analysis/modules/semantic-categorization.md`

- [ ] **Step 1: Read current file**

Read `plugins/imbue/skills/diff-analysis/modules/semantic-categorization.md`
to confirm content matches expected structure.

- [ ] **Step 2: Replace the Git Diff-Filter Examples section**

Replace lines 32-41 (the `## Git Diff-Filter Examples`
section) with a new section that uses sem as primary and
git diff-filter as fallback:

```markdown
## Entity-Level Diff (Primary: sem)

When [sem](https://github.com/Ataraxy-Labs/sem) is
available (see `leyline:sem-integration`), use
entity-level diffs:

\`\`\`bash
# Check sem availability
if command -v sem &>/dev/null; then
  sem diff --json <baseline>
fi
\`\`\`

This returns entities (functions, classes, methods)
with `change_type` of added, modified, deleted, or
renamed. Group by `change_type` to populate the
structural categories above.

## File-Level Diff (Fallback: git)

When sem is unavailable, use git's `--diff-filter`
flag to isolate change types at file level:

\`\`\`bash
git diff --name-only --diff-filter=A <baseline>  # Added files
git diff --name-only --diff-filter=M <baseline>  # Modified files
git diff --name-only --diff-filter=D <baseline>  # Deleted files
git diff --name-only --diff-filter=R <baseline>  # Renamed files
\`\`\`
```

- [ ] **Step 3: Verify the edit**

Read the modified file and confirm:
- sem primary path appears before fallback
- Fallback preserves all original git diff-filter commands
- Frontmatter unchanged

- [ ] **Step 4: Commit**

```bash
git add plugins/imbue/skills/diff-analysis/modules/semantic-categorization.md
git commit -m "$(cat <<'EOF'
feat(imbue): add sem diff as primary path in semantic categorization

Entity-level diffs via sem replace file-level git diff-filter
as the primary categorization method. Falls back to git
diff-filter when sem is unavailable.
EOF
)"
```

---

## Task 3: Add sem Impact as Middle Tier in pensive:blast-radius

**Files:**
- Modify: `plugins/pensive/skills/blast-radius/SKILL.md`

- [ ] **Step 1: Read current file**

Read `plugins/pensive/skills/blast-radius/SKILL.md`
to confirm the fallback section at lines 51-64.

- [ ] **Step 2: Insert sem impact tier between gauntlet and rg/grep**

Replace the current fallback block (lines 51-64) with a
two-tier fallback:

```markdown
   **Fallback tier 1 (sem available, no gauntlet)**:
   Use sem for cross-file dependency tracing:
   \`\`\`bash
   if command -v sem &>/dev/null; then
     sem impact --json <changed-file>
   fi
   \`\`\`

   This traces real function-level dependencies instead
   of filename matching. See `leyline:sem-integration`
   for detection patterns.

   **Fallback tier 2 (no sem, no gauntlet)**: Trace
   callers of changed functions with rg (or grep):
   \`\`\`bash
   # Prefer rg for speed; fall back to grep
   if command -v rg &>/dev/null; then
     git diff --name-only HEAD | while read f; do
       rg -l "$(basename $f .py)" --type py . 2>/dev/null
     done | sort -u
   else
     git diff --name-only HEAD | while read f; do
       grep -rl "$(basename $f .py)" --include="*.py" . 2>/dev/null
     done | sort -u
   fi
   \`\`\`
```

- [ ] **Step 3: Verify the three-tier structure**

Confirm the analysis now has three tiers:
1. gauntlet graph (step 2 main path)
2. sem impact (fallback tier 1)
3. rg/grep (fallback tier 2)

- [ ] **Step 4: Commit**

```bash
git add plugins/pensive/skills/blast-radius/SKILL.md
git commit -m "$(cat <<'EOF'
feat(pensive): add sem impact as middle-tier fallback in blast radius

Three-tier impact analysis: gauntlet graph (best),
sem impact (good, real dependency tracing), rg/grep
(basic, filename matching).
EOF
)"
```

---

## Task 4: Add Entity Summary to sanctum:git-workspace-review

**Files:**
- Modify: `plugins/sanctum/skills/git-workspace-review/SKILL.md`

- [ ] **Step 1: Read current Step 4 content**

Read `plugins/sanctum/skills/git-workspace-review/SKILL.md`
and locate Step 4 (line 78).

- [ ] **Step 2: Add sem entity summary to Step 4**

Replace the Step 4 paragraph (line 78-80) with:

```markdown
## Step 4: Review Diff Statistics (`diff-stat`)

Run `git diff --cached --stat` for staged changes (or
`git diff --stat` for unstaged work). Note the number of
files modified and identify hotspots with large insertion
or deletion counts.

When sem is available (see `leyline:sem-integration`),
also run `sem diff --staged` to display an entity-level
summary alongside the stat output. This shows which
functions, classes, and methods changed rather than just
line counts.
```

- [ ] **Step 3: Verify the edit**

Read the file and confirm:
- Step 4 preserves `git diff --stat` as the base command
- sem entity summary is additive, not replacing
- Step 5 unchanged

- [ ] **Step 4: Commit**

```bash
git add plugins/sanctum/skills/git-workspace-review/SKILL.md
git commit -m "$(cat <<'EOF'
feat(sanctum): add sem entity summary to workspace review

Step 4 now shows entity-level changes (functions, classes)
alongside git diff --stat when sem is available.
EOF
)"
```

---

## Task 5: Add sem Diff to sanctum:commit-messages

**Files:**
- Modify: `plugins/sanctum/skills/commit-messages/SKILL.md`

- [ ] **Step 1: Read current Step 1 content**

Read `plugins/sanctum/skills/commit-messages/SKILL.md`
and locate Step 1 (lines 34-40).

- [ ] **Step 2: Add sem to context gathering step**

Replace lines 34-40 with:

```markdown
1. **Gather context** (run in parallel):
   - `git status -sb`
   - `git diff --cached --stat`
   - `git diff --cached`
   - `git log --oneline -5`
   - When sem is available (see `leyline:sem-integration`):
     `sem diff --staged --json` for entity-level changes

   If nothing is staged, tell the user and stop.

   When sem output is available, use entity names
   (function, class, method) in the commit subject and
   body instead of parsing raw diff hunks. For example,
   "add function validate_webhook_url" instead of
   "add validation logic to notify.py".
```

- [ ] **Step 3: Verify the edit**

Read the file and confirm:
- All original context commands preserved
- sem is additive ("When sem is available")
- Usage guidance explains how to use entity names
- Steps 2-5 unchanged

- [ ] **Step 4: Commit**

```bash
git add plugins/sanctum/skills/commit-messages/SKILL.md
git commit -m "$(cat <<'EOF'
feat(sanctum): use sem entity names in commit message generation

Commit message skill now uses sem diff --staged --json
for entity-level change data when available, producing
more precise commit subjects.
EOF
)"
```

---

## Task 6: Add sem to imbue:catchup Patterns

**Files:**
- Modify: `plugins/imbue/skills/catchup/modules/git-catchup-patterns.md`

- [ ] **Step 1: Read current file**

Read `plugins/imbue/skills/catchup/modules/git-catchup-patterns.md`
to confirm the Git Delta Capture section (lines 28-41).

- [ ] **Step 2: Add sem-enhanced delta capture**

After the existing `## Git Delta Capture` section
(after line 41), insert a new section:

```markdown
## Semantic Delta Capture (sem)

When sem is available (see `leyline:sem-integration`),
enhance delta capture with entity-level diffs:

\`\`\`bash
# Entity-level change summary across commits
sem diff --json ${BASE}...HEAD

# Track a specific entity's evolution
sem log <entity-name>
\`\`\`

**Key advantages over git diff --stat:**
- Shows which functions/classes changed, not just files
- Distinguishes additions from modifications from renames
- `sem log` tracks an entity across renames

When sem is unavailable, fall back to the git commands
in the section above.
```

- [ ] **Step 3: Verify the edit**

Read the file and confirm:
- Original Git Delta Capture section unchanged
- New section appears after it
- Fallback reference points to original section

- [ ] **Step 4: Commit**

```bash
git add plugins/imbue/skills/catchup/modules/git-catchup-patterns.md
git commit -m "$(cat <<'EOF'
feat(imbue): add sem-enhanced delta capture to catchup patterns

Catchup now uses sem diff for entity-level change summaries
and sem log for entity history when sem is available.
EOF
)"
```

---

## Task 7: Register Foundation Skill and Update Plugin

**Files:**
- Modify: `plugins/leyline/.claude-plugin/plugin.json`

- [ ] **Step 1: Add sem-integration to leyline plugin.json**

Read `plugins/leyline/.claude-plugin/plugin.json` and add
`"./skills/sem-integration"` to the `skills` array in
alphabetical order.

- [ ] **Step 2: Run plugin validation**

```bash
python3 plugins/abstract/scripts/validate_plugin.py \
  plugins/leyline
```

Expected: validation passes with no errors.

- [ ] **Step 3: Run registration audit**

```bash
python3 plugins/sanctum/scripts/update_plugin_registrations.py \
  leyline --dry-run
```

Expected: no discrepancies.

- [ ] **Step 4: Commit**

```bash
git add plugins/leyline/.claude-plugin/plugin.json
git commit -m "$(cat <<'EOF'
chore(leyline): register sem-integration skill in plugin.json
EOF
)"
```

---

## Task 8: Run Full Test Suite and Verify

- [ ] **Step 1: Run leyline tests**

```bash
cd plugins/leyline && uv run pytest tests/unit/test_sem_integration.py -v --no-cov
```

Expected: all tests pass.

- [ ] **Step 2: Run imbue tests (regression check)**

```bash
cd plugins/imbue && uv run pytest tests/ -v --no-cov -x
```

Expected: all existing tests still pass.

- [ ] **Step 3: Run pensive tests (regression check)**

```bash
cd plugins/pensive && uv run pytest tests/ -v --no-cov -x
```

Expected: all existing tests still pass.

- [ ] **Step 4: Run sanctum tests (regression check)**

```bash
cd plugins/sanctum && uv run pytest tests/ -v --no-cov -x
```

Expected: all existing tests still pass.

- [ ] **Step 5: Run registration audit for all affected plugins**

```bash
python3 plugins/sanctum/scripts/update_plugin_registrations.py --dry-run
```

Expected: all plugins clean.

- [ ] **Step 6: Final commit (if any fixes needed)**

If any test or validation failures required fixes,
commit those fixes now.
