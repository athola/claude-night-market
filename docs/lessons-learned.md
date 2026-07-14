---
maturity: growing
type: lessons
updated: 2026-07-04
---

# Lessons Learned

Insights, failed approaches, rework, and blockers, captured blamelessly
so the team replicates what worked and avoids what did not.

## Active index

| ID | Status | Title | Date |
|----|--------|-------|------|
| LL-001 | open | Linked-worktree commits corrupt the index via hook-run git subprocesses | 2026-07-04 |

## Lessons

## LL-001: Linked-worktree commits corrupt the index via hook-run git subprocesses

- Status: open
- Date: 2026-07-04
- Phase: review
- Category: tooling
- Owner: -
- Links: PR #600, issue #609
<!-- key: 293e628a2673 -->

### What happened

Four commit attempts from a scratch git worktree for the PR 600 review fixes failed with escalating index corruption (~2,800 phantom staged deletions) before the root cause was found. The work was completed from a standalone clone, where the identical commit passed the full hook chain on the first try.

### What did not work

Retrying git commit with longer timeouts and repairing the index between attempts. The corruption was deterministic, not residue from the first killed run. Bootstrapping plugin venvs with uv sync --all-extras also backfired: installing optional packages (tiktoken, leyline-in-conjure) flipped mypy verdicts on except-ImportError fallback code.

### Root cause

git commit from a linked worktree exports GIT_DIR/GIT_INDEX_FILE to hook subprocesses. Test suites run by scripts/run-plugin-tests.sh spawn git in temp directories; with the leaked env their git add calls rewrote the real worktree index. Compounded by fresh plugin venvs diverging from the primary checkout (leyline tests import yaml but pyyaml is undeclared).

### Recommendation / action item

Resolved. Every test invocation in scripts/run-plugin-tests.sh now runs behind
scripts/without-git-env.sh, which unsets the whole GIT_* prefix. Committing from
a linked worktree is safe again.

The prescription this entry originally carried was to unset GIT_DIR,
GIT_INDEX_FILE and GIT_WORK_TREE by name, and that is the part worth keeping in
mind. A commit from a linked worktree exports eight GIT_* variables; naming
three of them left GIT_PREFIX, GIT_EDITOR, GIT_EXEC_PATH and the GIT_AUTHOR_*
trio reaching the test. When the leak is a category the tool populates at will,
scrub the category, not the three names you happened to think of. Declare pyyaml
in leyline's test deps.

## Archive

Superseded or deprecated entries sink here; nothing is deleted (git keeps history).

<!-- ENTRY TEMPLATE -- copy a block into the Lessons section above the Archive
heading, assign the next LL-NNN id, and fill it in. The journal_append helper
does this automatically; this block is the fallback for hand-editing.

## LL-NNN: <short lesson title>

- Status: open
- Date: YYYY-MM-DD
- Phase: execute | review
- Category: process | technology | requirements | testing | communication
- Owner: <who carries the follow-up>
- Links: <PR/commit/issue>, <related TR-NNN>

### What happened

<blameless, factual: the situation/activity>

### What went well / where we got lucky

<successes worth replicating>

### What did not work

<the gap or failure>

### Root cause

<5 Whys / contributing factors>

### Recommendation / action item

- Action: <specific change> -- Owner: <name> -- Due: <date> -- Status: <...>
-->
