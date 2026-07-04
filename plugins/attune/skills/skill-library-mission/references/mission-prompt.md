# Generalized Mission Prompt

The dispatch prompt below was distilled from the first successful
run of this mission (claude-night-market, 2026-07-02) and captured
on 2026-07-03. Paste it into a fresh session in the target
repository, or dispatch it through `/attune:skill-library`. It is
kept in one fenced block so it can be copied whole.

```text
You are a distinguished fellow on this project who is retiring.
Your final task: build a complete skill library under
`.claude/skills/` so that junior/mid-level engineers and smaller AI
models (Sonnet-class) can carry this project forward without you --
cheaper sessions must be able to debug, extend, validate, and
eventually advance this project at the standard I hold today. Use
multi-agent orchestration (workflows) for authoring and review;
token cost is not a constraint, correctness is.

## Phase 1 -- Discover before you write (no skill authoring yet)

Investigate the repo like an incoming principal engineer:
README/manifest/contributor docs, the build system, the test suite
and how it's actually run, CI config, docs directories, git history
(what changed, what got reverted, what stalled on dead branches),
open TODO/FIXME hotspots, issue-shaped artifacts, generated-data or
deploy conventions, and any project memory/notes available to you.
Then ask me AT MOST five questions, only for what the repo cannot
tell you -- likely: (1) what is the hardest live problem right now,
(2) what unwritten discipline rules exist (things you're not allowed
to do that no doc states), (3) who is the audience for this library
and what do they NOT know, (4) what past failures cost the most
time, (5) what does "beyond state of the art" mean for this project.
Fold my answers into everything below.

## Phase 2 -- Author the library (parallel agents, one skill per agent)

Instantiate this taxonomy, ADAPTED to what Phase 1 found -- merge
categories that are thin here, split ones that are deep, add domain
categories I haven't imagined. Aim for 10-16 skills:

CORE (every project has these):

1. <project>-change-control -- how changes are classified, gated,
   reviewed here; the project's non-negotiables with the *rationale*
   and the historical incident behind each.
2. <project>-debugging-playbook -- symptom->triage table for this
   project's failure modes; the traps that cost real time (each with
   its story); discriminating experiments.
3. <project>-failure-archaeology -- the chronicle: every major
   investigation, dead end, rejected fix, and revert, as symptom ->
   root cause -> evidence -> status, so no one re-fights a settled
   battle. Mine git history and docs hard for this.
4. <project>-architecture-contract -- the system's load-bearing
   design decisions and WHY; the invariants that must hold; the open
   known-weak points, stated plainly.
5. <domain>-reference -- the domain-theory knowledge pack a
   mid-level person lacks (the field's math/protocols/standards as
   they apply HERE, not a textbook).
6. <project>-config-and-flags -- catalog of every configuration
   axis: options, defaults, which are production vs experimental,
   guards; how to add one (checklist); with re-verification commands
   since flags drift.
7. <project>-build-and-env -- recreate the environment from
   scratch; known traps.
8. <project>-run-and-operate -- running/deploying the thing:
   command anatomy, data or artifact conventions, what output lands
   where.
9. <project>-diagnostics-and-tooling -- how to MEASURE instead of
   eyeball: the project's diagnostic tools with interpretation
   guides; ship actual scripts inside the skill's scripts/ dir where
   they exist or where you can write them.
10. <project>-validation-and-qa -- what counts as evidence here;
    acceptance-threshold discipline; the certified/golden inventory;
    how to add tests.
11. <project>-docs-and-writing -- maintaining the docs of record;
    templates; house style.
12. <project>-external-positioning -- papers/releases/ecosystem:
    what's novel vs known, what must be proven before claiming,
    reproducibility standards.

ADVANCED (the layer that makes juniors dangerous, in the good way):

13. <project>-<hardest-problem>-campaign -- an EXECUTABLE,
    decision-gated campaign for the hardest live problem from
    Phase 1: numbered phases, exact commands, EXPECTED
    observations/numbers at every gate ("if you see X instead ->
    branch to Y"), the solution menu ranked with theory/derivation
    obligations for each, known wrong paths explicitly fenced off,
    and a validation-and-promotion protocol that routes through the
    project's change control -- success must be measurable, never
    judged by eye.
14. <project>-proof-and-analysis-toolkit -- the first-principles
    analysis methods of this domain (whatever "prove it, don't just
    install it" means here), each as a recipe with a worked example
    from this repo's history.
15. <project>-research-frontier -- open problems where this project
    could advance the state of the art: for each, why current SOTA
    fails, this project's specific asset, the first three concrete
    steps IN THIS REPO, and a falsifiable "you have a result when..."
    milestone.
16. <project>-research-methodology -- the discipline that turns a
    hunch into an accepted result here: the evidence bar (one
    mechanism must explain ALL observations including negatives, and
    survive assigned adversarial refutation),
    hypothesis-predicts-numbers-before-running, the idea lifecycle
    from experiment flag to adopted change or documented retirement,
    and where good ideas historically came from.

AUTHORING RULES (bake into every agent's prompt):

- Audience: zero-context mid-level engineer or Sonnet-class model.
  Imperative runbook voice; copy-pasteable commands; every jargon
  term defined once; tables and checklists; each skill says when NOT
  to use it and which sibling to use instead.
- Format: `.claude/skills/<name>/SKILL.md`, YAML frontmatter with
  `name` and a trigger-rich `description` (exactly when a model
  should load it).
- GROUND TRUTH ONLY: verify every command, flag, path, and claim
  against the repo before stating it. Wrong runbooks are worse than
  none.
- Embed knowledge; don't reference private/user-specific paths as
  load-bearing sources.
- Date-stamp volatile facts; end each skill with a "Provenance and
  maintenance" section containing one-line re-verification commands
  for anything that may drift.
- No oversell: unproven things stay labeled open/candidate. Nothing
  may contradict the project's own manifest/rules, and no skill may
  route around its change-control.
- Write ONLY inside `.claude/skills/`; the rest of the repo is
  read-only; no mutating git commands.

## Phase 3 -- Review and fix (after ALL skills exist)

Three parallel reviewers over the complete set, then one fixer:

- FACTUAL: re-verify flags/paths/commands/citations against the
  repo; flag anything invented or stale (severity: would it send an
  engineer down a wrong path?).
- DOCTRINE: contradictions with the project's rules or between
  skills; overstated claims; missing gating on anything that changes
  behavior.
- USABILITY: trigger quality of descriptions, duplication (one home
  per fact, cross-references elsewhere), self-containedness,
  scannability.

Fixer applies blocking+important fixes. Then give me: the skill
inventory with one-line descriptions, what you verified by
spot-check, and what remains uncertain.
```

## Editorial Notes

- The prompt is preserved as dispatched, with three mechanical
  cleanups: invisible word-joiner characters removed from the
  numbered list, "contributordocs" split into two words, and a
  hyphenation typo fixed in "hypothesis-predicts-numbers".
- Session-specific directives from the original run (scope-guard
  override, branch choice) are intentionally NOT part of the
  template; record such directives in the mission state's
  `directive_overrides` instead.
