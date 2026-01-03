# Research Session: Codebase Bloat Detection

## Metadata

- **Queue Entry ID**: 2025-12-31_codebase-bloat-detection-research
- **Created**: 2025-12-31T01:43:56Z
- **Session Type**: brainstorming
- **Topic**: Codebase Bloat Detection - Deep Research
- **Status**: processed
- **Priority**: high

## Context

User requested deep research into codebase bloat detection to inform creation of a new skill and subagent pair in the conserve plugin. Research covered 4 major areas:
1. Static analysis tool APIs
2. Git history analysis techniques
3. Documentation bloat metrics
4. Language-specific patterns (Python, JS, Markdown)

## Research Conducted

### Web Searches Performed (8 total)

1. **Static Analysis Tools - Python**
   - Vulture API programmatic usage
   - deadcode configuration and whitelist patterns
   - autoflake for import cleanup
   - PyTrim for dependency bloat

2. **Static Analysis Tools - JavaScript/TypeScript**
   - Knip API and configuration
   - Tree shaking and bundle size optimization
   - SonarQube metrics API

3. **Git History Analysis**
   - Finding stale/unused files via git log
   - git blame for rarely-changed code
   - Code churn metrics and technical debt hotspots

4. **Documentation Bloat**
   - Readability metrics (Flesch-Kincaid, ARI)
   - Markdown-specific analysis tools
   - Duplicate documentation detection (Jaccard, Cosine similarity)

5. **Language-Specific Patterns**
   - Python anti-patterns (God Class, Lava Flow, import bloat)
   - JavaScript/TypeScript bundle bloat and barrel files
   - Markdown nesting anti-patterns
   - Python star imports and unused dependencies

## Key Findings Summary

### Static Analysis Tools

**Python:**
- Vulture: Programmatic API available, 60-100% confidence scoring
- deadcode: pyproject.toml config, --fix flag, ignore patterns
- autoflake: Star import expansion, removes unused imports
- PyTrim: End-to-end dependency cleanup (Oct 2024 research)

**JavaScript/TypeScript:**
- Knip: ⚠️ No programmatic API (CLI only, on roadmap)
- Tree shaking requires ESM modules (CommonJS blocks it)
- Barrel files break tree shaking
- TypeScript tslib bloat in CommonJS mode

**Multi-Language:**
- SonarQube: Web API for metrics (cyclomatic complexity, duplication)
- Duplication threshold: 100+ tokens or 10+ statements

### Git History Techniques

**Commands:**
```bash
# Stale files (6+ months)
git log --since="6 months ago" --name-only --pretty=format:

# Unused files (not referenced)
git ls-files | while read f; do git grep -q "$f" || echo "$f"; done

# Code churn
git log --stat --oneline
```

**Metrics:**
- Churn × Complexity = Technical Debt Hotspots
- Ownership + Cohesion + Churn = Quality Triangle
- AskGit: SQL queries against git data

### Documentation Bloat Metrics

**Readability Scores:**
- Flesch Reading Ease: 70-80 target (8th grade)
- Flesch-Kincaid Grade: 4-6.5 for technical docs
- ARI (Automated Readability Index): Designed for technical writing
- Standards: ≤5% passive voice, ≥80% readability, Fog < 13

**Tools:**
- mrkdwn_analysis (Python): Word count, complexity, structure analysis
- wordcountaddin (R): Readability stats for R Markdown
- Pandoc filters: Clean word counts minus syntax

**Similarity Detection:**
- Jaccard Similarity: 0-1 scale for duplicates
- Cosine Similarity: Vector-based comparison
- MinHash/SimHash: Fast hashing for near-duplicates

### Language-Specific Patterns

**Python:**
- God Class: >500 lines, >10 methods, multiple concerns
- Lava Flow: Unchanged code >2 years, commented blocks, stale TODOs
- Import bloat: Star imports, unused imports (40-70% startup reduction possible)
- Lazy imports (PEP 690/810): Major performance gains

**JavaScript/TypeScript:**
- CommonJS prevents tree shaking (use ESM)
- Barrel files (export *) break dead code elimination
- Side effects prevent optimization
- Check package.json for "module" entry

**Markdown:**
- Nesting threshold: >3 levels problematic
- Table limit: >10 rows hard to maintain
- Code blocks in nested lists = parser hell
- Inconsistent indentation (tabs vs spaces)

## Evaluation Scores (Knowledge-Intake Rubric)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Novelty | 80 | detailed tool landscape, recent research (2024-2025) |
| Applicability | 95 | Directly applicable to bloat-detector skill creation |
| Durability | 85 | Tool APIs stable, patterns enduring |
| Connectivity | 90 | Links to conservation, static analysis, git workflows |
| Authority | 85 | Multiple credible sources, academic papers, official docs |
| **TOTAL** | **87** | **Evergreen - Store and Apply** |

## Routing Recommendation

**Type**: Meta-Infrastructure (plugin development)

