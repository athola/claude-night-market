# Evidence: what the STE-for-LLMs numbers measured

For a practitioner about to cite a number. The public evidence that STE
helps an LLM measures one thing: the model obeys STE rules in its own
output. Nothing found measures task accuracy, reasoning, or
hallucination. Traced with tome on 2026-10-08.

## The 72.9% figure

A circulating summary says STE with LLMs "reduces rule violations by up
to 72.9%". The figure comes from an aiweekly alert dated 2026-07-31,
which reports the SimpleEnglish skill's own benchmark: 6 Claude models,
8 writing tasks, 96 generations. A regex linter counted STE-rule hits
per 100 words, with and without the skill. The four per-model figures
reported ran from 41% to 82%. The 72.9% is the aggregate.

The project README no longer carries 72.9%. It reports 81.3% fewer
linter violations over 144 generations and 9 models. Its 2026-09-02
audit says these numbers "measure rule obedience, not what a reader
sees". Version 2.0.1 reports a reader-side count instead: 218 visible
defects down to 11 across 16 chat replies. That is closer to what a
reader sees, and it is still the project counting its own output. Claude
models judged Claude text, and no independent replication was found.

Cite it as rule obedience. Never cite it as fewer errors.

## What has no source

No study was found that writes the prompt in controlled language and
measures task accuracy. The closest evidence points the other way.
arXiv 2603.13351 found that style directives added to a working prompt
took one reasoning task from 100% to 0% and 30%. arXiv 2601.22047 found
that a constraint the model already satisfied still cost accuracy.
Neither tests STE, and both are narrow. They show a register directive
cannot be assumed free.

"STE removes hallucinations" is unsourced. The nearest result is a 2025
Gothenburg thesis in which experts judged a fine-tuned Mistral-7B to
hallucinate less, with no count reported.

One informal test (Ghinda, 2026-08-14) found Claude lost 22 of 47 code
facts (47%) under formal ASD-STE100, against a no-style control. A
looser "Simple Technical English" instruction lost 4 of 47 (9%). Codex
lost about 40% under both. One author, no protocol, but it is the only
accuracy measurement found.

## What this repository does with it

The adopted limits are enforced on text a reader executes, by counting.
The shipped workflow scripts carry no "write in ASD-STE100" line in
their agent prompts. Their prompt and operator strings are held to the
limits by `tests/test_workflow_prompts_ste.py`. That moves the cost to
the author, who writes the short sentence once, and away from the
subagent, which would otherwise carry one more directive on every call.

The one-line invocation in the hub stays where the evidence supports
it: replies to the operator, where readability is the goal.

## Sources

| Source | Kind |
|--------|------|
| [aiweekly alert](https://aiweekly.co/alerts/simpleenglish-agent-skill-cuts-claude-ste-violations-729) | Secondary report of the 72.9% run |
| [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish) | Project README and audit, MIT |
| [arXiv 2603.13351](https://arxiv.org/abs/2603.13351) | Prompt complexity and reasoning |
| [arXiv 2601.22047](https://arxiv.org/abs/2601.22047) | Constraint interference |
| [Ghinda, 2026-08-14](https://allaboutcoding.ghinda.com/explain-to-me-in-simple-technical-english/) | Informal code-fact test |
| [Nieminen, 2025](https://gupea.ub.gu.se/items/18568d0f-52af-43ed-8915-abd0d9bf7afe/full) | Thesis, fine-tuned Mistral-7B |
