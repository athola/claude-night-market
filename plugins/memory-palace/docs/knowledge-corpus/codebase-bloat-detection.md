---
title: Codebase Bloat Detection - Tools and Techniques
source: Research Session 2025-12-31 (43 sources)
date_captured: 2025-12-31
palace: Code Quality
district: Static Analysis & Maintenance
maturity: growing
tags: [bloat-detection, static-analysis, git-history, documentation-quality, code-quality, dead-code, technical-debt]
queries:
  - How to detect unused code programmatically?
  - What tools exist for Python dead code detection?
  - How to analyze git history for stale files?
  - What metrics indicate documentation bloat?
  - How to detect import bloat in Python?
  - What causes bundle bloat in JavaScript?
  - How to find technical debt hotspots?
  - Best practices for code churn analysis?
---

# Codebase Bloat Detection: A Multi-Layered Approach

## Core Thesis

Codebase bloat detection requires a three-tier progressive architecture: quick heuristics for fast scans, static analysis for programmatic detection, and deep git history analysis for contextual understanding. No single tool catches everything - effective detection combines multiple techniques across code, documentation, and repository history.

## The Detection Landscape (Memory Palace Layout)

```
Bloat Detection Tower (Palace)
├── Quick Scan Observatory (Tier 1: Heuristics)
│   ├── File size thresholds (>500 lines = red flag)
│   ├── Git staleness checks (6+ months untouched)
│   └── Obvious patterns (commented blocks, TODO graveyard)
├── Static Analysis Laboratory (Tier 2: Tool Integration)
│   ├── Python Wing: Vulture, deadcode, autoflake
│   ├── JavaScript Wing: Knip, tree-shaking analysis
│   └── Multi-Language Wing: SonarQube metrics API
└── Deep Audit Archives (Tier 3: Git + Context)
    ├── Code churn × complexity hotspots
    ├── Ownership + cohesion quality triangle
    └── Documentation similarity detection
```

## Key Tools & Techniques

### 1. Python Static Analysis
**Location**: Static Analysis Laboratory - Python Wing
**Sensory Encoding**: Sharp, precise surgical tools revealing hidden waste

**Vulture** (Recommended)
- **API**: Programmatic access available
- **Confidence Scoring**: 60-100% confidence levels
- **Usage Pattern**: `vulture . --min-confidence 80`
- **Strength**: High accuracy, low false positives at 80%+ confidence
- **Source**: https://github.com/jendrikseipp/vulture

**deadcode** (Fastest)
- **Configuration**: `pyproject.toml` based
- **Auto-fix**: `--fix` flag removes unused code
- **Ignore Patterns**: Whitelist false positives
- **Strength**: Fast, integrated with Python tooling
- **Source**: https://github.com/albertas/deadcode

**autoflake** (Import Specialist)
- **Focus**: Unused imports and star import expansion
- **Performance Impact**: 40-70% startup time reduction possible
- **Best Practice**: Run before vulture for cleaner results
- **Source**: https://github.com/PyCQA/autoflake

**PyTrim** (Research, Oct 2024)
- **Scope**: End-to-end dependency cleanup
- **Novel Approach**: Removes unused transitive dependencies
- **Status**: Recent research, promising for dependency bloat
- **Source**: https://arxiv.org/html/2510.00674v1

### 2. JavaScript/TypeScript Analysis
**Location**: Static Analysis Laboratory - JavaScript Wing
**Sensory Encoding**: Bundle weight pressing down, tree-shaking lightness

**Knip** (CLI Only - No API Yet)
- **Current Limitation**: ⚠️ No programmatic API (CLI only)
- **Roadmap**: API support planned
- **Configuration**: `.knip.json` or package.json
- **Strength**: Detailed dead code detection
- **Workaround**: Shell out to CLI, parse JSON output
- **Source**: https://github.com/webpro-nl/knip

**Tree Shaking Best Practices**
- **Requires**: ESM modules (CommonJS blocks it)
- **Anti-Pattern**: Barrel files (`export *`) break dead code elimination
- **Detection**: Check `package.json` for `"module"` entry
- **Side Effects**: Mark side-effect-free in package.json
- **Sources**: Webpack docs, Smashing Magazine guide

**TypeScript-Specific Bloat**
- **tslib**: Duplicated in CommonJS mode (use ESM)
- **Type-only imports**: Use `import type` to prevent runtime bloat

### 3. Git History Analysis
**Location**: Deep Audit Archives
**Sensory Encoding**: Dusty repository layers, archaeological excavation of code evolution

**Staleness Detection**
```bash
# Files not touched in 6+ months
git log --since="6 months ago" --name-only --pretty=format: | sort -u | comm -13 - <(git ls-files)

# Files never referenced elsewhere (potential orphans)
git ls-files | while read f; do git grep -q "$(basename $f)" || echo "$f"; done
```

