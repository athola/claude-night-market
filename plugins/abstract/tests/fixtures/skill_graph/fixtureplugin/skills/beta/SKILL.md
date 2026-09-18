---
name: beta
description: Planted skill-graph control. Called by alpha, calls nothing.
---

# Beta

Reached from alpha. The live edge the audit must count.

## Exit Criteria

- [ ] `tests/scripts/test_skill_graph.py -k Planted` reports the
      fixture tree's known answer: one bug-class dangling reference,
      one isolate, two edges
