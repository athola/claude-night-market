# Interactive Review

A pull request whose author cannot explain each changed section is
not ready to merge, and passing tests do not change that. This
module turns the skill's "Don't: Merge Code You Cannot Explain"
anti-pattern into a loop you can run, and it records what you could
not explain so later probes and later gauntlet challenges aim
there.

Loaded by `/pr-review --interactive`. The rest of the review
workflow in `SKILL.md` runs unchanged around it.

## Turn Order

The reviewer speaks first in every round. The agent presents the
hunk under discussion and then waits.

This ordering is the point of the mode. An agent-first loop is a
quiz that tests recall of whatever the agent chose to ask. A
reviewer-first loop lets your own account of the change decide what
gets examined, including the parts you did not think to mention.

Each round accepts three kinds of opening:

- A statement of understanding: "this rewrites the retry to back
  off exponentially, capped at 30 seconds."
- A question of your own: "why does this need a lock at all?"
- An admission: "I do not follow this hunk."

All three are valid. An admission is the most useful of them, and
it scores no worse than a confident wrong answer.

## The Loop

For each hunk selected for probing:

1. **Present.** Show the hunk with enough surrounding code to read
   it. Name the file and line range.
2. **Listen.** The reviewer states understanding, asks a question,
   or admits the gap. Do not probe before this arrives.
3. **Answer.** Address what the reviewer raised, grounded in the
   diff. Quote the lines you rely on. If the reviewer's statement
   was wrong, say so plainly and show the line that contradicts it.
4. **Probe.** Ask one question aimed at the gap the opening
   revealed. If the opening was complete and correct, probe a
   failure mode instead: what input breaks this, what assumption it
   depends on, what happens when the call above it fails.
5. **Score.** Grade the exchange, then record it.

Stop when every hunk carrying a blocking or high-risk finding has
been probed, or when the reviewer ends the session. Probing every
hunk of a large PR is not the goal.

### Scoring

| Result | The reviewer |
|--------|--------------|
| `pass` | Explained the mechanism and named a way it fails |
| `partial` | Explained what the code does, but not how it fails |
| `fail` | Restated the diff, or could not explain it |

Grade the mechanism. A reviewer who describes the behavior
correctly in their own terms passes, whatever words they reach for.
One who quotes the function name back has not answered.

## Probe Categories

Tag every probe with one of gauntlet's seven categories. A tag
outside this list is recorded but steers nothing, because the
selector in `plugins/gauntlet/src/gauntlet/progress.py` only knows
these seven.

Two properties of that selector change how you should grade.

A category you have never been asked about outranks one you
answered badly: the untested bonus is `+1.5` and the weak bonus
tops out at `+1.0`. Coverage wins over remediation until every
category has been touched, so early sessions spread out rather than
drill the category you failed. Once all seven are tested, the steer
is clear: a failed category is selected about 18% of the time
against a 13% baseline.

The weak bonus needs accuracy strictly below `0.5`. A lone
`partial` scores exactly `0.5` and earns nothing. Grading a
genuine failure as `partial` to be kind therefore costs the
reviewer the adaptive follow-up they needed.

| Category | Probe the reviewer on |
|----------|----------------------|
| `business_logic` | What rule the change encodes, and who it affects |
| `architecture` | Why the change belongs at this layer |
| `data_flow` | Where a value comes from and where it ends up |
| `api_contract` | What callers may now rely on, and what broke |
| `pattern` | Which existing convention this follows or breaks |
| `dependency` | What this now needs, and what needs it |
| `error_handling` | Which failures propagate and which are swallowed |

Pick the category from what the hunk changed, not from which file
contains it. A new retry wrapper in a data module is
`error_handling`.

Difficulty runs 1 to 4. Read the current level before the session
and ask at that level:

```bash
python3 plugins/gauntlet/scripts/progress_tracker.py .gauntlet \
  --developer "$(git config user.email)" --format json
```

## Recording Answers

Write every graded exchange to the shared store as it happens,
rather than batching at the end. A session that crashes halfway
should keep what it learned.

```bash
python3 plugins/gauntlet/scripts/progress_tracker.py .gauntlet \
  --developer "$(git config user.email)" \
  --record '{
    "challenge_id": "pr-1234-h3",
    "knowledge_entry_id": "pr:1234:src/retry.py:88",
    "challenge_type": "explain_why",
    "category": "error_handling",
    "difficulty": 3,
    "result": "partial"
  }'
```

Field notes:

- `challenge_id`: `pr-<number>-h<hunk index>`, unique per exchange.
- `knowledge_entry_id`: `pr:<number>:<path>:<line>`. The `pr:`
  prefix marks the record as review-sourced, which keeps it
  distinguishable from a knowledge base entry without adding a
  field to the record schema.
- `challenge_type`: `explain_why` for mechanism probes, `trace` for
  data flow, `spot_bug` for failure modes, `impact_prediction` for
  blast radius.
- `result`: from the scoring table above.

The tracker stamps `answered_at` itself. Do not send it.

## Gate Policy

Probe results never block the merge recommendation.

The report gains one section when the mode ran:

```markdown
### Comprehension (4 probes)

| Hunk | Category | Result |
|------|----------|--------|
| `src/retry.py:88` | `error_handling` | partial |
| `src/pool.py:12` | `data_flow` | pass |

Weakest area over the last 20 answers: `error_handling` (42%).
```

The verdict stays whatever the code review produced. This is
deliberate. A probe that can block is a probe reviewers learn to
answer for the gate rather than for themselves, and the record it
leaves behind then measures nothing.

Report a failed probe on a hunk that also carries a blocking
finding as a note on that finding. Two independent signals pointing
at one hunk is worth saying out loud.

## Without a Knowledge Base

The mode does not require `.gauntlet/knowledge.json`. Most repos
running a PR review have never run `/gauntlet-extract`.

| Present | Behavior |
|---------|----------|
| Knowledge base and history | Categories weighted toward untested first, then weak ones, difficulty from streak |
| History only | Same weighting, categories drawn from the diff alone |
| Neither | Probe from the diff at difficulty 3, and still record every answer |

When no `.gauntlet` directory exists, create it before the first
record. The tracker creates `progress/` on write, but not its
parent.

```bash
mkdir -p .gauntlet
```

Recording without a knowledge base is worth doing on its own. The
history accumulates across reviews, and a later
`/gauntlet-extract` then finds a reviewer profile that already
knows where the gaps are.
