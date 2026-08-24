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
| LL-003 | open | A completeness score measured a different gap than the one I was closing | 2026-08-22 |
| LL-004 | open | Dogfooding priced a loop the test suite could not reach | 2026-08-23 |
| LL-005 | open | A guard I wrote to catch a defect reproduced it, and only the revert-test noticed | 2026-08-24 |

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

## LL-003: A completeness score measured a different gap than the one I was closing

- Status: open
- Date: 2026-08-22
- Phase: review
- Category: process
- Owner: alext
- Links: PR #662, commit 80e22e0f, discussion #682
<!-- key: 74088a4034cd -->

### What happened

Running /abstract:make-dogfood over PR #662, the dogfooder scored conjure at 100% coverage, 0 targets missing. Inspecting the plugin anyway showed demo-conjure-commands depending on two targets whose every recipe line is an @echo, all three advertising (LIVE). Running the aggregate printed "Demo Complete" having executed no plugin code.

### What went well / where we got lucky

Running `make help` on the real target, rather than trusting the score, surfaced delegate-setup and delegate-doctor already running the exact commands I had just drafted as new targets. The duplication was caught before it reached a commit.

### What did not work

I wrote demo-provider-status and demo-provider-doctor, about twenty lines, before discovering they duplicated existing targets. Reverted whole. The committed fix adds no targets at all: it repoints one prerequisite at delegate-setup and deletes three false (LIVE) labels, five insertions against five deletions.

### Root cause

The dogfooder measures documented commands against Makefile targets. Under that metric conjure was genuinely complete, and the report was correct. The metric cannot see "the aggregate runs nothing real", so a 100% score was consistent with the defect rather than evidence against it. I read a high score on one question as an answer to a different one, then reached for addition rather than inspection.

### Recommendation / action item

Action: before adding a target because a coverage tool reports a gap, or declines to, run the plugin's own `help` and read what already exists -- Owner: alext -- Due: standing -- Status: applied in 80e22e0f.

A score answers the question its metric asks, not necessarily the one you have, so treat a perfect score as a prompt to check what was measured. Guarded forward by tests/test_provider_status_demo_is_live.py, which fails any target advertising LIVE with an echo-only recipe.

## LL-004: Dogfooding priced a loop the test suite could not reach

- Status: open
- Date: 2026-08-23
- Phase: review
- Category: testing
- Owner: egregore maintainers
- Links: 9f31a878, e8f7ca78, docs/adr/0022-stop-hook-reinjection-as-continuation.md
<!-- key: 482f21373792 -->

### What happened

Egregore's Stop hook blocked the session from stopping whenever the manifest held active work, which is how the loop continues without a human turn. Twenty-eight unit tests covered that hook and all of them passed. Running the watchdog against a real project in tmux found three defects in the resume path within one session, including a one-word prompt that cost ten turns and roughly $0.70 of Opus because the block had no bound.

### What went well / where we got lucky

tmux was the right instrument and cost minutes. The measured numbers, one byte of log, a three second stall, ten turns, made each defect specific enough to fix without further investigation.

### What did not work

The unit tests. They asserted the hook's decision for a given manifest, which was correct in every case. The defect was that the same correct decision repeated forever, and repetition is not a property a single invocation can show.

### Root cause

The hook blocked on a static condition. A manifest with active work stays true until something advances the pipeline, so the hook's answer did not depend on whether the session could advance it. Nothing in the test suite modeled a sequence of stops, so nothing could have caught it.

### Recommendation / action item

- Action: bound the hook by stall detection and test the sequence, not the single decision (done, 9f31a878) -- Owner: egregore maintainers -- Due: 2026-08-23 -- Status: done
- Action: when a hook's decision feeds back into the next turn, write at least one test that calls it repeatedly and asserts the loop ends -- Owner: egregore maintainers -- Due: ongoing -- Status: open

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

## LL-005: A guard I wrote to catch a defect reproduced it, and only the revert-test noticed

- Status: open
- Date: 2026-08-24
- Phase: review
- Category: testing
- Owner: night-market maintainers
- Links: 100e045a, aaa42cf5, PR #662

### What happened

Cycle 3 of #662 closed 43 review findings. Several were of the form "this behavior is pinned by no test", so the fix was a new guard. Twice the guard I wrote had the same defect as the code it was guarding, and passed.

NB32 asked for per-lane coverage of a scan, because one global total could be satisfied by a single lane. My replacement parametrized over the lanes and globbed each pattern off the filesystem, so it measured the world rather than the scanner. Deleting two lanes from `INVOCATION_GLOBS` left it green.

NB40 asked for a login hint to stop being selected by a substring over prose. My test constructed the auth-unknown case, which `doctor_lines` handles in an earlier arm that prints the hint and returns. The test passed through code my change never touched.

### What went well / where we got lucky

Nothing about the passing suite distinguished either guard from a real one. The revert-test did, both times, at a cost of about a minute each: restore the old code, run the test, watch it stay green. Adopting revert-testing as a per-finding step rather than a per-cycle summary is what made the failures visible while the context was still loaded.

Probing installed binaries rather than inferring flags also paid: `ollama run --help` has no `--model`, which turned a cosmetic consistency fix into a latent bug fix.

### What did not work

Writing the guard and reading it back. Both guards looked right, named the right thing, and asserted something true. The assertion was true for a reason unrelated to the change.

### Root cause

A test written immediately after a fix is written against the author's model of the code, and the model is what was wrong in the first place. Green is not evidence. The only evidence a guard is load-bearing is that it goes red when its subject is removed. The two guards that failed this way were both cases where the code under test had a structure I had not fully read: a parametrized helper that took its data from the filesystem, and a function with an early `continue`.

### Recommendation / action item

- Action: revert-test every new guard individually before reporting it, not as a batch at the end of the cycle (done this cycle) -- Owner: night-market maintainers -- Due: 2026-08-24 -- Status: done
- Action: when a revert leaves a new test green, read the function's control flow before rewriting the test. Both misses here were an unread branch rather than a bad assertion -- Owner: night-market maintainers -- Due: ongoing -- Status: open
- Action: prefer probing an installed binary over inferring a CLI contract, and record the probe output in the comment that states the default -- Owner: conjure maintainers -- Due: ongoing -- Status: open
