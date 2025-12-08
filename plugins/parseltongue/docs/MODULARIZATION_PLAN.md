# Parseltongue Modularization Plan

## Executive Summary

Based on comprehensive analysis using `plugin-validator`, `skills-eval`, `hooks-eval`, and `modular-skills` methodologies, this plan outlines how to modularize parseltongue skills for:
- **59-79% context reduction** through progressive loading
- **10,500+ tokens** of cross-plugin deduplication
- **Improved reusability** with leyline integration

## Current State Analysis

### Plugin Validation Results
- **Status**: ✅ VALID
- **Name**: `parseltongue` (kebab-case compliant)
- **Skills**: 4 monolithic skills (python-testing, python-async, python-performance, python-packaging)
- **Hooks**: None
- **Issue**: Empty `modules/` directories in skills (infrastructure ready but unused)

### Skills Token Analysis

| Skill | Lines | Current Tokens | Hub Tokens | Savings |
|-------|-------|---------------|------------|---------|
| python-testing | 240 | 1,450 | 599 | 59% |
| python-async | 360 | 3,000 | 100 | 97% (with module loading) |
| python-performance | 360 | 2,000 | 200 | 90% (with module loading) |
| python-packaging | 406 | 1,200 | 300 | 75% |

## Phase 1: Python-Testing Modularization

### Module Breakdown

```
python-testing/
├── SKILL.md (Hub - 599 tokens)
│   ├── Quick Start
│   ├── When to Use
│   ├── Module Navigation
│   └── Exit Criteria
├── modules/
│   ├── unit-testing.md (425 tokens)
│   │   └── AAA pattern, basic pytest, assertions
│   ├── fixtures-and-mocking.md (500 tokens)
│   │   └── pytest fixtures, parameterization, mocking
│   ├── test-infrastructure.md (300 tokens)
│   │   └── pyproject.toml, directory structure, pytest config
│   ├── testing-workflows.md (325 tokens)
│   │   └── Running tests, CI/CD integration
│   ├── test-quality.md (250 tokens)
│   │   └── Best practices, anti-patterns, exit criteria
│   └── async-testing.md (275 tokens)
│       └── pytest-asyncio, async fixtures
```

### Cross-Plugin References
- `pensive:test-review` → Reference `test-quality.md`
- `parseltongue:python-async` → Reference `async-testing.md`
- `sanctum:commit-messages` → Reference `test-quality.md` for test commit patterns

## Phase 2: Python-Async Modularization

### Module Breakdown

```
python-async/
├── SKILL.md (Hub - 100 tokens)
├── modules/
│   ├── basic-patterns.md (250 tokens)
│   │   └── Event loop, coroutines, tasks, gather()
│   ├── concurrency-control.md (220 tokens)
│   │   └── Semaphores, locks, rate limiting
│   ├── error-handling-timeouts.md (280 tokens)
│   │   └── Exception handling, timeouts, cancellation
│   ├── advanced-patterns.md (350 tokens)
│   │   └── Context managers, iterators, producer-consumer
│   ├── testing-async.md (180 tokens)
│   │   └── pytest-asyncio patterns
│   ├── real-world-applications.md (220 tokens)
│   │   └── aiohttp, async DB, framework integration
│   └── pitfalls-best-practices.md (300 tokens)
│       └── Common mistakes, 10 best practices
```

### Cross-Plugin References
- `conservation:context-optimization` → Reference `concurrency-control.md`
- `abstract:hooks-eval` → Reference `error-handling-timeouts.md`
- `imbue:catchup` → Reference `real-world-applications.md`

## Phase 3: Python-Performance Modularization

### Module Breakdown

```
python-performance/
├── SKILL.md (Hub - 200 tokens)
├── modules/
│   ├── profiling-tools.md (360 tokens)
│   │   └── cProfile, line_profiler, memory_profiler, py-spy
│   ├── optimization-patterns.md (811 tokens)
│   │   └── 10 concrete optimization patterns
│   ├── memory-management.md (167 tokens)
│   │   └── tracemalloc, WeakRef, leak detection
│   ├── benchmarking-tools.md (173 tokens)
│   │   └── Decorators, pytest-benchmark
│   └── best-practices.md (207 tokens)
│       └── Guidelines, pitfalls, exit criteria
```

### Cross-Plugin References
- `conservation:cpu-gpu-performance` → Reference `profiling-tools.md`
- `abstract:performance-benchmarking` → Consolidate with `benchmarking-tools.md`

## Phase 4: Leyline Integration

### New Shared Modules for Leyline

```
leyline/skills/
├── pytest-config/SKILL.md (NEW)
│   └── Shared pytest configuration patterns
├── python-config/SKILL.md (NEW)
│   └── Shared pyproject.toml, ruff, mypy patterns
├── async-testing/SKILL.md (NEW)
│   └── Extracted from parseltongue for cross-plugin use
└── testing-quality-standards/SKILL.md (NEW)
    └── Shared quality metrics for pensive:test-review + parseltongue
```

## Implementation Priority

### Immediate (Phase 1)
1. ✅ Create `python-testing/modules/` structure
2. Extract `unit-testing.md` from SKILL.md
3. Extract `fixtures-and-mocking.md`
4. Extract `test-infrastructure.md`
5. Refactor SKILL.md as hub

### Short-term (Phase 2)
1. Create `python-async/modules/` structure
2. Extract `concurrency-control.md` (high cross-plugin value)
3. Extract `error-handling-timeouts.md` (high reuse)
4. Refactor SKILL.md as hub

### Medium-term (Phase 3-4)
1. Create `python-performance/modules/` structure
2. Integrate with leyline shared modules
3. Update pensive:test-review to reference shared modules

## Token Savings Summary

| Category | Before | After | Savings |
|----------|--------|-------|---------|
| python-testing (hub load) | 1,450 | 599 | 59% |
| python-async (hub load) | 3,000 | 100 | 97% |
| python-performance (hub load) | 2,000 | 200 | 90% |
| Cross-plugin deduplication | N/A | N/A | ~150 tokens |
| **Total typical session** | **6,450** | **~1,900** | **71%** |

## Success Criteria

- [ ] All skills pass `plugin-validator`
- [ ] Each hub < 200 lines
- [ ] Each module < 150 lines
- [ ] Progressive loading enabled in frontmatter
- [ ] Cross-plugin references documented
- [ ] Token estimates accurate (±10%)