**Code Churn Metrics**
- **Formula**: `Churn × Complexity = Technical Debt Hotspots`
- **Quality Triangle**: `Ownership + Cohesion + Churn`
- **Tool**: AskGit (SQL queries against git data)
- **Command**: `git log --stat --oneline` for churn rates
- **Sources**: GitClear blog, tdebt repo

**Ownership & Cohesion**
- **git blame**: Identify rarely-changed code sections
- **Threshold**: Code untouched for 2+ years = Lava Flow candidate
- **Pattern**: Many authors + high churn = ownership problem

### 4. Documentation Bloat
**Location**: Deep Audit Archives - Documentation Hall
**Sensory Encoding**: Dense text fog clearing to reveal readable prose

**Readability Metrics**
- **Flesch Reading Ease**: Target 70-80 (8th grade level)
- **Flesch-Kincaid Grade**: 4-6.5 for technical docs
- **ARI (Automated Readability Index)**: Designed for technical writing
- **Standards**: ≤5% passive voice, ≥80% readability, Fog < 13
- **Tool**: `py-readability-metrics` Python library
- **Sources**: ClickHelp blog, Technical Writer HQ

**Markdown-Specific Analysis**
- **Tool**: `mrkdwn_analysis` (Python)
- **Metrics**: Word count, complexity, structure analysis
- **Clean Counting**: Pandoc filters for accurate word counts (minus syntax)
- **Source**: https://github.com/yannbanas/mrkdwn_analysis

**Duplicate Detection**
- **Jaccard Similarity**: 0-1 scale for document comparison
- **Cosine Similarity**: Vector-based semantic comparison
- **MinHash/SimHash**: Fast hashing for near-duplicate detection
- **Threshold**: 80%+ similarity = redundant documentation

### 5. Language-Specific Anti-Patterns
**Location**: Pattern Recognition Chamber
**Sensory Encoding**: Code smells wafting up, architectural rot visible in structure

**Python Anti-Patterns**
- **God Class**: >500 lines, >10 methods, multiple concerns
- **Lava Flow**: Unchanged >2 years, commented blocks, stale TODOs
- **Import Bloat**: Star imports (`from x import *`), unused imports
- **Lazy Imports**: PEP 690/810 for major performance gains
- **Sources**: BairesDev blog, QuantifiedCode anti-patterns

**JavaScript/TypeScript Anti-Patterns**
- **CommonJS Bloat**: Prevents tree shaking (migrate to ESM)
- **Barrel Files**: `export *` breaks dead code elimination
- **Side Effects**: Prevent optimization if unmarked
- **Bundle Analysis**: Use webpack-bundle-analyzer

**Markdown Anti-Patterns**
- **Deep Nesting**: >3 levels problematic for readability
- **Giant Tables**: >10 rows hard to maintain
- **Code Blocks in Lists**: Parser complexity increases
- **Inconsistent Indentation**: Tabs vs spaces issues

## Multi-Language Detection Strategy (SonarQube)
**Location**: Static Analysis Laboratory - Central Tower
**Sensory Encoding**: Dashboard of metrics, unified quality view

**SonarQube Web API**
- **Metrics Available**: Cyclomatic complexity, duplication, maintainability
- **Duplication Threshold**: 100+ tokens or 10+ statements
- **Integration**: REST API for programmatic access
- **Use Case**: Cross-language quality monitoring
- **Source**: https://docs.sonarsource.com/sonarqube-server/

## Progressive 3-Tier Architecture

### Tier 1: Quick Scan (Heuristics)
**Speed**: Seconds
**Purpose**: Fast red flags for daily use
**Checks**:
- File size >500 lines
- Git staleness >6 months
- Commented code blocks >50 lines
- TODO count >10 in single file

### Tier 2: Static Analysis (Tool Integration)
**Speed**: Minutes
**Purpose**: Programmatic detection with high confidence
**Tools**:
- Python: Vulture (80%+ confidence)
- JavaScript: Knip CLI (parse JSON output)
- Documentation: mrkdwn_analysis

### Tier 3: Deep Audit (Git + Context)
**Speed**: Hours
**Purpose**: Contextual understanding for major refactoring
**Analysis**:
- Code churn × complexity hotspots
- Ownership + cohesion quality triangle
- Documentation similarity matrix
- Historical staleness patterns

## Practical Application to Conserve Plugin

### Recommended Implementation

**Skill Structure**:
```
conserve/skills/bloat-detector/
├── SKILL.md                    # Hub with tier selection
├── modules/
│   ├── quick-scan.md           # Tier 1 heuristics
│   ├── static-analysis.md      # Tier 2 tool integration
│   ├── git-history-analysis.md # Tier 3 deep audit
│   ├── documentation-bloat.md  # Readability + similarity
│   └── language-patterns.md    # Python, JS, Markdown specifics
└── baseline-scenarios.md       # Test scenarios for validation
```

**Subagent**:
- `conserve:bloat-auditor` - Orchestrates multi-tier detection
- Tool restrictions: Bash (git commands), Grep (pattern matching)
- Model: Haiku for speed, escalate to Sonnet for analysis

