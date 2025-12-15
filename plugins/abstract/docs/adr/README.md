# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Abstract plugin infrastructure.

## What is an ADR?

An ADR documents a significant architectural decision along with its context and consequences. ADRs serve two purposes:

1. **Knowledge preservation**: Future contributors can understand *why* things are built this way
2. **Communication**: Stakeholders stay informed about architectural evolution

## When to Write an ADR

Write an ADR for (medium scope):

- Breaking changes to skills or APIs
- New skill additions
- Significant refactors (>3 files, architectural changes)
- New external dependencies
- Changes to plugin loading/isolation mechanisms

You do NOT need an ADR for:

- Bug fixes
- Documentation updates
- Minor improvements
- Routine maintenance

## How to Create an ADR

1. Copy `template.md` to `NNNN-YYYY-MM-DD-title.md`
2. Use the next sequential number (check existing ADRs)
3. Fill out all sections
4. Complete the Architecture Review Checklist
5. Submit with your PR or commit

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](./0001-2025-12-04-architecture-governance-process.md) | Architecture Governance Process | Accepted | 2025-12-04 |

## Status Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded by ADR-XXXX]
```

- **Proposed**: Under discussion
- **Accepted**: Decision is final
- **Deprecated**: No longer applies (context changed)
- **Superseded**: Replaced by a newer ADR
