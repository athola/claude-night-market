---
title: Agent Psychosis and Codebase Hygiene
source: Deep research synthesis (Ronacher, GitClear, MIT Tech Review, maintainer surveys)
date_captured: 2026-01-19
palace: Code Quality
district: AI-Assisted Development
maturity: budding
tags: [agent-psychosis, ai-bloat, vibe-coding, technical-debt, code-quality, slop-detection, maintainer-burden]
queries:
  - What is agent psychosis in AI coding?
  - How does AI create codebase bloat?
  - What is vibe coding technical debt?
  - How to detect AI-generated slop?
  - What is the 6-month wall in AI codebases?
  - How to prevent AI amplified cargo cult programming?
  - Why is refactoring declining in AI-assisted codebases?
  - What patterns indicate AI-generated code problems?
sensory_encoding: A gleaming factory producing shiny gadgets at incredible speed, but the quality control room is empty and dust-covered
---

# Agent Psychosis and Codebase Hygiene

Research synthesis on the emerging crisis of AI-generated code quality, maintainer burden, and codebase degradation patterns unique to the AI coding era (2024-2026).

## Core Thesis

AI coding agents create bloat faster than humans can review it, and this bloat has qualitatively different characteristics than traditional technical debt. The combination of parasocial developer-AI relationships, dopamine-driven coding loops, and declining refactoring practices is creating a new category of unmaintainable codebases.

## The Agent Psychosis Problem

**Source**: [Armin Ronacher - Agent Psychosis](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/)

### Key Phenomena

| Phenomenon | Description | Codebase Impact |
|------------|-------------|-----------------|
| **Parasocial Dependency** | Developers form emotional bonds with AI agents | Users defend low-quality code because "we built it together" |
| **Dopamine-Driven Loops** | Productivity rushes become addictive | Massive token consumption, projects built without validation |
| **Contribution Asymmetry** | Minutes to create, hours to review | Maintainer burnout, review backlog grows exponentially |
| **Cultural Echo Chambers** | Discord/X circles celebrate AI work uncritically | No external quality sanity-check |
| **Slop Generation** | Code that looks correct but lacks depth | 240,000 lines that are "abysmal" underneath |

### The One-Directional Relationship

> "The relationship is fundamentally one-directional. The agent reinforces whatever direction the user pushes it toward, lacking genuine critical thinking."

This creates a feedback loop where:
1. Developer has an idea (possibly flawed)
2. AI enthusiastically implements it
3. Developer feels validated
4. Repeat without external review

**Sensory Encoding**: A mirror that always smiles back, no matter what you show it.

## The GitClear Code Quality Crisis

**Source**: [GitClear AI Code Quality 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research)

### Historic Shift in 2024

| Metric | 2021 | 2024 | 2025 Prediction | Implication |
|--------|------|------|-----------------|-------------|
| Refactoring % of changes | 25% | <10% | 3% | Codebases rot, never cleaned |
| Code duplication (5+ lines) | Baseline | 8x increase | Worse | Copy-paste culture |
| Copy/paste vs refactor ratio | Refactor > copy | Copy > refactor | Much worse | **First historic reversal** |
| Code churn (revised in 2 weeks) | 3.1% | 5.7% | Higher | More premature commits |

### Root Cause

AI makes inserting new code as easy as pressing Tab. It does NOT propose reusing similar functions elsewhere - partly because of limited context windows.

> "Code assistants make it easy to insert new blocks of code simply by pressing the tab key. It is less likely that the AI will propose reusing a similar function elsewhere in the code."

**Sensory Encoding**: A kitchen where every meal creates new pots and pans instead of washing the existing ones.

## The Maintainer Burden Crisis

