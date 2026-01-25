# Evaluation and Validation Skills Inventory

This document catalogs all evaluation, validation, and review-related skills in the claude-night-market ecosystem. These skills have **metacognitive properties** (they evaluate other things) and should themselves be tested with the same rigorous standards to prevent cargo cult patterns.

## Criteria for Inclusion

Skills are included if they:
- Evaluate, validate, audit, or review artifacts
- Define quality standards or thresholds
- Provide scoring or assessment frameworks
- Enforce compliance with standards
- Have metacognitive properties (evaluate the evaluation process)

## Priority Classification

- **HIGH**: Core infrastructure skills that other skills depend on
- **MEDIUM**: Domain-specific evaluation skills
- **LOW**: Specialized or less frequently used evaluation skills

---

## ✅ COMPLETED - With Comprehensive Tests

### Abstract Plugin (Infrastructure Evaluation)

| Skill | Tests | Coverage | Priority | Status |
|-------|-------|----------|----------|--------|
| **skills-eval** | 22 | Cargo cult detection, documentation testing, quality gates, TOC requirements, voice consistency | HIGH | ✅ COMPLETE |
| **hooks-eval** | 17 | Security patterns, performance benchmarks, SDK integration, verification steps, compliance | HIGH | ✅ COMPLETE |
| **modular-skills** | 16 | Progressive disclosure, line limits, token optimization, single responsibility, TOC | HIGH | ✅ COMPLETE |

### Imbue Plugin (Evidence-Based Validation)

| Skill | Tests | Coverage | Priority | Status |
|-------|-------|----------|----------|--------|
| **proof-of-work** | 17 | Iron Law compliance, TDD enforcement, self-check tables, evidence logging | HIGH | ✅ COMPLETE |

### Leyline Plugin (Quality Infrastructure)

| Skill | Tests | Coverage | Priority | Status |
|-------|-------|----------|----------|--------|
| **evaluation-framework** | 15 | Weighted scoring, threshold decisions, quality gates, verification steps | HIGH | ✅ COMPLETE |
| **testing-quality-standards** | 17 | Coverage thresholds, quality metrics, anti-patterns, reliability criteria | HIGH | ✅ COMPLETE |

**Total Completed: 104 tests across 5 skills**

---

## 🔄 RECOMMENDED - Next Priority for Testing

### Pensive Plugin (Code Review Skills)

These skills perform various types of code reviews and should have validation tests:

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **review-core** | Review methodology quality, evidence requirements, checklist completeness | HIGH | Core review infrastructure |
| **test-review** | Test quality assessment, coverage validation, anti-pattern detection | HIGH | References testing-quality-standards |
| **api-review** | API design validation, contract verification, documentation completeness | MEDIUM | API quality gate |
| **architecture-review** | Architecture principles validation, pattern compliance, trade-off analysis | MEDIUM | Design quality assessment |
| **bug-review** | Root cause analysis validation, fix verification, regression testing | MEDIUM | Bug fix quality |
| **math-review** | Numerical correctness, edge case validation, precision verification | LOW | Specialized domain |
| **makefile-review** | Makefile best practices, portability, target validation | LOW | Build system quality |
| **rust-review** | Rust patterns, ownership validation, safety checks | LOW | Language-specific |
| **fpf-review** | Functional programming patterns, purity validation | LOW | Paradigm-specific |
| **unified-review** | Multi-language review methodology, unified criteria | MEDIUM | Cross-language consistency |
| **shell-review** | Shell script correctness, portability, security | MEDIUM | Script quality |

**Recommended Tests for Pensive**: ~150 tests (15 skills × ~10 tests each)

### Sanctum Plugin (Workflow Validation)

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **pr-review** | PR quality checklist, review completeness, approval criteria | HIGH | Git workflow quality gate |
| **test-updates** | Test update validation, coverage preservation, regression checks | HIGH | Test maintenance quality |
| **git-workspace-review** | Workspace cleanliness, commit quality, branch hygiene | MEDIUM | Git workflow enforcement |
| **doc-updates** | Documentation consistency, link validation, completeness | MEDIUM | Doc quality gate |
| **doc-consolidation** | Consolidation correctness, deduplication validation | LOW | Refactoring quality |

