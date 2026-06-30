# forced-eval activation hook (prototype)

A UserPromptSubmit hook that makes the model explicitly evaluate
installed skills before acting. It targets the activation-reliability
problem: the skill activation layer does near-keyword matching, so
relevant skills sometimes fail to fire. The research (Scott Spence;
umputun) reports that a forced evaluation pass lifts activation
materially.

## Status

PROTOTYPE. Not wired into any `plugin.json` and not installed
globally. The core logic is unit-tested (6 tests, all green). The
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

`measure_activation.py` implements the Scott Spence methodology against
a labelled prompt set (`activation_cases.json`):

1. Baseline: run each prompt through `claude -p --output-format
   stream-json --max-turns 1 --allowedTools Skill` with the hook off and
   count how often the expected `Skill()` event fires.
2. Treatment: repeat with the forced-eval hook wired via a temp
   `--settings` file.
3. Compare the activation rate (positives) and false-activation rate
   (true-negatives, so a high positive rate is not vanity). The paired
   McNemar test reports whether the lift is significant.

Run it:

    # Dry run: prints the planned commands and token cost, spends nothing
    uv run python measure_activation.py

    # Live run: invokes claude per case x 2 conditions (spends tokens).
    # Point --root at the plugin tree whose skills you want listed.
    uv run python measure_activation.py --live \
        --root "$PWD/../../plugins/superpowers" --repeats 3

Results (JSON + a markdown report) land under `results/`. The dataset is
deliberately small; expand `activation_cases.json` before trusting the
rates. The pure scoring/parsing logic is unit-tested in
`test_measure_activation.py` (14 tests).

Caveat the harness cannot fix: `forced_eval.py` lists skill *names*
under one `--root` tree. A real comparison against the full ~198-skill
ecosystem needs the production hook to scope names to plausibly-relevant
skills first (see Caveats), or the treatment condition just floods
context with one plugin's names.

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
- Background: `docs/quality-gates.md` ("Dogfooding Harness Lessons")