**Integration Points**:
1. Pre-commit hook: Quick scan (Tier 1)
2. Weekly CI job: Static analysis (Tier 2)
3. Quarterly review: Deep audit (Tier 3)

### Detection Scripts (Optional)

**Python Integration** (`scripts/bloat-detector.py`):
```python
import vulture
from deadcode import DeadCode

def detect_python_bloat(paths):
    # Vulture for unused code
    v = vulture.Vulture()
    v.scavenge(paths)
    unused = [item for item in v.get_unused_code() if item.confidence >= 80]

    # deadcode for thorough scan
    dc = DeadCode(paths)
    dead = dc.find_dead_code()

    return {"vulture": unused, "deadcode": dead}
```

**Git History Analysis** (`scripts/git-staleness.sh`):
```bash
#!/bin/bash
# Find files not modified in 6+ months
git log --since="6 months ago" --name-only --pretty=format: | \
  sort -u | comm -13 - <(git ls-files) | \
  head -20
```

**Markdown Analysis** (use mrkdwn_analysis library):
```python
from mrkdwn_analysis import analyze_markdown

def check_doc_bloat(md_files):
    for file in md_files:
        stats = analyze_markdown(file)
        if stats.nesting_depth > 3:
            print(f"⚠️  {file}: Deep nesting ({stats.nesting_depth})")
        if stats.readability_score < 70:
            print(f"⚠️  {file}: Low readability ({stats.readability_score})")
```

## Cross-References

### Internal Skills & Plugins
- `conserve:context-optimization` - Uses bloat detection for skill optimization
- `conserve:unbloat-remediator` - Applies fixes based on bloat detection
- `abstract:plugin-validator` - Validates plugin structure health
- `sanctum:git-workflow` - Git history analysis integration

### Related Concepts
- Token conservation principles (conserve plugin philosophy)
- Progressive disclosure (modular skill design)
- Technical debt quantification (quality metrics)

## Implementation Checklist

From the original research session, these are the recommended next steps:

- [ ] Create `conserve:bloat-detector` skill with 3-tier architecture
- [ ] Create `conserve:bloat-auditor` subagent
- [ ] Add modules for each detection layer (5 modules)
- [ ] Integrate Vulture API for Python detection
- [ ] Add git history analysis commands
- [ ] Create documentation bloat metrics
- [ ] Update conserve plugin README with new capabilities
- [ ] Add baseline test scenarios

## Meta-Insights

> **Token Optimization Alignment**: The 3-tier progressive architecture mirrors the conserve plugin's philosophy - start cheap (heuristics), escalate when needed (static analysis), go deep only when justified (git audit).

> **No Silver Bullet**: Every tool has blind spots. Vulture misses dynamic imports, Knip lacks programmatic API, git history can't detect logical bloat. Effective detection combines multiple techniques.

> **Performance vs. Accuracy Trade-off**: Quick scans have false positives, deep audits are slow. The tier system lets users choose appropriate depth for their context.

## Source Attribution

This knowledge entry synthesizes 43 sources from a thorough research session on 2025-12-31.

 Key sources by category:

**Static Analysis**:
- Vulture: https://github.com/jendrikseipp/vulture
- deadcode: https://github.com/albertas/deadcode
- autoflake: https://github.com/PyCQA/autoflake
- PyTrim research: https://arxiv.org/html/2510.00674v1
- Knip: https://github.com/webpro-nl/knip
- SonarQube: https://docs.sonarsource.com/sonarqube-server/

**Git Analysis**:
- AskGit: https://augmentable.medium.com/identifying-code-churn-with-askgit-sql-1b91680f6349
- GitClear technical debt: https://www.gitclear.com/blog/minimize_technical_debt_and_churn
- tdebt hotspot detection: https://github.com/mduerig/tdebt
- GitHub stale-repos: https://github.com/github/stale-repos

**Documentation Quality**:
- Flesch metrics: https://clickhelp.com/clickhelp-technical-writing-blog/improve-the-readability-of-your-technical-documentation-with-flesch/
- py-readability-metrics: https://github.com/cdimascio/py-readability-metrics
- mrkdwn_analysis: https://github.com/yannbanas/mrkdwn_analysis
- Document similarity: https://journalofbigdata.springeropen.com/articles/10.1186/s40537-018-0163-2

**Language Patterns**:
- Python anti-patterns: https://docs.quantifiedcode.com/python-anti-patterns/
- JavaScript tree shaking: https://www.smashingmagazine.com/2021/05/tree-shaking-reference-guide/
- Bundle optimization: https://madelinemiller.dev/blog/reduce-webapp-bundle-size/
- Markdown best practices: https://www.markdownlang.com/advanced/best-practices.html

**Full source list** (43 total): See original research document in queue archive.

---

**Maturity Status**: Growing → Will become Evergreen after implementation and field testing of bloat-detector skill.

**Maintenance Notes**: Update when new static analysis tools emerge or when bloat-detector implementation reveals gaps in the research.
