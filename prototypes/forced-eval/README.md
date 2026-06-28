# forced-eval activation hook (prototype)

A UserPromptSubmit hook that makes the model explicitly evaluate
installed skills before acting. It targets the activation-reliability
problem: the skill activation layer does near-keyword matching, so
relevant skills sometimes fail to fire. The research (Scott Spence;
umputun) reports that a forced evaluation pass lifts activation
materially.

## Status

PROTOTYPE. Not wired into any `plugin.json` and not installed
globally. The core logic is unit-tested (4 tests, all green). The
live activation lift is not measured here. Measuring it requires the
sandboxed-eval methodology below.

## How it works

On each UserPromptSubmit event the hook:

1. Reads the event JSON from stdin.
2. Discovers skill names under `FORCED_EVAL_ROOT` (or its own dir).
3. Emits the UserPromptSubmit additionalContext contract:

       {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
        "additionalContext": "Before responding, evaluate ..."}}

This contract mirrors `plugins/egregore/hooks/user_prompt_hook.py`.

## Try it

    # Run the tests
    uv run python -m pytest prototypes/forced-eval/test_forced_eval.py

    # Smoke test against a real plugin tree
    printf '{"prompt":"x"}' | FORCED_EVAL_ROOT=$PWD/plugins/imbue \
        uv run python prototypes/forced-eval/forced_eval.py

## Install (optional, opt-in)

Add a UserPromptSubmit hook in `settings.json` pointing at this
script, with `FORCED_EVAL_ROOT` set to the plugin tree you want
evaluated. Measure the context cost before enabling globally (see
Caveats).

## Measuring activation lift

Measure the activation lift the way the research does (Scott Spence):

1. Baseline: run prompts that should trigger a skill through
   `claude -p --output-format stream-json --max-turns 1
   --allowedTools Skill` and count how often a `Skill()` event fires.
2. Treatment: repeat with the hook enabled.
3. Compare the activation rate. Include true-negative prompts
   (queries that should not trigger a skill) so a 100% rate is not
   vanity.

## Caveats

- Context cost. Listing every skill every turn bloats context and can
  push past the skill Discovery budget of about 16,000 characters,
  after which skills are silently dropped. A production version should
  scope the reminder to skills plausibly relevant to the prompt, not
  all of them. This prototype lists all, for simplicity.
- Forced evaluation adds latency to every turn. Weigh it against the
  activation win.

## Sources

- Scott Spence, How to make Claude Code skills activate reliably
  https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably
- Scott Spence, Measuring skill activation with sandboxed evals
  https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals
- shimo4228, skill sprawl and the Discovery character budget
  https://dev.to/shimo4228/15-days-of-skill-sprawl-in-claude-code-lessons-from-3-audits-27em
- Background: `reports/dogfooding-feature-review-2026-06-28.md`
