# Testing Skills With Fresh Subagents

The Iron Law in `SKILL.md` says "no skill without a failing test
first." This module covers how to run that test in a fresh
subagent so the result is uncontaminated by the conversation
that wrote the skill. For the full TDD methodology, see
`tdd-methodology.md`. For the dispatch and validation patterns
shared across skills, see `Skill(abstract:subagent-testing)`.

## Why fresh subagents matter

A skill written and tested in the same conversation has
already primed Claude with the desired behavior. Asking the
same instance to run the baseline scenario is the testing
equivalent of grading your own homework. Common contamination
modes:

| Contamination | Symptom |
|---------------|---------|
| Recency bias | Claude repeats the last pattern it saw |
| Sycophancy | Claude does what the author wanted |
| Goal inference | Claude infers the test's purpose and complies |
| Tool primed | Claude reaches for the tool the author just used |

A fresh subagent has none of this. It sees the user prompt,
the loaded skill (or its absence), and nothing else. The
result is the closest thing to a real production session.

## The TDD cycle in subagents

### RED: baseline without the skill

Dispatch a subagent in the same harness with the same model,
but with the skill disabled. The dispatch prompt should
contain only what a real user would type. No meta-commentary,
no "I am testing X," no hints.

Example dispatch fragment:

```
You are a fresh Claude Code subagent. The user has just opened
a session and typed:

  "Add a login endpoint to the API."

Respond as you normally would. Do not assume anything about
which skills are loaded.
```

Capture the full response verbatim. Note every place the
response fails the requirement the new skill is meant to
address (e.g., missing input validation, no error handling,
plain-text password).

If the subagent succeeds without the skill, the skill is not
needed. Stop. Build something that solves a real failure.

### GREEN: same dispatch with the skill loaded

Dispatch a fresh subagent with the new skill loaded. Use the
identical prompt. Compare the response.

The skill passes GREEN when:

1. Every documented baseline failure is now absent.
2. No new failures were introduced.
3. The compliance rate (failures fixed / failures observed)
   is at least 50% across three scenarios.

A 50% threshold is the floor. If the skill cannot fix half of
the documented failures, it is too vague or too narrow.
Rewrite or split.

### REFACTOR: pressure the skill

Run the skill against scenarios designed to invite
rationalization. From `anti-rationalization.md`, common
pressure shapes:

- "Quickly add..." (time pressure)
- "Just a simple..." (scope minimization)
- "Standard approach..." (ambiguity)
- "Internal tool..." (trust assumption)

Dispatch a fresh subagent with the skill loaded and the
pressure prompt. Capture rationalizations verbatim. Add
explicit counters to the skill. Re-run until rationalizations
stop appearing across three consecutive dispatches.

## Dispatch mechanics

The actual dispatch depends on your harness. In Claude Code,
the patterns below work today.

### Pattern: ad-hoc dispatch from the parent session

Use the parent agent's dispatch capability (e.g., the Task
tool in Claude Code) to start a subagent. Pass:

1. The user prompt verbatim.
2. The skill content (or its absence).
3. An instruction not to load other skills.

Example dispatch instruction:

```
You are a fresh Claude Code subagent dispatched for skill
testing. Your context contains:

- The user prompt (below).
- The SKILL.md for `<skill-name>` (loaded as a system message).
- No other skills.

Do not load additional skills. Do not search the codebase
unless the user prompt asks you to. Respond to the user
prompt directly.

User prompt:
<paste prompt>
```

### Pattern: persistent test corpus

For skills that ship with tests, store the dispatch prompts
under the skill directory:

```
plugins/<plugin>/skills/<skill>/
├── SKILL.md
├── modules/
└── tests/
    ├── baseline/
    │   ├── scenario-1.md
    │   ├── scenario-2.md
    │   └── scenario-3.md
    ├── with-skill/
    │   ├── scenario-1.md
    │   └── ...
    └── rationalization/
        └── ...
```

Each file contains the dispatch prompt, the captured response,
and a notes section listing observed failures. This makes
re-testing after a skill change a mechanical process.

### Pattern: model fixed across phases

Use the same model for RED, GREEN, and REFACTOR. A skill that
appears to fix failures because GREEN ran on a stronger model
than RED is measuring the model, not the skill. Note the
model in each test file.

## What to measure

For each baseline failure, record:

| Field | Example |
|-------|---------|
| Scenario name | "user-registration-quick" |
| Failure observed in RED | "missing input validation" |
| Status in GREEN | "fixed" / "partial" / "still failing" |
| Status in REFACTOR | "stable" / "regressed under pressure" |

A scenario that passes RED, GREEN, and REFACTOR with all
failures fixed and stable is a passing test. A scenario where
REFACTOR shows regression is a sign the skill needs more
anti-rationalization content.

## Anti-patterns

### Same-conversation testing

Asking the parent agent "did the skill work?" is not a test.
The parent has seen the skill, the test design, and the
desired answer. Always dispatch a fresh subagent.

### Single-scenario validation

A skill that passes one scenario may fail on the next. The
Iron Law calls for at least three scenarios because patterns
of failure are more reliable than single failures.

### Synthetic prompts

Inventing a prompt no real user would type produces a skill
that handles a fictional case. Pull baseline prompts from
real session transcripts where possible.

### Iterative tuning to the test

Modifying the skill until the specific test passes, without
adding new scenarios, produces a skill that overfits.
Whenever you fix a scenario, add a new variant to the test
corpus and verify the fix generalizes.

### Skipping REFACTOR

Skills that pass GREEN but skip REFACTOR collapse under real
user pressure. The pressure scenarios in REFACTOR are the
ones that matter in production. Do not ship without them.

## Verification

The deployment checklist (see `deployment-checklist.md`)
requires evidence under `tests/baseline/`, `tests/with-skill/`,
and `tests/rationalization/` before merge. The skill is not
ready until all three directories exist with at least three
scenarios each, and the scenarios were run in fresh subagents
on the same model.

To audit a skill's test coverage:

```bash
# List test scenarios
ls plugins/<plugin>/skills/<skill>/tests/*/

# Confirm scenarios exist for all three phases
for phase in baseline with-skill rationalization; do
  count=$(ls plugins/<plugin>/skills/<skill>/tests/$phase/ \
    2>/dev/null | wc -l)
  echo "$phase: $count scenarios"
done
```

Cross-reference: see `Skill(abstract:subagent-testing)` for
the dispatch contract shared across skills, and
`Skill(superpowers:dispatching-parallel-agents)` for
parallel-dispatch patterns when scenarios can run
independently.
