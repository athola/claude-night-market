---
name: feedback-collector
description: >-
  Capture section-level verdicts (approve/revise/reject)
  with optional rationale and typed annotations, write
  structured feedback to .attune/plan-history/feedback/.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 200
---

# Feedback Collector

## Purpose

Capture the user's section-by-section review verdicts
and write them as structured JSON for consumption by
the context injector and plan versioner.

## Verdict Types

| Verdict | Meaning | Requires Rationale |
|---------|---------|-------------------|
| `approve` | Section is acceptable | No |
| `revise` | Section needs changes | Yes |
| `reject` | Section is wrong approach | Yes |

## Optional Typed Annotations

When the user wants finer-grained control than
section-level verdicts, they can add typed annotations:

| Type | Purpose |
|------|---------|
| `reject` | Remove this entirely |
| `revise` | Change this, here is why |
| `question` | I do not understand this |
| `constraint` | Add this requirement |

## Feedback File Schema

Written to `.attune/plan-history/feedback/round-N.json`:

```json
{
  "round": 1,
  "plan_version": 1,
  "timestamp": "2026-04-13T14:30:00Z",
  "sections": [
    {
      "name": "architecture",
      "verdict": "revise",
      "rationale": "Split the API layer into read/write services",
      "annotations": []
    },
    {
      "name": "phase-1",
      "verdict": "approve",
      "rationale": null,
      "annotations": []
    },
    {
      "name": "phase-2",
      "verdict": "reject",
      "rationale": "Wrong approach entirely, use event sourcing",
      "annotations": [
        {
          "type": "constraint",
          "text": "Must support event replay for auditing"
        }
      ]
    }
  ],
  "overall": "revision_requested",
  "bias_findings": [],
  "war_room": null
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `round` | int | Review round number (1-3) |
| `plan_version` | int | Version of plan being reviewed |
| `timestamp` | ISO 8601 | When feedback was collected |
| `sections` | array | Per-section verdicts |
| `sections[].name` | string | Section identifier |
| `sections[].verdict` | string | approve/revise/reject |
| `sections[].rationale` | string or null | Why, if not approved |
| `sections[].annotations` | array | Optional typed annotations |
| `overall` | string | `approved` or `revision_requested` |
| `bias_findings` | array | From additive-bias-defense scan |
| `war_room` | object or null | War-room verdict (filled after deliberation) |

## Overall Verdict Logic

```
if all sections have verdict "approve":
    overall = "approved"
else:
    overall = "revision_requested"
```

## Writing the Feedback File

```bash
mkdir -p .attune/plan-history/feedback
# Write JSON to round-N.json
```

The orchestrator writes the JSON after collecting all
section verdicts in a single review pass.
