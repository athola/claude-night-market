# Cross-Plugin Collaboration Guide

This guide demonstrates how plugins in the Claude Night Market ecosystem work together through shared superpowers to create workflows that combine multiple domain specializations.

## Overview

The Night Market plugin ecosystem is designed for collaboration. Each plugin specializes in a domain and exposes capabilities through skills:

- **Abstract** - Meta-infrastructure for skills, validation, and quality
- **Sanctum** - Git workflows, PR generation, and documentation
- **Scry** - Media generation (VHS terminal recordings, Playwright browser recordings)
- **Conservation** - Context optimization and resource management

## Common Collaboration Patterns

### Pattern 1: Quality Assurance Chain
```
Abstract (TDD/Bulletproofing) -> Sanctum (Quality Gates) -> Production
```
Abstract enforces TDD and skill structure, Sanctum validates before integration.

### Pattern 2: Resource Optimization Loop
```
Conservation (Monitor) -> Abstract (Refactor) -> Conservation (Validate)
```
Conservation identifies issues, Abstract provides patterns to fix them.

### Pattern 3: Automated Workflow Enhancement
```
Sanctum (Detect Need) -> Conservation (Optimize) -> Sanctum (Execute)
```
Sanctum recognizes resource constraints, Conservation optimizes, Sanctum proceeds.

### Pattern 4: Media-Enhanced Documentation
```
Sanctum (Detect Tutorial Need) -> Scry (Generate Media) -> Sanctum (Update Docs)
```
Sanctum identifies documentation gaps, Scry generates GIFs, Sanctum integrates them.

### Pattern 5: Cross-Plugin Dependencies
```yaml
# Skills can depend on other plugins' capabilities
dependencies:
  plugins:
    - conservation:context-optimization
    - sanctum:git-workspace-review
    - abstract:modular-skills
    - scry:vhs-recording
    - scry:gif-generation
```

---

## Two-Plugin Collaborations

### Abstract + Sanctum: Skill-Driven PR Workflow

**Use Case**: Creating and integrating new skills with automated PR generation

#### Workflow Steps

**Step 1: Create and Validate the Skill (Abstract)**
```bash
/abstract:create-skill "my-awesome-skill"
# Creates: skill directory, implementation, tests, documentation
```

**Step 2: Test and Bulletproof (Abstract)**
```bash
/abstract:test-skill my-awesome-skill
/abstract:bulletproof-skill my-awesome-skill
# Validates: best practices, TDD methodology, edge case resistance
```

**Step 3: Estimate Token Usage (Abstract)**
```bash
/abstract:estimate-tokens my-awesome-skill
# Output: skill tokens, dependencies, total impact
```

**Step 4: Generate PR (Sanctum)**
```bash
/sanctum:pr
# Automatically: reviews workspace, runs quality gates, generates PR description
```

#### Generated PR Example
```markdown
## Summary
- Add new `my-awesome-skill` skill for processing workflow data
- Implements TDD methodology with 95%+ test coverage
- Validated through Abstract's skill evaluation framework

## Testing
- Skill validation passed: `/abstract:validate-skill my-awesome-skill`
- TDD workflow passed: `/abstract:test-skill my-awesome-skill`
- Bulletproofing completed: `/abstract:bulletproof-skill my-awesome-skill`
- Project linting passed, all tests passing
```

#### Benefits
- **Quality Assurance**: Abstract validates skills are well-structured and tested
- **Security**: Bulletproofing prevents edge cases and bypass attempts
- **Automation**: Sanctum handles mechanical PR creation
- **Consistency**: Standardized PR format with all necessary information

---

### Conservation + Abstract: Optimizing Meta-Skills

**Use Case**: Reducing context usage of complex evaluation skills without losing functionality

#### Initial Problem
```yaml
# Skill consuming too much context
name: detailed-skill-eval
token_budget: 2500  # Too high!
estimated_tokens: 2300
progressive_loading: false  # Loading everything at once
```

#### Optimization Workflow

**Step 1: Analyze Context Usage (Conservation)**
```bash
/conservation:analyze-growth
# Output: Current context usage: 45% (CRITICAL)
# Top consumer: detailed-skill-eval: 2300 tokens
```

