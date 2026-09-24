---
maturity: growing
type: lessons
updated: 2026-09-17
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
| LL-006 | open | A mechanism and the thing it claims to beat were indistinguishable to its own tests | 2026-08-25 |
| LL-007 | open | A dogfooding harness reported zero failures while masking two real ones | 2026-06-28 |
| LL-008 | open | Fixes that regress the tool that runs them | 2026-09-10 |
| LL-009 | open | Fifteen findings named one defect: gates that convert failure into output | 2026-09-02 |
| LL-010 | open | Review agents reported four criticals that one command refuted | 2026-09-02 |
| LL-011 | open | A package root put PyYAML in front of every stdlib-only hook | 2026-09-22 |
| LL-012 | open | uv run pre-commit vouched for hooks that git commit could not run | 2026-09-22 |

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

Action: before adding a target because a coverage tool reports a gap, or declines to, run the plugin's own `help` and read what already exists. Owner: alext. Due: standing. Status: applied in 80e22e0f.

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

- Action: bound the hook by stall detection and test the sequence, not the single decision (done, 9f31a878). Owner: egregore maintainers. Due: 2026-08-23. Status: done
- Action: when a hook's decision feeds back into the next turn, write at least one test that calls it repeatedly and asserts the loop ends. Owner: egregore maintainers. Due: ongoing. Status: open

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

- Action: revert-test every new guard individually before reporting it, not as a batch at the end of the cycle (done this cycle). Owner: night-market maintainers. Due: 2026-08-24. Status: done
- Action: when a revert leaves a new test green, read the function's control flow before rewriting the test. Both misses here were an unread branch rather than a bad assertion. Owner: night-market maintainers. Due: ongoing. Status: open
- Action: prefer probing an installed binary over inferring a CLI contract, and record the probe output in the comment that states the default. Owner: conjure maintainers. Due: ongoing. Status: open

## LL-006: A mechanism and the thing it claims to beat were indistinguishable to its own tests

- Status: open
- Date: 2026-08-25
- Phase: review
- Category: testing
- Owner: night-market maintainers
- Links: 3466862e,
  docs/adr/0023-continuation-baton-makes-a-dropped-turn-observable.md, PR #662

### What happened

The continuation baton exists to tell a stalled autonomous loop from a finished
one. Its entire claim over a plain timeout is that it measures a missed handoff
rather than elapsed time, so the session records a deadline at each handoff and
a turn that happens sets a new one.

Thirteen tests covered the round trip, the stranded case, the advancing case,
the cleared case and the corrupt file. All thirteen passed with `is_stranded`
mutated from `now > baton.deadline` into `now > baton.written_at + 1000.0`,
which is a plain age timeout and is exactly what the mechanism is supposed to
improve on.

The cause was in the implementation, not the tests. `advance_baton` recorded
`written_at=deadline`, collapsing two fields into one, so every fixture had the
two values equal and no assertion could separate them.

### What went well / where we got lucky

The revert test was run because LL-005 made it a per-guard step this cycle. It
cost under a minute and it caught a defect that thirteen green tests, a passing
type check and a passing lint did not.

The fix improved the design rather than only the test: `advance_baton` now takes
`now` as a required keyword, so the write time and the deadline cannot silently
be the same value again.

### What did not work

