---
name: research
description: 'Run a multi-source research session searching GitHub, HN, Lobsters, Reddit, arXiv, and Semantic Scholar. Use for multi-channel topic surveys.'
usage: >-
  /tome:research "<topic>" [--format report|brief|transcript]
  [--resume] [--list] [--domain <override>]
---

# Research Command

Start an autonomous multi-source research session.

## Usage

```bash
# Full research session
/tome:research "async python patterns"

# Choose output format
/tome:research "cache eviction policies" --format brief

# Resume most recent session
/tome:research --resume

# List saved sessions
/tome:research --list

# Override domain classification
/tome:research "raft consensus" --domain architecture
```

## What Happens

1. Topic is classified into a domain (algorithm, ui-ux,
   architecture, etc.)
2. Research channels are selected based on domain
3. Parallel agents search each channel autonomously
4. Findings are merged, deduplicated, and ranked
5. A formatted report is generated and saved
6. You can refine results with `/tome:dig`

## Execution

Invoke the research skill:

```
Skill(tome:research)
```

Pass the topic, format flag, and any overrides.

## Output

Reports are saved to `docs/research/{session}-{topic}.md`.

## See Also

- `/tome:dig` -- refine results interactively
- `/tome:cite` -- generate bibliography
- `/tome:export` -- export to memory-palace format
