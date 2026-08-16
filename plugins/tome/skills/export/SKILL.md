---
name: export
description: Export a research session into knowledge-intake compatible markdown. Use after a research session to hand findings to memory-palace.
alwaysApply: false
category: output
tags:
- export
- research
- knowledge-transfer
- memory-palace
dependencies:
- tome:research
- tome:synthesize
scripts: []
usage_patterns:
- research-handoff
- corpus-ingestion
complexity: simple
model_hint: standard
estimated_tokens: 400
---

# Export

Turn a finished research session into a file `knowledge-intake` can read
without reformatting.

## When To Use

After a research session has findings and you want them stored rather
than merely reported.

## When NOT To Use

- The session is still gathering findings: finish `Skill(tome:research)`
  first, since an export of an empty session emits only frontmatter.
- You want a human-readable report: use `Skill(tome:synthesize)`, which
  produces the narrative form with coverage and gaps.

## Workflow

Load the session and render it:

```python
from pathlib import Path

from tome.session import SessionManager
from tome.output.export import export_for_memory_palace

session = SessionManager(Path.cwd()).load_latest()
markdown = export_for_memory_palace(session)
Path(f"docs/research/export-{session.id}.md").write_text(markdown)
```

`SessionManager` resolves its store relative to the path it is given, so
run this from the repository root or the session will not be found.

To export a specific session, use `load(session_id)` instead of
`load_latest()`.

## What It Emits

YAML frontmatter carrying `topic`, `domain`, `session_id`, `date`,
`finding_count`, `channels`, and `type: research-export`, followed by
findings grouped by channel. Each finding renders its source, URL,
relevance, summary, and channel-specific metadata.

An empty session emits the frontmatter and a line stating that no
findings were recorded, which is deliberate. A silent empty file would
read as a successful export of nothing.

## Handoff

The output is an external resource, not a corpus entry. Feed it to
`Skill(memory-palace:knowledge-intake)`, which owns evaluation, routing,
and storage. This skill does no scoring.

## Exit Criteria

- [ ] `export_for_memory_palace` was called on a loaded session
- [ ] The output file exists and its frontmatter includes
      `type: research-export`
- [ ] `finding_count` in the frontmatter matches the session's findings
- [ ] The file was handed to `Skill(memory-palace:knowledge-intake)` or
      its path was reported for later intake
