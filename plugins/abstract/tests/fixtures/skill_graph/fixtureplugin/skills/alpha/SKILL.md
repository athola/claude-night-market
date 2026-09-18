---
name: alpha
description: Planted skill-graph control. Calls beta and one skill that does not exist.
---

# Alpha

Delegates to `Skill(fixtureplugin:beta)` and, on purpose, to
`Skill(fixtureplugin:absent)`, which no directory provides. The audit
must classify the second as a bug before its report on `plugins/` is
reportable.

## Exit Criteria

- [ ] `tests/scripts/test_skill_graph.py -k Planted` reports the
      fixture tree's known answer: one bug-class dangling reference,
      one isolate, two edges
