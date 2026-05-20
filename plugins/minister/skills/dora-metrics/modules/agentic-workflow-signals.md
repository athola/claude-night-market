# Agentic Workflow Signals from DORA

DORA metrics were designed for human-driven engineering teams, but
the same four numbers expose specific failure modes in
AI-assisted pipelines.

## What to Watch

### Change Failure Rate, AI vs human

Run the metric twice with different `--failure-label` values:

```bash
python3 -m minister.dora_metrics --window 30 --failure-label bug --json > all.json
python3 -m minister.dora_metrics --window 30 --failure-label ai-bug --json > ai.json
```

If AI-authored CFR exceeds human-authored CFR by more than five
percentage points, treat it as a signal that review is too lenient
on AI output, not that AI is unsafe in general. The right response
is usually adding a hookify rule or imbue gate at the friction
point, not banning AI assistance.

### Lead Time, before vs after agent adoption

Compute lead time for the 30 days before and after enabling an
agentic workflow. If LT improved but CFR or TRS regressed, the team
is trading stability for velocity. The bottleneck dimension surfaced
by the skill points at which trade was made.

### Time to Restore, agent-driven hotfixes

If TRS got worse after agents started shipping hotfixes, suspect
incomplete root-cause analysis. The Replit incident is a case study:
fast restore claims that turn out to be fabricated extend TRS once
the truth surfaces.

### Deployment Frequency, ceiling check

Agents can push DF arbitrarily high. Pair DF with CFR; if DF rose
and CFR rose proportionally, the agent is generating noise rather
than signal. A high-DF, high-CFR team produces churn.

## Producing a Comparison Report

Combine two windows side-by-side:

```python
from minister.dora_metrics import compute_metrics
# ... collect events for each cohort ...
human = compute_metrics(human_deploys, human_failures, window_days=30)
agent = compute_metrics(agent_deploys, agent_failures, window_days=30)
print("Human:", human.tier())
print("Agent:", agent.tier())
print("Human bottleneck:", human.bottleneck())
print("Agent bottleneck:", agent.bottleneck())
```

If the bottleneck differs across cohorts, that is the most
useful single output: it tells the engineering manager which
guardrail is missing for which population.

## Anti-Patterns

- Reporting only DF as proof of agent ROI without CFR.
- Excluding agent-authored failures from the failure label.
- Comparing against last quarter when agent adoption mid-window
  invalidates the comparison.
