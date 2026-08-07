# Discussion board reconciliation, 2026-08-03

Twenty-two PR findings on the board were already fixed in the tree and
nobody had said so. This records the evidence for each, so the
write-back comment points at something a reader can check.

## Why the board looked worse than it was

The house convention reads a comment on a finding as "somebody triaged
this". 28 findings carried one. 46 did not, and the 2026-08-02 sweep
treated all 46 as open work. Verifying them against the tree found
roughly half already repaired, some of them months earlier.

Nothing was wrong with the fixes. No step in any workflow told the
board a finding was done, so a fixed finding and an ignored finding
were the same shape from the board's side, and every sweep paid to
re-derive the same answer. `scripts/reconcile_discussions.py` and the
`Addresses-Discussion:` trailer close that loop going forward. This
document is the one-time pass over the backlog that accumulated before
it existed.

## Verified fixed

Each row was checked against the working tree at commit `cf9d92c4`.

| # | Finding | Evidence |
|---|---------|----------|
| 512 | Python 3.9 hook compatibility broken | `pyproject.toml` pins `requires-python = ">=3.12"`; the 3.9 constraint no longer exists |
| 522 | 4 em dashes in `dora-metrics/SKILL.md` | `grep -c '—'` returns 0 |
| 523 | tier-1 slop word `actionable` | absent from `modules/agentic-workflow-signals.md` |
| 534 | em-dash density in harden docs | `SKILL.md` has 2 in 1457 words (1.4/1000); the rule targets 0-2/1000. Six sibling modules have 0 |
| 535 | `dora-metrics/SKILL.md` missing Exit Criteria | the section is present |
| 542 | Tier 5 slop tests pass on revert | `test_slop_patterns.py` sources regex from `get_tier5_patterns`, so removing the YAML section fails the tests |
| 543 | Tier 5 patterns absent from runtime source | `tier5` is present in `plugins/scribe/data/languages/en.yaml` |
| 544 | `logs-tokenizer` banned dep vs recommended tool | the clarifying note is in place: "external and not bundled, see Tier 3" |
| 559 | `re.IGNORECASE` undercuts the exact-phrase claim | no `IGNORECASE` remains in `web_research_handler.py` |
| 560 | annotation contradicts the isinstance guard | signature is `tool_response: dict[str, Any] \| str` |
| 561 | status regex matches 000-999 | guarded by `100 <= code < 600` |
| 562 | no integration test through `main()` | seven `main()` call sites in `test_web_research_handler.py` |
| 563 | (resolution record for 559) | same evidence as 559 |
| 564 | (resolution record for 560) | same evidence as 560 |
| 565 | (resolution record for 561) | same evidence as 561 |
| 566 | (resolution record for 562) | same evidence as 562 |
| 629 | `env -u GIT_DIR ...` repeated at four sites | replaced by `scripts/without-git-env.sh`; the literal survives only in a comment in `tests/unit/test_run_plugin_tests.py` |
| 630 | agent told "Levels 0-5" but Level 6 exists | `rust-auditor.md` says "Levels 0-6" and names Level 6 explicitly |
| 435 | prose lines exceed the 80-char wrap | three lines exceed it: the frontmatter `description` and two table rows, all excluded by `markdown-formatting.md` |
| 436 | ASCII arrow as a prose connector | `brainstorm→plan→execute` is gone; the line reads "brainstorm, plan, and execute" |

Two more are addressed by work in this branch rather than by prior
repairs:

| # | Finding | Evidence |
|---|---------|----------|
| 628 | the #609 guard runs in no automated gate | `make test` chains `test-ecosystem`, and `ecosystem-tests.yml` runs the root suite per PR. `c9a53ab2` closes the residual half: the trigger was narrower than the sweep, leaving 547 files unable to run the gate that reads them |
| 614 | silent commit abort from an auto-fixing hook | `e1cdc1b5` added the HEAD-comparison check to acp, commit-messages, and do-issue. It fired twice during this session's own commits |

## Left open

These were genuine backlog and were not closed by that pass. The
reconciler's untriaged ratchet was set to the real remaining count.

`#424` `#425` `#426` `#433` `#524` `#545` `#588` `#589` `#590` `#591`
`#592` `#593` `#594` `#595` `#605` `#606` `#607` `#611` `#624` `#625`
`#627`

`#524` and `#545` describe commits already in history (a folded
contract change, and a feature that landed on a release branch). Both
are process observations about the past rather than defects in the
tree, and neither can be repaired by editing code now.

## Closed out, 2026-08-06

All 21 are answered. The ratchet is 0 and the reconciler reports 33
triaged, 0 pending write-back, 0 mentioned, 0 untriaged.

Most were closed by commits carrying an `Addresses-Discussion:`
trailer, which is the loop working as designed: the fix lands, the
reconciler joins it against the board, and the comment posts itself.
Four needed a hand-written write-back because they were fixed before
the trailer convention existed (`#604`, `#610`, `#586`, `#520`), and
three were dispositions rather than fixes (`#424`, `#545`, `#524`).

Two results are worth keeping.

**The mention heuristic has a false positive, and it is structural.**
`#424` sat in the "mentioned in prose" bucket because commit
`6b28aa1a` names it. That commit did not fix it: it is the dogfood run
that *created* discussions #424-#436 by posting PR #417's findings to
the board. A commit that creates a discussion and a commit that
inspects one are the same shape to the heuristic. The bucket is still
the right design, since it keeps unproven claims out of the write-back
path, but it is a lead for a human and not a status. Read it as such.

**A third citation form had no gate.** Chasing `#433` surfaced that a
document naming a sibling capability as backticked `plugin:name` was
watched by nothing: `scripts/check_skill_graph_drift.py` matches only
the `Skill(...)` call syntax, and `tests/test_cited_paths_resolve.py`
needed a slash to recognize a token. 797 such references existed and
11 pointed at nothing, two of them at a `memory-palace:strategeion`
that was proposed in `0157d500` and never built. The gate now covers
that form, which is the same defect class as `#604`, `#610` and `#623`
arriving through a door nobody had checked.
