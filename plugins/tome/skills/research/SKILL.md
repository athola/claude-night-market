---
name: research
description: Runs multi-source research across GitHub, HN, Reddit, arXiv, and Semantic Scholar. Use when surveying a technical topic across multiple channels.
alwaysApply: false
category: orchestration
tags:
  - research
  - synthesis
  - multi-source
tools: []
estimated_tokens: 600
progressive_loading: true
orchestrates:
  - tome:code-search
  - tome:discourse
  - tome:papers
  - tome:triz
  - tome:synthesize
model_hint: standard
---
# Research Session Orchestrator

Run a full multi-source research session: classify the
domain, dispatch parallel agents, synthesize findings,
and output a formatted report.

## When NOT To Use

- Drilling into one subtopic of an active session (use `tome:dig`)
- Merging findings already gathered (use `tome:synthesize`)

## Workflow

### Step 1: Classify Domain

Run the domain classifier on the topic:

```python
from tome.scripts.domain_classifier import classify
result = classify(topic)
# result.domain, result.triz_depth, result.channel_weights
```

If confidence < 0.6, ask the user to confirm or override
the domain classification before proceeding.

### Step 2: Plan Research

```python
from tome.scripts.research_planner import plan
research_plan = plan(result)
# research_plan.channels, research_plan.weights, research_plan.triz_depth
```

### Step 3: Create Session

```python
from tome.session import SessionManager
mgr = SessionManager(Path.cwd())
session = mgr.create(topic, result.domain, result.triz_depth, research_plan.channels)
```

### Step 4: Dispatch Agents

Launch research agents in parallel using the Agent tool.
Use this mapping:

| Channel | Agent Type | Prompt Includes |
|---------|-----------|-----------------|
| code | `tome:code-searcher` | topic |
| discourse | `tome:discourse-scanner` | topic, domain, subreddits |
| academic | `tome:literature-reviewer` | topic, domain |
| triz | `tome:triz-analyst` | topic, domain, triz_depth |

**Rules:**
- Always dispatch code and discourse agents
- Dispatch academic agent only if "academic" is in
  research_plan.channels
- Dispatch triz agent only if "triz" is in
  research_plan.channels AND triz_depth != "light"
- Dispatch all eligible agents in a SINGLE message
  (parallel, not sequential)

Each agent prompt must include:
1. The topic string
2. The domain classification
3. Any channel-specific context (subreddits for discourse,
   triz_depth for triz)
4. Instruction to return findings as JSON

### Step 5: Collect and Synthesize

After all agents return:

1. Parse each agent's findings into Finding objects
2. Record what each agent actually searched, before
   merging anything:

   ```python
   from tome.synthesis.quality import parse_envelope

   for envelope in agent_envelopes:      # one per dispatched agent
       session.query_log.extend(parse_envelope(envelope))
   ```

   This is the step that makes an empty channel readable.
   Findings record what was found; the query log records
   what was looked for, and without it a channel that
   errored and a channel that searched a thin topic are
   the same thing: no findings. Skip this and every
   channel in the report reads `unknown`.

3. Merge using `tome.synthesis.merger.merge_findings()`
4. Rank using `tome.synthesis.ranker.rank_findings()`

### Step 6: Generate Output

```python
from tome.output.report import format_report, format_brief, format_transcript

# Default to report format
output = format_report(session)

# Save to docs/research/
output_path = f"docs/research/{session.id}-{slug}.md"
```

Save the session state:
```python
mgr.save(session)
```

### Step 7: Present Results

Display a brief summary to the user:
- The frontier verdict and its reason, from
  `tome.synthesis.frontier.frontier_verdict(session)`. It is
  the report's own answer to "did we find little because
  there is little, or because the search went badly"
- Number of findings per channel, with its outcome status
  from `tome.synthesis.quality.channel_outcomes(session)`:
  `ok`, `empty`, `error`, `rate_limited`, `degraded`, or
  `unknown`
- Top 3 findings by relevance
- Path to saved report
- Any research stories from
  `tome.synthesis.frontier.frontier_stories(session)`. Each
  is a gap with its evidence, and each arrives `undecided`.
  Ask the user to mark it `act`, `defer`, or `decline`.
  Do not decide for them and do not file an issue for a
  story they have not marked `act`: nothing in a search
  record says what is worth this project's time. On `defer`,
  file it with `minister:create-issue`.

The three retrieval channels run a positive control before
their topic queries, so `INCONCLUSIVE` now means something
specific rather than "controls do not exist yet". Read it as
one of two things: a channel failed its canary and is blind,
or a channel searched without running one. Both are named in
the verdict's evidence, and both produce a story under
`Research Stories`.

`triz` runs no control and is excluded from the verdict. It
generates analogies rather than retrieving prior work, so
its output is not evidence about what has been published and
its findings are not counted toward coverage.

State plainly which channels did not return cleanly. A
summary that reports "3 findings" without saying two
channels were rate-limited invites the reader to treat a
half-run search as a finding about the topic.

Then offer interactive refinement:
"Use `/tome:dig \"subtopic\"` to explore specific areas."

## Error Handling

- If an agent fails, continue with remaining agents
- If all agents fail, report the error and suggest
  manual research approaches
- If synthesis produces 0 findings, state this clearly
  rather than generating an empty report
- Save session state even on partial failure

## Output Format Selection

| Flag | Format | Function |
|------|--------|----------|
| (default) | report | `format_report()` |
| `--format brief` | brief | `format_brief()` |
| `--format transcript` | transcript | `format_transcript()` |

## Exit Criteria

- [ ] Domain classified before agents are dispatched; if confidence
      < 0.6, user confirmation is requested before proceeding
- [ ] Code and discourse agents always dispatched; academic and triz
      agents dispatched only when their channels are in the plan;
      all eligible agents sent in a single parallel message
- [ ] Session saved to `docs/research/{session.id}-{slug}.md` after
      synthesis regardless of whether all agents succeeded
- [ ] Top 3 findings by relevance score displayed to the user with
      the path to the saved report
- [ ] If all agents fail, error reported and manual alternatives
      suggested; an empty report is never generated