**Sources**:
- [Socket.dev: OSS Maintainers Demand Copilot Blocking](https://socket.dev/blog/oss-maintainers-demand-ability-to-block-copilot-generated-issues-and-prs)
- [st0012.dev: AI and Open Source](https://st0012.dev/ai-and-open-source-a-maintainers-take-end-of-2025)

### Evidence of Crisis

| Issue | Evidence |
|-------|----------|
| **Low-effort AI PRs** | OCaml maintainers rejected 13,000-line AI PR - couldn't review it |
| **Slop detection demand** | GitHub survey: 5% of maintainers explicitly want "slop detection" |
| **Burnout acceleration** | Kubernetes retired Ingress NGINX due to maintainer burnout (Nov 2025) |
| **Insidious errors** | "Human mistakes are easier to spot. AI-generated ones look correct, plausible." |
| **Unpaid burden** | 60% of open source maintainers work unpaid |

### The Perception Gap

Contributors feel genuinely rejected when AI PRs are closed. They believe they helped. This creates friction because:
- Contributor: "I spent 2 hours with Claude on this!"
- Maintainer: "This would take me 8 hours to review properly"
- Result: Hurt feelings, maintainer guilt, project friction

### AGENTS.md Solution

Maintainers suggest using agent instruction files to communicate directly with AI agents:

> "A contributor might not read your docs, but their agent is more likely to. This lets maintainers influence how contributors' tools behave in their repo."

## AI Slop Detection Patterns

**Sources**:
- [Glukhov: Detecting AI Slop](https://www.glukhov.org/post/2025/12/ai-slop-detection/)
- [arXiv: Measuring AI Slop in Text](https://arxiv.org/abs/2509.19163)

### Linguistic Red Flags

| Pattern | Example | Why It's Slop |
|---------|---------|---------------|
| **Excessive hedging** | "It's worth noting...", "arguably", "to some extent" | AI safety training creates artificial balance |
| **Formulaic structure** | Always numbered lists, predictable subheadings | Pattern matching, not thinking |
| **Surface insights** | Describes WHAT without explaining WHY | No genuine understanding |
| **Rhythmic patterns** | Multiple sentences with same construction | Statistical generation |
| **Artificial balance** | Hedging on obvious issues | Avoiding strong stances |

### Code-Specific Slop Patterns

| Pattern | Description | Detection Method |
|---------|-------------|------------------|
| **Hallucinated APIs** | Functions/packages that don't exist | Import verification |
| **Slopsquatting** | Fake packages with plausible names | Dependency audit |
| **Happy path only** | Tests verify success, miss edge cases | Mutation testing |
| **Ignored constraints** | Follows instructions literally, misses context | Semantic review |
| **Repetitive logic** | Same pattern repeated instead of abstracted | Duplication detection |

### Statistical Detection

**Perplexity**: How "surprised" a model is by text. Human writing shows higher perplexity (less predictable).

**Burstiness**: Variation in sentence complexity. Human writing has more variation (some simple, some complex sentences).

AI-generated text tends to be uniformly "medium complexity" - neither very simple nor very complex.

## Vibe Coding Technical Debt

**Sources**:
- [InfoWorld: Vibe Coding Gateway to Debt](https://www.infoworld.com/article/4098925/is-vibe-coding-the-new-gateway-to-technical-debt.html)
- [Tabnine: Avoid Vibe Coding Tsunami](https://www.tabnine.com/blog/how-to-avoid-vibe-coding-your-way-into-a-tsunami-of-tech-debt/)

### The "6-Month Wall"

Without rigorous security oversight, developers eventually hit the point where accumulated security debt and logical inconsistencies become so great that the app becomes unmaintainable and unfixable.

### Risk Categories

| Risk | Evidence | Mitigation |
|------|----------|------------|
| **Security vulnerabilities** | 40% of Copilot code had exploitable vulns | Security review gates |
| **Shadow debt** | Quality drop is silent, accumulates invisibly | Continuous hygiene |
| **Mystery code** | Works by coincidence, not design | Understanding verification |
| **Context blindness** | AI lacks situational awareness | Human review checkpoints |
| **Phantom dependencies** | Hallucinated libraries | Dependency verification |

### The Invisible Debt Problem

> "The biggest risk is that technical debt becomes invisible. Systems will look complete - but underneath, they'll be messy, fragile, and undocumented. And no one will know until they try to extend them."

**Sensory Encoding**: A beautiful house where all the support beams are made of cardboard - looks fine until the first storm.

## Detection Framework

### Tier 1: Quick AI Bloat Indicators

```bash
# Large single-commit additions (vibe coding signature)
git log --oneline --shortstat | grep -E "files? changed, [0-9]{3,} insertion"

# Files with 0 tests but >200 lines
find . -name "*.py" -exec sh -c 'lines=$(wc -l < "$1"); [ $lines -gt 200 ] && echo "$1"' _ {} \; | while read f; do
  test_file=$(echo $f | sed 's/.py/_test.py/')
  [ ! -f "$test_file" ] && echo "UNTESTED: $f"
done

# Duplicate code blocks (Tab-completion bloat)
# Use conserve's detect_duplicates.py script (no external deps)
python plugins/conserve/scripts/detect_duplicates.py . --min-lines 5
```

### Tier 2: AI-Specific Pattern Detection

| Pattern | Detection Command | Confidence |
|---------|-------------------|------------|
| **Massive single commits** | `git log --shortstat \| grep "500 insertion"` | HIGH |
| **No refactoring activity** | `git log --all --oneline \| grep -i refactor \| wc -l` | MEDIUM |
| **Test-to-code ratio** | Compare test file count to source file count | HIGH |
| **Duplication ratio** | `python detect_duplicates.py . --format json` | HIGH |
| **Abstraction deficit** | Count base classes with single inheritor | MEDIUM |

### Tier 3: Deep AI Hygiene Audit

- Git history pattern analysis (massive single commits)
- Duplication-to-abstraction ratio over time
- Test coverage vs code complexity mismatch
- Documentation hedge-word density analysis
- Dependency verification (hallucinated packages)
- Understanding verification interviews

## Prevention Strategies

### For Individual Developers

1. **24-Hour Rule**: Sleep before adopting new patterns
2. **Explain It Test**: If you can't explain WHY, don't ship it
3. **External Review**: Get feedback from someone NOT using AI
4. **Refactor Budget**: For every 100 lines added, refactor 25 existing

### For Teams

1. **AGENTS.md**: Communicate expectations to AI tools
2. **PR Size Limits**: Reject PRs over 500 lines
3. **Test Requirements**: No merge without proportional tests
4. **Refactoring Metrics**: Track refactoring % in CI

### For Maintainers

1. **AI Disclosure Policy**: Require disclosure of AI tool usage
2. **Review Time Budget**: Factor AI review overhead into capacity
3. **Slop Detection**: Add automated linguistic analysis
4. **Understanding Gates**: Require explanation of non-trivial changes

## Integration with Existing Skills

### conserve:bloat-detector

New module: `ai-generated-bloat.md`
- Detects AI-specific bloat patterns
- Integrates with existing Tier 1-3 architecture
- Adds slop detection for documentation

### imbue:scope-guard

Enhanced anti-overengineering with agent psychosis warnings:
- Dopamine-driven coding signs
- Sunk cost with AI patterns
- Echo chamber validation warnings

### imbue:proof-of-work

Integration with understanding verification:
- No completion claim without explanation ability
- Evidence of refactoring, not just addition
- Test-driven, not Tab-driven

### imbue:anti-cargo-cult

AI amplification section:
- AI makes cargo cult coding faster and more convincing
- 48% of AI snippets contain exploitable vulnerabilities
- Junior engineer paradox applies to AI

## The Fundamental Insight

The AI coding era has inverted a fundamental software engineering truth:

**Old Truth**: Adding code is easy, maintaining it is hard.
**New Truth**: Adding code is instant, understanding it is impossible.

The solution is not to stop using AI, but to:
1. **Detect** AI-specific bloat patterns
2. **Require** understanding verification
3. **Enforce** refactoring alongside addition
4. **Maintain** external review practices

> "If you don't understand the code, you'll have no clue how to debug it if something goes wrong."

## Sources

### Primary Research
- [Armin Ronacher: Agent Psychosis](https://lucumr.pocoo.org/2026/1/18/agent-psychosis/)
- [GitClear: AI Code Quality 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research)
- [MIT Technology Review: AI Coding Everywhere](https://www.technologyreview.com/2025/12/15/1128352/rise-of-ai-coding-developers-2026/)
- [Sonar: Poor Code Quality Rise](https://www.sonarsource.com/blog/the-inevitable-rise-of-poor-code-quality-in-ai-accelerated-codebases/)
- [Google DORA Report 2025](https://dora.dev/)

### Maintainer Perspectives
- [Socket.dev: OSS Maintainers vs Copilot](https://socket.dev/blog/oss-maintainers-demand-ability-to-block-copilot-generated-issues-and-prs)
- [st0012.dev: AI and Open Source](https://st0012.dev/ai-and-open-source-a-maintainers-take-end-of-2025)
- [OCaml PR Rejection](https://devclass.com/2025/11/27/ocaml-maintainers-reject-massive-ai-generated-pull-request/)
- [Piero.dev: Nuisance of AI](https://piero.dev/2025/06/nuisance-of-ai-on-open-source-maintainers/)

### Vibe Coding Analysis
- [InfoWorld: Vibe Coding Gateway](https://www.infoworld.com/article/4098925/is-vibe-coding-the-new-gateway-to-technical-debt.html)
- [Tabnine: Avoid Debt Tsunami](https://www.tabnine.com/blog/how-to-avoid-vibe-coding-your-way-into-a-tsunami-of-tech-debt/)
- [SashiDo: Vibe Coding Risks](https://www.sashido.io/en/blog/vibe-coding-risks-technical-debt-backend-strategy)
- [Medium: Vibe Coding Debt](https://medium.com/@instatunnel/vibe-coding-debt-the-security-risks-of-ai-generated-codebases-7e3a038edf09)

### Slop Detection
- [Glukhov: Detecting AI Slop](https://www.glukhov.org/post/2025/12/ai-slop-detection/)
- [arXiv: Measuring AI Slop](https://arxiv.org/abs/2509.19163)
- [GitHub: slop-detector](https://github.com/beavis07/slop-detector)

### Refactoring Decline
- [The New Stack: What's Missing? Refactoring](https://thenewstack.io/whats-missing-with-ai-generated-code-refactoring/)
- [LeadDev: AI Code Compounds Debt](https://leaddev.com/technical-direction/how-ai-generated-code-accelerates-technical-debt)
- [VentureBeat: AI Agents Not Production Ready](https://venturebeat.com/ai/why-ai-coding-agents-arent-production-ready-brittle-context-windows-broken)

---

**Maturity Status**: Budding - Will become Evergreen after integration with bloat-detector and field validation.

**Maintenance Notes**: Update quarterly as AI coding landscape evolves rapidly. Track GitClear annual reports for refactoring metrics.
