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
| LL-002 | open | A commit that creates a discussion and one that fixes it are the same shape to the reconciler | 2026-08-06 |

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

## LL-002: A commit that creates a discussion and one that fixes it are the same shape to the reconciler

- Status: open
- Date: 2026-08-06
- Phase: review
- Category: process
- Owner: -
- Links: PR #417, discussions #424-#436, commit 6b28aa1a
<!-- key: 19a7b929a791 -->

### What happened

The 2026-08-02 board sweep treated 46 uncommented findings as open work. Verifying them against the tree found roughly half already repaired, some months earlier. Discussion #424 in particular sat in the reconciler's "mentioned in prose" bucket because commit 6b28aa1a names it.

### What went well / where we got lucky

The mention bucket did its job. It kept an unproven claim out of the write-back path instead of posting a wrong "fixed" comment, so the false positive cost a human read rather than a bad board entry.

### What did not work

Reading the bucket as a status. Commit 6b28aa1a did not fix #424: it is the dogfood run that *created* discussions #424-#436 by posting PR #417's findings to the board. A commit that opens a discussion and a commit that repairs one both mention its number, and nothing in the text distinguishes them.

### Root cause

The house convention read a comment on a finding as "somebody triaged this", and no workflow step told the board when a fix landed. A fixed finding and an ignored one were the same shape from the board's side, so every sweep paid to re-derive the same answer. The mention heuristic inherits that ambiguity: mention is evidence of contact, not of repair.

### Recommendation / action item

Resolved for the forward path. scripts/reconcile_discussions.py and the Addresses-Discussion: trailer close the loop, so a fix now announces itself and the comment posts automatically. The mention bucket stays, and stays a lead for a human rather than a status: read an entry there as "a commit touched this number", then check which direction it touched it. Four findings fixed before the trailer convention existed (#604, #610, #586, #520) needed a hand-written write-back, which is the shape of every pre-trailer backlog item.

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
