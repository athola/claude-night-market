---
name: dig
description: >-
  Interactively refine research results by searching
  deeper into a specific subtopic or channel. Requires
  an active research session from /tome:research.
usage: >-
  /tome:dig "<subtopic>" [--channel code|discourse|academic|triz]
---

# Dig Command

Refine an active research session by searching deeper.

## Usage

```bash
# Dig deeper into a subtopic
/tome:dig "event loop implementation details"

# Search only a specific channel
/tome:dig "tokio runtime" --channel code

# Dig into academic literature specifically
/tome:dig "formal verification of consensus" --channel academic
```

## What Happens

1. Loads the most recent active research session
2. Runs targeted searches on the subtopic using selected
   channels (or all channels from the original session)
3. Merges new findings into the existing session
4. Updates the saved report

## Execution

Invoke the dig skill:

```
Skill(tome:dig)
```

## Error Cases

- No active session: directs user to start one with
  `/tome:research`
- Channel not in original session: warns and suggests
  available channels