**Step 2: Estimate Token Impact (Abstract)**
```bash
/abstract:estimate-tokens detailed-skill-eval
# Breakdown: Core logic 900, Examples 600, Validation 400, Error handling 300
```

**Step 3: Optimize Context Structure (Conservation)**
```bash
/conservation:optimize-context
# Suggestions: Enable progressive loading, split modules, lazy load examples
```

**Step 4: Refactor with Abstract's Patterns**
```bash
/abstract:analyze-skill detailed-skill-eval
# Provides: Modular decomposition strategy, shared pattern extraction
```

#### Results Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Token Usage | 2300 | 750 | 67% reduction |
| Load Time | 2.3s | 0.8s | 65% faster |
| Memory Usage | 45% | 15% | Within MECW limits |
| Test Coverage | 95% | 95% | Maintained |

#### Optimized Skill Structure
```yaml
name: skill-eval-hub
token_budget: 800  # 65% reduction!
progressive_loading: true
modules:
  - core-eval
  - validation-rules
  - example-library
  - error-handlers
shared_patterns:
  - token-efficient-validation
  - lazy-loading-examples
```

---

### Conservation + Sanctum: Optimized Git Workflows

**Use Case**: Managing multiple large feature branches efficiently

#### Challenge
```bash
# Multiple active branches need processing
- feature/auth-refactor (2,340 files changed)
- feature/performance-boost (1,890 files changed)
- feature/ui-redesign (3,210 files changed)
# Traditional approach would exceed context limits
```

#### Workflow Steps

**Step 1: Analyze Resource Requirements (Conservation)**
```bash
/conservation:optimize-context
# Output: Context Status: CRITICAL (68% usage)
# Available for git operations: 32%
# Recommended: Process branches sequentially with optimization
```

**Step 2: Process Branch with Optimization (Sanctum + Conservation)**
```bash
/git-catchup feature/auth-refactor --context-optimized
# Optimization applied:
# 1. Use summary mode for large diffs
# 2. Progressive loading of file details
# 3. Focus on critical changes only
```

**Step 3: Generate Optimized PR (Sanctum)**
```bash
/sanctum:pr --optimize-context
# Applies: Compressed summaries, token-efficient descriptions, progressive loading
```

#### Performance Comparison

**Without Conservation:**
```
Total context used: 124%
Result: Context overflow, incomplete processing
Success rate: 33% (1/3 branches)
```

**With Conservation:**
```
Total context used: 38%
Result: All branches processed successfully
Success rate: 100% (3/3 branches)
```

#### Advanced Features

**Adaptive Detail Loading**
```bash
Initial PR: 200 tokens (summary only)
/sanctum:show-details src/auth/           # +150 tokens
/sanctum:show-details src/auth/token.js   # +50 tokens
Total: 400 tokens (vs 2,000 without optimization)
```

**Cross-Branch Pattern Recognition**
```bash
# Conservation identifies patterns across branches
# Common changes consolidated into single documentation item
# Estimated savings: 800 tokens
```

---

### Sanctum + Scry: Tutorial Generation Pipeline

**Use Case**: Creating and updating documentation tutorials with animated GIFs

#### Challenge
```bash
# Documentation needs visual demos
- Installation tutorials need terminal recordings
- Web UI guides need browser screen captures
- Combined workflows need multi-source compositions
# Manual process is time-consuming and inconsistent
```

#### Workflow Steps

**Step 1: Identify Tutorial Needs (Sanctum)**
```bash
/sanctum:update-tutorial --list
# Output:
# Available tutorials:
#   quickstart     assets/tapes/quickstart.tape
#   mcp            assets/tapes/mcp.manifest.yaml (terminal + browser)
#   skill-debug    assets/tapes/skill-debug.tape
```

**Step 2: Generate Terminal Recordings (Scry)**
```bash
# Sanctum's tutorial-updates skill orchestrates scry:vhs-recording
Skill(scry:vhs-recording) assets/tapes/quickstart.tape
# VHS processes tape file, generates optimized GIF
# Output: assets/gifs/quickstart.gif (1.2MB)
```

