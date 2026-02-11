---
name: evidence-formats
description: Standardized formats for evidence capture and citation
parent_skill: imbue:shared
category: infrastructure
estimated_tokens: 200
reusable_by: [all imbue skills, pensive skills, sanctum skills]
---

# Evidence Formats

## Evidence Reference Format

### Command Evidence

```
[E1] Command: git diff --stat HEAD~5..HEAD
     Output: 15 files changed, 234 insertions(+), 89 deletions(-)
     Timestamp: 2024-01-15T10:30:00Z
```

### Citation Format

```
[C1] Source: https://doc.rust-lang.org/nomicon/
     Section: "Working with Unsafe"
     Relevance: Validates unsafe block justification
```

### Artifact Index

```
[A1] Type: Coverage Report
     Path: ./coverage/index.html
     Generated: 2024-01-15T10:35:00Z
     Retention: Ephemeral (session only)
```

## Reference Linking in Findings

```
Finding: Memory leak in connection pool [E3, C2]
- Evidence [E3]: valgrind output showing 4KB unreleased
- Citation [C2]: PostgreSQL docs on connection lifecycle
```

## Best Practices

1. **Sequential numbering**: E1, E2, E3... C1, C2...
2. **Include timestamps**: ISO 8601 format
3. **Capture relevant snippets**: Not entire outputs
4. **Note working directory**: When context matters
5. **Retention policy**: Mark ephemeral vs archived