Reading the tests back. They named the right property ("stranded means stalled,
not old"), had a test class named after it, and asserted things that were true.
They were true for a reason unrelated to the mechanism, because the fixture data
made the two rules equivalent.

### Root cause

A guard can only distinguish two rules if some fixture separates them. Every
fixture here had `written_at` and `deadline` at values where an age rule and a
deadline rule agree, so the suite had no case that could tell them apart. Naming
the property in a class name is not the same as constructing the input that
discriminates it.

This generalizes past this module: when a design's whole justification is "not
the obvious simpler thing", at least one test has to be built from inputs where
the two diverge, and the honest way to find out whether one exists is to
implement the simpler thing and watch what fails.

### Recommendation / action item

- Action: when a mechanism is justified by being better than a simpler
  alternative, revert-test by substituting the simpler alternative, not only by
  deleting the code. Owner: night-market maintainers. Due: ongoing --
  Status: open
- Action: check that a dataclass's fields are independent in test fixtures
  before trusting assertions that depend on their difference. Owner:
  night-market maintainers. Due: ongoing. Status: open
- Action: wire the watchdog to consume the baton, with the dogfooding that
  ADR-0022's defect table came from. Owner: egregore maintainers. Due:
  unscheduled. Status: open

## LL-007: A dogfooding harness reported zero failures while masking two real ones

- Status: open
- Date: 2026-06-28
- Phase: review
- Category: tooling
- Owner: night-market maintainers
- Links: tests/unit/test_plugin_check_harness.py
<!-- key: 90e17bd1a287 -->

### What happened

A dogfooding pass over `make plugin-check` and the plugin Makefiles found
two recipes written as `cmd 2>/dev/null || echo "benign fallback"`. A real
failure, a missing file or an `E902` io-error, printed a harmless message
and the target still exited 0, so the harness reported zero failures while
masking defects as skips. conserve pointed at a stale `../conservation/`
path and parseltongue ran `ruff check parseltongue/` against a path that
does not exist, because the source lives under `src/`.

The same run hung for over eight minutes on `npx playwright --version` in
`plugins/scry`, with stdout and stderr redirected, so the stall was silent
and the run never reached the later plugins.

### What went well / where we got lucky

Driving the check from a detached tmux session kept the harness running
while other evidence gathering proceeded, and the session log captured
output that the redirected stdout would otherwise have hidden. That is how
the eight-minute stall became visible at all.

### What did not work

Reading a zero-failure report as evidence of health. The `|| echo` form
makes a defect and a skip indistinguishable to the caller, which is
sanitized optimism at the harness layer and defeats the point of a
dogfooding check.

### Root cause

The recipes conflated two different states. A tool that is genuinely absent
should skip with a stated reason. A tool that ran and failed should
propagate its exit code, and `2>/dev/null` swallowed the difference. The
repository already ships a `silent-failure-hunter` agent for this class of
bug in code, and the same lens applies to Makefile recipes. Presence probes
and intentional empty-result handlers are legitimate uses of `|| echo` and
stay.

The stall had a second cause: no step in the loop was bounded, so one
dependency probe that resolved over the network could hold the whole run.

### Recommendation / action item

- Action: distinguish absent from failed in Makefile recipes, skipping with
  a reason in the first case and propagating the exit code in the second.
  Owner: night-market maintainers. Due: ongoing. Status: closed, guarded by
  `tests/unit/test_plugin_check_harness.py`.
- Action: bound every harness step. Dependency probes use the non-fetching
  `npx --no-install playwright --version`, and the `plugin-check` loop wraps
  each plugin in `timeout 180`, so a hang surfaces as `(plugin-check failed
  or timed out)`. Owner: night-market maintainers. Due: ongoing. Status:
  closed.
- Action: wire the forced-eval skill-activation gate prototyped under
  `prototypes/forced-eval/`, which targets near-keyword-matching activation.
  Owner: night-market maintainers. Due: unscheduled. Status: open.
- Action: add a layer-count guard for the finite skill Discovery budget of
  about 16K characters, past which skills are dropped silently. Owner:
  night-market maintainers. Due: unscheduled. Status: open.
- Action: add an evidence-driven `review` mission type to attune, whose four
  existing types all assume building from artifacts. Owner: attune
  maintainers. Due: unscheduled. Status: open.

## LL-008: Fixes that regress the tool that runs them

- Status: open
- Date: 2026-09-10
- Phase: review
- Category: testing
- Owner: night-market maintainers
- Links: PR #784, commits e672375c..b0793bdc, c0d571d1
<!-- key: 39076f17582b -->

### What happened

A 60-item fix pass on PR #784 landed in 15 commits. Four of those
items needed rework because the first version was wrong in a way the run
that produced it could not show.

### What went well / where we got lucky

Every behavioral fix was revert-tested: undo the fix, confirm the test
goes red, restore. That is what caught both bad tests below, and it is a
per-fix step rather than a per-cycle summary because of LL-005.

Three new guard tests also found two defects no review pass had named.
`tests/test_hook_subprocess_budgets.py` AST-scans each registered hook's
timeout values against its hooks.json cap, and turned up a 5s git timeout
under a 1s SessionStart cap and a 3s notifier budget under a 1s Stop cap.

### What did not work

Two of the four broke the tooling itself.

Replacing a bare `$LINT_FIX` with `"${LINT_FIX[@]}"` in
run-plugin-lint.sh broke lint for all 18 plugins. bash 3.2, which is stock
/bin/bash on macOS, reports an empty array as an unbound variable under
`set -u`.

Inserting `status=0;` before `@$(PYTEST)` in conjure/Makefile moved the
`@` off the start of the recipe line, where it stops being a Make prefix
and becomes a syntax error. A comment three lines above documented that
exact trap.

The other two were tests that could not fail. An oracle sentinel test
passed with the sentinel check deleted, because `is_provisioned`
independently blocked the launch. A budget atomic-write test injected its
failure at `json.dumps`, which raises before `write_text` truncates, so
the file it was checking was never at risk.

### Root cause

Each fix was verified against the thing it changed rather than the thing
that runs it. The array quoting was checked against shellcheck instead of
the interpreter the script actually gets. The Makefile edit was read as
text instead of as a recipe.

The two bad tests share a different cause: the assertion was written
before finding out which guard the code path really depends on, so it
pinned a condition that was true for an unrelated reason.

### Recommendation / action item

Revert-test the test as well as the fix. A test that stays green with the
fix undone is not a test, whatever it asserts.

For shell, name the interpreter before choosing an idiom. On macOS that is
bash 3.2, and the portable empty-array expansion is ${arr[@]+"${arr[@]}"}.

For Makefiles, remember that an inserted line moves the `@` prefix, which
is only a prefix at the start of a recipe line.

## LL-009: Fifteen findings named one defect: gates that convert failure into output

- Status: open
- Date: 2026-09-02
- Phase: review
- Category: testing
- Owner: night-market maintainers
- Links: review a39c6168, commits 8555e33a, 64a4e439, 4835ab30
<!-- key: 8444b511c598 -->

### What happened

The Tier 3 review of 2026-09-02 (report at commit `a39c6168`) opened with
a finding that was not a bug. Fifteen findings across three review
dimensions named fourteen distinct defects of one shape: a quality check
that converted its own failure into output and exited 0.

conserve's `make test` ran no pytest at all. Root `validate-all` and
`plugin-check` echoed every validator failure and discarded stderr.
`test-coverage` re-ran pytest without coverage when `--cov-fail-under`
tripped. scribe's `lint` printed WARNING on a slop hit. Five abstract
audit targets ended in `|| echo`. The house shellcheck gate aborted on
macOS `/bin/sh` before it linted anything. Six test functions computed a
verdict and never asserted on it.

### What went well / where we got lucky

Nothing was hiding behind the gates. Run directly, conserve's suite was
787 passed. The targets were covering no defects. Each one had lost the
ability to report, so the repair was mechanical rather than a bug hunt.

### What did not work

A June commit, `fix(gates): make quality gates able to fail`, had already
fixed one instance of this class. Nobody searched for the rest, so
fourteen more survived three months.

The same session that produced the review had, earlier that day,
reported "conserve passed" on the strength of `make conserve-test`,
which runs lint, mypy and bandit and no pytest. A gate that cannot fail
does not only miss defects. It gets quoted as evidence that there are
none.

### Root cause

`|| echo`, `|| true`, a fallback re-run and a warning-level exit are each
locally reasonable: they keep a noisy target from blocking work. Nothing
checked whether a gate could still return nonzero, so each instance was
added without anyone seeing the class it joined.

### Recommendation / action item

- Action: a gate proves it can fail before it is trusted. Break what it
  checks, run it, confirm nonzero. Owner: night-market maintainers.
  Status: done. `8555e33a` repaired fourteen make targets, `64a4e439`
  the six tests, and `4835ab30` the shellcheck gate.
- Action: when one instance of a defect class is fixed, search for the
  rest before closing. Owner: night-market maintainers. Status: open.

## LL-010: Review agents reported four criticals that one command refuted

- Status: open
- Date: 2026-09-02
- Phase: review
- Category: process
- Owner: night-market maintainers
- Links: review a39c6168
<!-- key: 1de6ca43ca41 -->

### What happened

Nine agents ran the 2026-09-02 Tier 3 review, one per dimension, each
under the same output contract: a JSON findings file with verbatim
anchors, a citation verifier, a 40-line report. Three returned
conclusions that did not survive a check.

One reported six Python 3.9 incompatibilities in hooks, four of them
critical. Every file named carries `from __future__ import annotations`,
and one command refuted all six: each module imports cleanly under
`/usr/bin/python3` 3.9.6.

One measured conjure's Delegator at 910 lines. It had run in a worktree
that was auto-removed with its output, and the measurement was of a
pre-split commit. The class was 691 lines when the report was written.

One triaged 53 June findings as still standing. A one-line `rg` over all
209 SKILL.md files closed 13 of them at once, and reading a `.gitignore`
closed a fourteenth.

### What went well / where we got lucky

The output contract made each claim checkable. Verbatim anchors made a
wrong line number mechanical to catch, and the confirmations cost
seconds. Every finding ranked above medium was reproduced or re-read by
hand, which is why the refutations landed in the report instead of in
the fix pass.

### What did not work

The citation verifier catches a wrong anchor. It cannot catch a wrong
conclusion about a correct anchor, and that is the shape all three took.
The file was real, the line was right, the reasoning about it was not.

### Root cause

An agent reading a file in isolation reads an annotation without the
`__future__` import above it, reads a file without the commit it came
from, and reads a finding's anchor without the one-line query that
closes a whole category. Each missing check costs seconds, and nothing
in the contract asked for any of them.

### Recommendation / action item

- Action: a claim that a module fails to load, or that a version breaks,
  needs an execution result rather than a read. Owner: night-market
  maintainers. Status: open.
- Action: an agent that may run in a worktree writes findings outside it
  and states the commit it measured. Owner: night-market maintainers.
  Status: open.
- Action: before triaging an old findings list entry by entry, run the
  mechanical checks that could close a category at once. Owner:
  night-market maintainers. Status: open.

## LL-011: A package root put PyYAML in front of every stdlib-only hook

- Status: open
- Date: 2026-09-22
- Phase: execute
- Category: technology
- Owner: night-market maintainers
- Links: 496a8f68, 0a5c1dbb, tests/test_hooks_import_without_project_deps.py
<!-- key: d76f1b296e51 -->

### What happened

Every session start and stop printed a ModuleNotFoundError for PyYAML from a
memory-palace hook that wanted one stdlib-only name. Hooks run under the
operator's PATH python3, which carries no project dependencies. import
memory_palace.paths executed memory_palace/__init__.py first, and that file
eagerly re-exported a class whose module imports yaml. A sweep of all 52
registered hooks found the same shape in three more, across abstract and
hookify, one of them a regression on the branch.

### What went well / where we got lucky

Blocking yaml through sitecustomize in a subprocess reproduced the operator's
interpreter from inside a venv that has PyYAML. Running the sweep against the
installed 1.9.20 copies separated the branch regression from the pre-existing
bugs before any fix was chosen.

### What did not work

The first test covered one hook file and its name read as if it covered the
class. Guarding the leaf's import yaml was the tempting fix and the wrong one:
the leaf cannot parse an entry without yaml, so a guard degrades the module
silently instead of failing the hook loudly. In abstract, lazifying the root was
not enough either, because the hook imported through a yaml-bearing module
rather than past it.

### Root cause

import pkg.leaf executes pkg/__init__.py first. A package root that re-exports
for convenience turns every one of its dependencies into a dependency of every
leaf, and a hook only ever wants a leaf.

### Recommendation / action item

Action: package roots resolve exports on first attribute access, and helpers a
hook needs live in a stdlib-only module such as abstract/paths.py;
tests/test_hooks_import_without_project_deps.py fails on any registered hook
that cannot import with PyYAML blocked. Owner: night-market maintainers. Due:
2026-09-22. Status: done.

## LL-012: uv run pre-commit vouched for hooks that git commit could not run

- Status: open
- Date: 2026-09-22
- Phase: review
- Category: process
- Owner: night-market maintainers
- Links: 01295e0e, f1ed63b1, tests/test_precommit_entries_import_without_project_deps.py
<!-- key: f4af0d2bc4dd -->

### What happened

Committing a SKILL.md change failed in two pre-commit hooks with
ModuleNotFoundError for PyYAML. Both entries invoked python3 from PATH. Minutes
earlier, uv run pre-commit run --files had passed the same hooks on the same
files. A sweep of every bare-python3 entry found two more that would fail the
same way on their own trigger files.

### What went well / where we got lucky

The failing hook could be run the way git commit runs it, through the
interpreter named in .git/hooks/pre-commit with PATH reduced to
/opt/homebrew/bin:/usr/bin:/bin, and that reproduced the failure on demand. The
fix was the form slop-ratchet already used.

### What did not work

uv run puts the venv first on PATH, so a language: system entry that says
python3 resolves an interpreter with every dependency under uv and one with none
under git commit. A dry run through uv is not evidence for a hook. The
pin-freshness gate then held the config edit hostage to an unrelated action
bump, and pre-commit refuses to run while its own config is modified but
unstaged, so the two changes could not be committed apart.

### Root cause

Two interpreters share the name python3, and the check ran under the one that
never runs the hook.

### Recommendation / action item

Action: verify a language: system hook the way git commit runs it, not through
uv; run any entry that needs PyYAML as uv run --with pyyaml python;
tests/test_precommit_entries_import_without_project_deps.py fails on any
bare-python3 entry that cannot import with PyYAML blocked. Owner: night-market
maintainers. Due: 2026-09-22. Status: done.

## Archive

Superseded or deprecated entries sink here; nothing is deleted (git keeps history).

<!-- ENTRY TEMPLATE: copy a block into the Lessons section above the Archive
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

- Action: <specific change>. Owner: <name>. Due: <date>. Status: <...>
-->