**Step 3: Generate Browser Recordings (Scry)**
```bash
# For web UI tutorials, Playwright captures video
Skill(scry:browser-recording) specs/dashboard.spec.ts
# Output: test-results/dashboard/video.webm

# Convert to optimized GIF
Skill(scry:gif-generation) --input video.webm --output dashboard.gif
# Output: assets/gifs/dashboard.gif (980KB)
```

**Step 4: Compose Multi-Source Tutorials (Scry)**
```bash
# For combined terminal + browser tutorials
Skill(scry:media-composition)
# Reads manifest, combines components
# Output: assets/gifs/mcp-combined.gif
```

**Step 5: Generate Documentation (Sanctum)**
```bash
/sanctum:update-tutorial quickstart mcp
# Sanctum generates dual-tone markdown:
# - docs/tutorials/quickstart.md (project docs, concise)
# - book/src/tutorials/quickstart.md (technical book, detailed)
# - Updates README.md demo section with GIF embeds
```

#### Manifest-Driven Composition
```yaml
# assets/tapes/mcp.manifest.yaml
name: mcp
title: "MCP Server Integration"
components:
  - type: tape
    source: mcp.tape
    output: assets/gifs/mcp-terminal.gif
  - type: playwright
    source: browser/mcp-browser.spec.ts
    output: assets/gifs/mcp-browser.gif
    requires:
      - "npm run dev"  # Start server before recording
combine:
  output: assets/gifs/mcp-combined.gif
  layout: vertical
  options:
    padding: 10
    background: "#1a1a2e"
```

#### Results Comparison

| Metric | Manual | Automated |
|--------|--------|-----------|
| Time per tutorial | 30-60 min | 2-5 min |
| Consistency | Variable | 100% consistent |
| GIF optimization | Often skipped | Always optimized |
| Documentation sync | Often outdated | Always current |

#### Benefits
- **Automation**: End-to-end tutorial generation from tape files
- **Consistency**: All GIFs use same quality settings and themes
- **Dual-Tone Output**: Both project docs and technical book content
- **Manifest-Driven**: Declarative composition for complex tutorials

---

## Three-Way Ecosystem: Complete Development Lifecycle

**Use Case**: End-to-end enterprise plugin development with full optimization

### Phase 1: Planning and Analysis

```bash
# 1. Analyze current resource state (Conservation)
/conservation:analyze-growth
# Output: Context at 25%, optimal for new development

# 2. Plan skill architecture (Abstract)
/abstract:analyze-skill ecosystem-orchestrator
# Output: Recommends modular architecture with 5 interconnected skills

# 3. Check git workspace (Sanctum)
/git-catchup
# Output: Clean workspace, ready for new feature branch
```

### Phase 2: Skill Creation with Built-in Optimization

```bash
# Create orchestrator with Conservation awareness
/abstract:create-skill ecosystem-orchestrator

# Abstract creates with Conservation-suggested limits:
{
  "name": "ecosystem-orchestrator",
  "token_budget": 800,
  "progressive_loading": true,
  "modules": [
    "skill-discovery",
    "dependency-resolution",
    "execution-planning",
    "resource-monitoring"
  ]
}
```

### Phase 3: Development and Testing

```bash
# TDD development cycle for all skills (Abstract)
for skill in ecosystem-orchestrator skill-discovery dependency-resolution; do
  /abstract:test-skill $skill
  /abstract:bulletproof-skill $skill
done

# Conservation monitors and optimizes during development
/conservation:optimize-context
# Output: Applied shared patterns, saved 1,200 tokens total

# Validate entire plugin structure (Abstract)
/abstract:validate-plugin
```

### Phase 4: Integration and Performance Tuning

```bash
# Estimate total impact (Abstract + Conservation)
/abstract:estimate-tokens ecosystem-orchestrator --include-dependencies
# Output: Core 750 tokens, Dependencies 1,100, Total 1,850 (within limits)

# Performance analysis (Conservation)
/conservation:analyze-growth
# Output: Growth pattern optimal, MECW compliant
```

