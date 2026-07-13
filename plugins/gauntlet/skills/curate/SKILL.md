---
name: curate
description: Adds developer-authored annotations to the gauntlet knowledge base. Use when capturing tribal knowledge or rationale not visible in code.
model_hint: standard
---

# Curate Knowledge

Add developer-authored annotations to the knowledge base.

## When NOT To Use

- Knowledge derivable from the code itself (use `gauntlet:extract`)
- The DSA problem bank (use `gauntlet:gauntlet-curate`)

## Steps

1. Identify the module to annotate
2. Ask for the concept (key insight or rule)
3. Ask for the why (rationale, history, context)
4. Generate YAML annotation file
5. Save to `.gauntlet/annotations/<slug>.yaml`
6. Confirm saved and will be included in future challenges

## Exit Criteria

- [ ] A YAML file exists at `.gauntlet/annotations/<slug>.yaml`
  after the skill completes, where `<slug>` is derived from the
  annotated module and concept
- [ ] The YAML file contains at minimum a `concept` field (key
  insight or rule) and a `why` field (rationale/history/context)
- [ ] Confirmation message states the annotation will be included
  in future challenges, indicating it is on the discovery path
  for `gauntlet:extract`
- [ ] Annotation does not duplicate an existing entry under the
  same slug (checked before saving)
