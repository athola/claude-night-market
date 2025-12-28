---
parent_skill: sanctum:shared
name: todowrite-patterns
description: TodoWrite naming conventions and patterns for sanctum skills
category: patterns
tags: [todowrite, naming, conventions]
estimated_tokens: 150
---

# TodoWrite Patterns for Sanctum

## Naming Convention
All sanctum skills follow a consistent pattern for TodoWrite items:
```
<skill-name>:<step-name>
```

The skill name matches the frontmatter `name` field, and the step name describes the specific workflow phase.

## Examples from Sanctum Skills

### git-workspace-review
```
git-review:repo-confirmed
git-review:status-overview
git-review:diff-stat
git-review:diff-details
```

### commit-messages
Commit messages skill does not use TodoWrite as it's a single-step artifact generation workflow.

### pr-prep
```
pr-prep:workspace-reviewed
pr-prep:quality-gates
pr-prep:changes-summarized
pr-prep:testing-documented
pr-prep:pr-drafted
```

### doc-updates
```
doc-updates:context-collected
doc-updates:targets-identified
doc-updates:consolidation-checked
doc-updates:edits-applied
doc-updates:guidelines-verified
doc-updates:accuracy-verified
doc-updates:preview
```

### version-updates
```
version-update:context-collected
version-update:target-files
version-update:version-set
version-update:docs-updated
version-update:verification
```

## Best Practices

### Step Naming
- Use present tense verbs (collected, identified, applied, verified)
- Keep names concise (2-3 words max)
- Make the outcome clear from the name
- Order steps sequentially in the workflow

### When to Skip TodoWrite
- Single-step workflows (like commit-messages)
- Quick utilities that complete in one operation
- Read-only analysis with no discrete phases

### Integration
- Create all TodoWrite items at workflow start
- Mark items complete immediately after finishing each step
- Use TodoWrite as workflow documentation for users