### Phase 5: Documentation and PR Generation

```bash
# Generate detailed PR (Sanctum)
/sanctum:pr --include-performance-report

# Sanctum automatically includes:
# - Change summary
# - Test results from Abstract's testing
# - Performance metrics from Conservation
# - Context optimization details
```

### Real-World Impact

| Metric | Before Integration | After Integration |
|--------|-------------------|-------------------|
| Development time | 2-3 weeks | 3-5 days |
| Quality issues | Frequent, discovered late | Caught early |
| Resource problems | Context overflow common | Eliminated |
| Documentation | Manual, often incomplete | Automatic, detailed |

**Measurable Improvements:**
- Development speed: 70% faster
- Bug reduction: 85% fewer production issues
- Resource efficiency: 42% less token usage
- Documentation quality: 100% compliance with standards

---

## Integration Techniques

### Shared State Management
```bash
# Conservation sets context budget
export CONTEXT_BUDGET=0.4

# Abstract respects budget in skill creation
/abstract:create-skill my-skill --context-limit $CONTEXT_BUDGET

# Sanctum generates PRs within budget
/sanctum:pr --respect-context-limit
```

### Progressive Loading Framework
```python
# Conservation provides framework
def progressive_load(module, priority):
    if context_available():
        load_module(module, priority)
    else:
        queue_for_later(module)

# Abstract implements for skills
# Sanctum implements for git operations
```

### Quality Gates Integration
```yaml
quality_gates:
  - abstract:validate-skill
  - abstract:test-skill
  - sanctum:lint-check
  - sanctum:security-scan
```

---

## Measuring Collaboration Success

### Development Metrics
- **Speed**: Time from idea to production
- **Quality**: Bug rates and test coverage
- **Consistency**: Code style and pattern adherence
- **Documentation**: Completeness and accuracy

### Resource Metrics
- **Context Usage**: Token consumption optimization
- **Performance**: Response times and throughput
- **Scalability**: Concurrent operation capacity
- **Efficiency**: Resource utilization percentage

### Collaboration Metrics
- **Interoperability**: How well plugins work together
- **Integration**: Clean handoffs between plugins
- **Flexibility**: Ability to adapt to different scenarios
- **Maintainability**: Long-term sustainability

---

## Commands Reference

### Abstract Commands
- `/abstract:create-skill` - Create new skill with proper structure
- `/abstract:test-skill` - Run TDD validation workflow
- `/abstract:bulletproof-skill` - Harden skill against edge cases
- `/abstract:estimate-tokens` - Calculate context impact
- `/abstract:analyze-skill` - Get optimization recommendations
- `/abstract:validate-plugin` - validate quality after optimization

### Sanctum Commands
- `/git-catchup` - Efficient git branch analysis
- `/sanctum:pr` - Generate detailed PR description
- `/sanctum:show-details <path>` - Progressive detail loading
- `/sanctum:update-tutorial` - Generate tutorials with media (uses Scry)

### Conservation Commands
- `/conservation:analyze-growth` - Monitor resource usage trends
- `/conservation:optimize-context` - Apply MECW optimization principles

### Scry Commands
- `/scry:record-terminal` - Record terminal sessions using VHS tape files
- `/scry:record-browser` - Record browser sessions using Playwright specs

---

## Key Takeaways

1. **Synergy Over Silos**: Plugins working together create more value than separate usage
2. **Complementary Strengths**: Each plugin specializes in a domain, combined they cover the development lifecycle
3. **Adaptive Workflows**: Collaboration enables workflows that adapt to constraints
4. **Quality at Scale**: Maintain high quality even with complex, multi-plugin workflows
5. **Resource Efficiency**: Optimize for both development speed and operational cost

The Claude Night Market ecosystem is designed for collaboration. Combining plugin superpowers creates workflows that are efficient and maintainable by composing specialized capabilities.

## See Also

- [Superpowers Integration](../reference/superpowers-integration.md) - Technical skill integration details
- [Plugin Overview](../plugins/README.md) - Creating new plugins
- [Skills Reference](../reference/capabilities-skills.md) - Skill workflow patterns
