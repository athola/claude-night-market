---
name: challenge
description: Presents adaptive codebase challenge questions with multiple-choice and trace exercises. Use when testing contributor knowledge of the codebase.
---

# Run Gauntlet Challenge

Present challenges from the knowledge base and evaluate answers.

## When NOT To Use

- The knowledge base does not exist yet (use `gauntlet:extract`)
- A staged path for a new contributor (use `gauntlet:onboard`)

## Challenge Sources

`scripts/challenge_engine.py` draws from one of three sources:

- `--source knowledge` (default): an entry from
  `.gauntlet/knowledge.json`, weighted by the developer's progress
- `--source bank`: a problem from the shipped problem bank, narrowed
  with `--category` and `--difficulty`, and varied so its answer
  cannot be memorised
- `--source graph`: an impact or dependency question about a real
  call edge in `.gauntlet/graph.db`

The bank variation goes through the in-loop provider inside Claude
Code and the Anthropic API outside it (issue #464). The script calls
`register_in_loop_provider_if_inside_claude_code()` in its own process,
so no setup step is needed.

## Steps

1. **Load state**: read `.gauntlet/knowledge.json` and developer
   progress

2. **Check for pending challenge**: if
   `.gauntlet/state/pending_challenge.json` exists, evaluate the
   developer's most recent message as an answer before generating
   a new one

3. **Generate challenge**: run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/challenge_engine.py .gauntlet`
   with the source that fits: the default for codebase knowledge, a
   `--source bank --category <name>` for practice problems, or
   `--source graph` once a graph has been built

4. **Present challenge**: show the question with context

5. **Evaluate answer**: score the response (pass/partial/fail)

6. **Record result**: update developer progress and streak

7. **On pass**: when the challenge came from the pre-commit gate,
   score it with the command below, which writes the one-time token
   that releases the commit of the staged files. Under `--gate` the
   script scores `.gauntlet/state/pending_challenge.json` and ignores
   the file argument. Show next challenge if in session.

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/answer_evaluator.py \
     .gauntlet/state/pending_challenge.json "<answer>" --gate
   ```

8. **On fail**: show correct answer with explanation. Present a
   new challenge.

## Scoring

| Result | Score | Streak |
|--------|-------|--------|
| Pass | 1.0 | +1 |
| Partial | 0.5 | reset |
| Fail | 0.0 | reset |

## Exit Criteria

- [ ] `.gauntlet/knowledge.json` exists and is readable before a
  challenge is generated; if missing, the skill surfaces the error
  and suggests running `gauntlet:extract`
- [ ] Each challenge attempt results in a score (1.0/0.5/0.0) written
  to the developer's progress store and a streak update applied
- [ ] `.gauntlet/state/pending_challenge.json` is evaluated before
  generating a new challenge when it exists; the file is removed
  or updated after evaluation
- [ ] A `--source bank` or `--source graph` request yields a challenge
  from that source, or the script's error naming what is missing
- [ ] On fail, the correct answer and explanation are shown before
  the next challenge is presented (not skipped silently)
- [ ] On a pass from the pre-commit gate,
  `.gauntlet/state/pass_token.json` exists and names the staged set,
  so the retried commit is released