**Recommended Tests for Sanctum**: ~40 tests (5 skills × ~8 tests each)

### Parseltongue Plugin (Python Testing)

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **python-testing** | Python test patterns, pytest validation, async testing | HIGH | References testing-quality-standards |
| **python-performance** | Performance benchmarking, profiling validation, optimization | MEDIUM | Performance quality gate |
| **python-async** | Async patterns, concurrency validation, error handling | MEDIUM | Async correctness |
| **python-packaging** | Package structure validation, dependency checking, publishing | MEDIUM | Distribution quality |

**Recommended Tests for Parseltongue**: ~35 tests (4 skills × ~9 tests each)

### Abstract Plugin (Additional Evaluation Skills)

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **subagent-testing** | Subagent test patterns, isolation validation, TDD for skills | HIGH | Skill testing methodology |
| **validate-plugin-structure** | Plugin structure validation, schema compliance, metadata checks | HIGH | Plugin quality gate |
| **hook-authoring** | Hook correctness validation, scope validation, security | MEDIUM | Hook quality gate |

**Recommended Tests for Abstract**: ~25 tests (3 skills × ~8 tests each)

---

## 📋 LOWER PRIORITY - Specialized Evaluation Skills

### Scribe Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **slop-detector** | Slop pattern detection, verbosity validation, clarity checks | LOW | Writing quality |
| **style-learner** | Style pattern validation, consistency checks | LOW | Style enforcement |

### Conjure Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **delegation-core** | Delegation validation, correctness checks | LOW | Delegation quality |
| **qwen-delegation** | Qwen-specific validation, model constraints | LOW | Model-specific |
| **gemini-delegation** | Gemini-specific validation, model constraints | LOW | Model-specific |

### Spec-Kit Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **speckit-orchestrator** | Orchestrator validation, workflow correctness | MEDIUM | Spec quality gate |
| **spec-writing** | Spec completeness, validation criteria, acceptance criteria | MEDIUM | Spec quality |
| **task-planning** | Task breakdown validation, dependency checking | MEDIUM | Planning quality |

### Imbue Plugin (Additional)

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **review-core** | Review methodology validation (if different from pensive) | HIGH | Core review infrastructure |
| **structured-output** | Output structure validation, schema compliance | MEDIUM | Output quality |
| **scope-guard** | Scope validation, size checking, complexity assessment | MEDIUM | Scope enforcement |
| **workflow-monitor** | Workflow efficiency, error detection, optimization | MEDIUM | Workflow quality |
| **evidence-logging** | Evidence completeness, reproducibility validation | HIGH | Evidence quality gate |

### Attune Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **project-init** | Init template validation, structure correctness | MEDIUM | Project setup quality |
| **project-planning** | Planning methodology validation, completeness checks | MEDIUM | Planning quality |
| **project-specification** | Spec completeness, requirement validation | MEDIUM | Requirements quality |
| **project-execution** | Execution validation, milestone tracking | LOW | Execution monitoring |

### Conserve Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **context-optimization** | Optimization validation, efficiency checks | MEDIUM | Context quality |
| **token-conservation** | Token usage validation, conservation patterns | MEDIUM | Token efficiency |
| **cpu-gpu-performance** | Performance benchmarking, optimization validation | MEDIUM | Performance quality |
| **code-quality-principles** | Quality principles validation, anti-pattern detection | HIGH | Code quality gate |

### Memory-Palace Plugin

| Skill | Suggested Test Focus | Priority | Rationale |
|-------|---------------------|----------|-----------|
| **review-chamber** | Review methodology, quality validation | MEDIUM | Knowledge review quality |

---

## 📊 Summary Statistics

### Current State
- **Completed**: 5 skills with 104 tests
- **In Progress**: 0 skills
- **Recommended**: ~400+ tests across 40+ skills

### Priority Breakdown

**HIGH Priority (Core Infrastructure)**
- Completed: 5 skills (skills-eval, hooks-eval, modular-skills, proof-of-work, evaluation-framework, testing-quality-standards)
- Recommended: 8 skills (review-core, test-review, pr-review, python-testing, subagent-testing, validate-plugin-structure, evidence-logging, code-quality-principles)
- **Total HIGH**: ~13 skills requiring ~180 tests

