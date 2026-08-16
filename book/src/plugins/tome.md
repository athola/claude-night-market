# tome

Multi-source research plugin for code archaeology,
community discourse, academic literature, and TRIZ
cross-domain analysis.

## Overview

Tome orchestrates research across four channels:
GitHub code search, community discourse (HN, Lobsters,
Reddit), academic literature (arXiv, Semantic Scholar),
and TRIZ analogical reasoning. It classifies domains
and adapts search depth automatically.

## Frontier detection

A research report ends with a verdict describing the search
itself. Few findings can mean a thin field or a search that
went wrong, and those two cases call for opposite responses.
To tell them apart, each channel runs a positive control: a
query whose answer is known to be in that channel's index.
A channel that cannot retrieve a document it should find is
blind, and its silence carries no information about the
field.

Rules are evaluated in order, and the first match wins:

| Verdict | Meaning |
|---------|---------|
| `INCONCLUSIVE` | A channel errored, was rate-limited, or failed its control. The run is not evidence. |
| `THIN_FIELD_CANDIDATE` | Two or more channels searched cleanly and still returned few findings. |
| `CHANNEL_MISMATCH_SUSPECTED` | One channel holds most findings while a control-passing channel came back empty, which points to a vocabulary mismatch more often than to a thin field. |
| `COVERED` | The channels searched cleanly and returned enough findings that no sparsity question arises. |

Only channels answering from an external index take part in
the verdict. `RETRIEVAL_CHANNELS` in `tome/models.py` names
them: `academic`, `code`, and `discourse`. The `triz`
channel writes analogies rather than retrieving records, and
its exclusion holds in two directions. Counting its output
would let a session clear the sparsity threshold with text
it wrote itself. Demanding a control from a channel that has
no index would pin every session carrying `triz` to
`INCONCLUSIVE` for a reason that says nothing about
coverage.

A null result is reported with the floor it was measured
against. For the rationale and the limits of the mechanism,
see
[ADR-0020](../../../docs/adr/0020-tome-frontier-detection-via-positive-controls.md).

## Installation

```bash
/plugin install tome@claude-night-market
```

## Commands

| Command | Description |
|---------|-------------|
| `/tome:research` | Run multi-source research session |
| `/tome:dig` | Refine results interactively |
| `/tome:cite` | Generate formatted bibliography |
| `/tome:export` | Export findings for knowledge-intake |

## Skills

- `research`: orchestrate a full research session
- `code-search`: search GitHub implementations
- `discourse`: scan community discussions
- `papers`: search academic literature
- `triz`: cross-domain analogical reasoning
- `ideate`: diverse ideation methods with rotation
- `synthesize`: merge and rank findings
- `dig`: interactive refinement

## Agents

- `code-searcher`: GitHub code search
- `discourse-scanner`: community discussion scanning
- `literature-reviewer`: academic paper review
- `research`: multi-source research orchestrator (delegates to `Skill(tome:research)`)
- `triz-analyst`: cross-domain analysis
