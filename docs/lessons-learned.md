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

Never commit this repo from a linked worktree until issue #609 is fixed; use a standalone clone. Fix per #609: scrub GIT_* env in test-runner hooks (env -u GIT_DIR -u GIT_INDEX_FILE -u GIT_WORK_TREE) or add a conftest guard in suites that spawn git. Declare pyyaml in leyline's test deps.

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