**MEDIUM Priority (Domain-Specific)**
- Recommended: 20+ skills across pensive, sanctum, parseltongue, spec-kit, imbue, attune, conserve
- **Total MEDIUM**: ~150 tests

**LOW Priority (Specialized)**
- Recommended: 10+ skills across scribe, conjure, memory-palace
- **Total LOW**: ~70 tests

---

## 🎯 Testing Strategy

### Anti-Cargo Cult Patterns to Test

All evaluation skills should be tested for:

1. **Concrete Quick Starts**
   - ✅ Actual commands, not abstract descriptions
   - ✅ Verifiable examples with output

2. **Verification Steps**
   - ✅ Commands to validate examples work
   - ✅ Evidence of execution

3. **Quality Standards Defined**
   - ✅ Scoring criteria documented
   - ✅ Thresholds specified
   - ✅ Anti-patterns listed

4. **Documentation Testing**
   - ✅ TOCs for long modules (>100 lines)
   - ✅ Progressive disclosure structure
   - ✅ Third-person voice consistency

5. **Metacognitive Validation**
   - ✅ Skill practices what it preaches
   - ✅ Evaluation framework itself evaluated
   - ✅ Quality standards meet quality standards

### Test Template Pattern

```python
class Test{Skill}QualityFramework:
    """Feature: {skill} provides {domain} evaluation.

    As a {role}
    I want automated {domain} checks
    So that {domain} meets standards
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_{skill}_defines_quality_criteria(self, content: str) -> None:
        """Scenario: {skill} defines quality criteria."""
        assert "quality" in content.lower() or "criteria" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_{skill}_includes_verification_steps(self, content: str) -> None:
        """Scenario: {skill} includes verification after examples."""
        assert "verification" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_{skill}_avoids_cargo_cult(self, content: str) -> None:
        """Scenario: {skill} avoids abstract descriptions."""
        assert "```" in content  # Has code blocks
```

---

## 🔧 Implementation Roadmap

### Phase 1: Core Infrastructure (HIGH Priority)
**Target**: 8 skills, ~80 tests
- pensive:review-core
- pensive:test-review
- sanctum:pr-review
- parseltongue:python-testing
- abstract:subagent-testing
- abstract:validate-plugin-structure
- imbue:evidence-logging
- conserve:code-quality-principles

### Phase 2: Domain-Specific (MEDIUM Priority)
**Target**: 15 skills, ~120 tests
- pensive reviews (api, architecture, bug, unified, shell)
- sanctum validations (test-updates, git-workspace-review, doc-updates)
- parseltongue (python-performance, python-async, python-packaging)
- spec-kit (speckit-orchestrator, spec-writing, task-planning)

### Phase 3: Specialized (LOW Priority)
**Target**: 10+ skills, ~70 tests
- scribe (slop-detector, style-learner)
- conjure (delegation variants)
- memory-palace (review-chamber)
- Additional domain-specific skills

---

## 📝 Quality Gates for Evaluation Skills

Before an evaluation skill is considered production-ready, it must have:

1. ✅ **BDD-style tests** validating all quality criteria
2. ✅ **Anti-cargo cult patterns** documented and tested
3. ✅ **Concrete Quick Start** with verification steps
4. ✅ **TOC** if skill >100 lines
5. ✅ **Quality standards** that the skill itself meets
6. ✅ **Verification examples** for all code examples
7. ✅ **Third-person voice** throughout
8. ✅ **Evidence-based** recommendations, not opinions

---

## 🔄 Recursion Principle

**"Evaluation skills must evaluate themselves"**

This is the core principle:
- skills-eval must be skill-evaluated
- hooks-eval must be hook-evaluated
- testing-quality-standards must meet testing quality standards
- evaluation-framework must be evaluation-framework-compliant

This recursive validation prevents the irony of evaluation frameworks that don't meet their own standards.

---

*Last Updated: 2025-01-24*
*Completed: 104 tests across 5 core evaluation skills*
*Recommended: ~400+ tests across 40+ evaluation-related skills*
