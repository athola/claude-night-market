# ADR-0001: Architecture Governance Process

**Status**: Accepted
**Date**: 2025-12-04
**Author**: @athola

## Context

Abstract is evolving into a foundational plugin that other plugins in the claude-night-market ecosystem will compose from. As the ecosystem grows, we need:

1. A way to document architectural decisions so future contributors understand *why* things are built this way
2. Communication mechanisms to keep stakeholders informed about architectural evolution
3. Patterns for how plugins compose with abstract and each other
4. Conflict detection and version compatibility strategies

Without formal governance, architectural knowledge lives only in commit history and tribal knowledge, making it difficult for new contributors to understand design rationale.

## Decision

Establish a lightweight architecture governance framework consisting of:

1. **ADR Process**: Architecture Decision Records in `docs/adr/` for significant decisions
2. **Two-tier Review**: Automated pre-commit checks + manual ADR-linked checklists
3. **Evolution Patterns**: Documented patterns for how the architecture grows
4. **Composition Model**: Plugins compose from abstract components rather than inherit
5. **Version Compatibility**: SemVer contract with explicit version constraints

### ADR Scope (Medium)

Write an ADR for:
- Breaking changes to skills or APIs
- New skill additions
- Significant refactors (>3 files, architectural changes)
- New external dependencies
- Changes to plugin loading/isolation mechanisms

### Review Tiers

**Tier 1 (Pre-commit)**: Automated checks for new dependencies, skill files, module changes

**Tier 2 (ADR-linked)**: Manual checklist covering single responsibility, dependency direction, token impact, plugin isolation, backward compatibility, testability

## Consequences

**Benefits**:
- Architectural decisions are discoverable and searchable
- New contributors can understand design rationale
- Prevents re-litigating settled decisions
- Creates accountability for significant changes

**Trade-offs**:
- Additional overhead for medium-scope changes
- Requires discipline to maintain ADR currency
- May slow down rapid prototyping phases

**Mitigations**:
- Keep ADR template minimal
- Only require ADRs for medium-scope changes (not every commit)
- ADRs can be written retroactively if needed

## Alternatives Considered

### 1. No formal governance
**Rejected**: As ecosystem grows, lack of documentation leads to inconsistent decisions and repeated debates.

### 2. Heavy change control (approval gates)
**Rejected**: Overkill for current team size. Adds friction without proportional benefit.

### 3. PR-based review only
**Rejected**: Pre-commit catches issues earlier. Combining with ADR-linked review gives two appropriate checkpoints.

## Related ADRs

None - this is the foundational ADR.

## Architecture Review Checklist

- [x] Single responsibility: Establishes governance framework only
- [x] Dependency direction: N/A (process, not code)
- [x] Token impact: N/A (documentation)
- [x] Plugin isolation: Defines isolation mechanisms for ecosystem
- [x] Backward compatibility: N/A (new process)
- [x] Testability: Process can be validated through PR reviews