**Applications:**
1. Create `conservation:bloat-detector` skill with 3-tier architecture
2. Create `conservation:bloat-auditor` subagent
3. Add modules for each detection layer
4. Update conserve plugin with new capabilities

**Storage:**
- Location: `docs/knowledge-corpus/codebase-bloat-detection.md`
- Format: Full memory palace entry
- Maturity: Growing (will become Evergreen after implementation)

## Implementation Artifacts Needed

1. **Skill Structure:**
   ```
   conservation/skills/bloat-detector/
   ├── SKILL.md (hub)
   ├── modules/
   │   ├── quick-scan.md (heuristics)
   │   ├── static-analysis.md (tool integration)
   │   ├── git-history.md (churn, staleness)
   │   ├── documentation-bloat.md (readability, similarity)
   │   └── language-patterns.md (Python, JS, Markdown)
   └── baseline-scenarios.md
   ```

2. **Subagent:**
   ```
   conservation/agents/bloat-auditor.md
   ```

3. **Detection Scripts (optional):**
   - Python: Vulture/deadcode integration
   - Shell: Git history analysis
   - Python: Markdown analysis (mrkdwn_analysis)

## Sources (43 total)

### Static Analysis
- https://pypi.org/project/vulture/
- https://github.com/jendrikseipp/vulture
- https://pypi.org/project/deadcode/
- https://github.com/albertas/deadcode
- https://github.com/PyCQA/autoflake
- https://arxiv.org/html/2510.00674v1
- https://github.com/webpro-nl/knip
- https://knip.dev/reference/configuration
- https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition

### Git Analysis
- https://madelinemiller.dev/blog/knip-dead-code/
- https://tanzu.vmware.com/content/blog/a-simple-way-to-detect-unused-files-in-a-project-using-git
- https://github.com/github/stale-repos
- https://adamj.eu/tech/2022/04/18/how-to-clean-up-unused-code-with-git/
- https://augmentable.medium.com/identifying-code-churn-with-askgit-sql-1b91680f6349
- https://github.com/flacle/truegitcodechurn
- https://axify.io/blog/git-analytics
- https://www.gitclear.com/blog/minimize_technical_debt_and_churn
- https://github.com/mduerig/tdebt
- https://git-scm.com/docs/git-blame

### Documentation Bloat
- https://clickhelp.com/clickhelp-technical-writing-blog/improve-the-readability-of-your-technical-documentation-with-flesch/
- https://medium.com/technical-writing-is-easy/readability-metrics-and-technical-writing-b776422eaba
- https://github.com/cdimascio/py-readability-metrics
- https://technicalwriterhq.com/writing/technical-writing/technical-writing-metrics/
- https://pypi.org/project/markdown-analysis/
- https://github.com/benmarwick/wordcountaddin
- https://www.danieltorrecillas.com/blog/meaningful-word-count-for-markdown/
- https://github.com/yannbanas/mrkdwn_analysis
- https://github.com/malteos/awesome-document-similarity
- https://journalofbigdata.springeropen.com/articles/10.1186/s40537-018-0163-2

### Language Patterns
- https://www.bairesdev.com/blog/software-anti-patterns/
- https://medium.com/@devlinktips/10-python-anti-patterns-ruining-your-code-and-what-to-do-instead-e304c457bc98
- https://docs.quantifiedcode.com/python-anti-patterns/
- https://medium.com/expsoftwareengineering/anti-patterns-dead-code-lava-flows-331af63b11cd
- https://softwarepatternslexicon.com/patterns-python/11/2/3/
- https://www.smashingmagazine.com/2021/05/tree-shaking-reference-guide/
- https://madelinemiller.dev/blog/reduce-webapp-bundle-size/
- https://webpack.js.org/guides/tree-shaking/
- https://www.markdownlang.com/advanced/best-practices.html
- https://ref.coddy.tech/markdown/markdown-nested-lists
- https://dev.to/vivekjami/unused-imports-the-hidden-performance-tax-3340
- https://medium.com/cyberark-engineering/navigating-pythons-dependency-system-from-overload-to-optimization-6209cde2bbcd

## Next Actions

- [x] Review this queue entry for storage decision
- [x] Create memory palace entry in `docs/knowledge-corpus/codebase-bloat-detection.md`
- [ ] Begin skill/subagent implementation using research findings
- [ ] Extract reusable patterns into shared modules
- [ ] Update conserve plugin README with new capabilities

## Processing Notes

**Processed**: 2026-01-02
**Action**: Approved and added to knowledge corpus
**Location**: `plugins/memory-palace/docs/knowledge-corpus/codebase-bloat-detection.md`
**Rationale**: High evaluation score (87/100) and clear evergreen value for conserve plugin development

## Notes

This research session represents significant value for the conserve plugin ecosystem. The detailed coverage across tools, techniques, and language-specific patterns provides a strong foundation for implementing a production-quality bloat detection system.

The progressive 3-tier architecture (heuristics → static analysis → deep audit) aligns well with the conserve plugin's token-optimization philosophy.
