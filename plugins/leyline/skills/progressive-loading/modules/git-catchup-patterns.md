# Git Catchup Patterns

This module covers progressive-loading for git-based catchup
workflows: summarizing recent commits, surfacing what changed
since a baseline, and producing a handoff for the next session.
The loading question is which git tools and analysis modules to
pull in based on the size of the diff and the depth of summary
the user wants.

## When This Module Applies

Load this module when the task is:

- "What changed since I left?" after a session break.
- Preparing a handoff summary for another developer.
- Summarizing the work on a feature branch before review.
- Catching up on a repo you have not touched in a while.

For deep diff analysis with risk scoring, load the
`imbue:diff-analysis` skill instead. This module is about
catchup loading, not full diff review.

## Three Loading Tiers by Diff Size

The cost of analyzing a git range scales with the number of
commits and changed files. The loader picks a tier first.

| Tier | Diff Size | Modules Loaded |
|------|-----------|----------------|
| Quick | <10 commits, <20 files | `git-summary-quick.md` |
| Standard | 10-50 commits, <100 files | quick and `commit-grouping.md` |
| Deep | >50 commits or >100 files | standard and `chunked-analysis.md` |

The tier is computed once at the start of catchup. If the user
asks follow-up questions about specific files, the loader can
upgrade to the next tier without redoing earlier work.

## Establish Baseline First

Every catchup needs a baseline: "since when?". The default is
the merge-base with the upstream branch. The user can override
with a date, tag, or commit SHA.

```bash
# Default baseline: merge-base with upstream
BASE=$(git merge-base @ @{u} 2>/dev/null) || BASE=HEAD~10

# Show the size of the range
git log --oneline "$BASE"..HEAD | wc -l
git diff --stat "$BASE"...HEAD | tail -1
```

The three-dot `...HEAD` notation shows changes on the current
branch since divergence. The two-dot `..HEAD` shows commits
reachable from HEAD but not from the baseline. Catchup uses
both: dots-2 for commit lists, dots-3 for cumulative diffs.

## Quick Tier: Single Pass Summary

For small ranges, one pass over the log is enough.

```bash
git log --pretty=format:'%h %s' "$BASE"..HEAD
git diff --stat "$BASE"...HEAD
```

The quick module formats this into a short markdown summary.
No grouping, no per-file analysis. Token cost stays under 500.

## Standard Tier: Grouped by Subsystem

For medium ranges, group commits by subsystem (top-level
directory or component). Grouping makes the summary scannable.

```bash
# List changed files grouped by top directory
git diff --name-only "$BASE"...HEAD \
  | awk -F/ '{print $1}' \
  | sort \
  | uniq -c \
  | sort -rn
```

The grouping module reads this output and produces a heading
per subsystem with the relevant commits underneath.

## Deep Tier: Chunked Analysis

For large ranges, even the log output exceeds safe budgets. The
chunked module splits the range by week or by 20-commit windows
and summarizes each window separately.

```bash
# Split the range into weekly windows
git log --pretty=format:'%ad %h %s' --date=format:'%Y-W%V' \
  "$BASE"..HEAD \
  | awk '{print $1}' | sort -u
```

Each window summary is small. The merge step combines them into
a single digest. This keeps any one turn under the per-turn
token budget set in `performance-budgeting.md`.

## Pitfalls

1. **No baseline**: Without an explicit baseline, catchup
   produces unstable output as HEAD moves. Always pin the
   baseline at the start of the workflow.
2. **Skipping the size check**: Loading the deep-tier module
   for a 5-commit range wastes tokens. Always check size before
   tier selection.
3. **Reading every diff**: A 10000-line diff overwhelms context.
   Use `--stat` for size, then drill into specific files only
   when asked.
4. **Forgetting submodules**: `git diff --stat` does not show
   submodule content changes by default. Add `--submodule=diff`
   when submodules are involved.
5. **Mixing local and pushed history**: Catchup on unpushed
   commits is a different workflow than catchup on the upstream
   branch. Document which baseline the summary covers.

## Cross-Reference

See `git-patterns.md` for general git tooling patterns, and the
parent `SKILL.md` for how catchup modules plug into the
hub-and-spoke pattern.
