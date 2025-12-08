---
name: conditional-loading
description: Implements progressive loading system for skills to optimize context usage and performance. Use when designing large skills that need chunked loading, implementing progressive disclosure patterns, or reducing token consumption in complex skill architectures.
category: performance-optimization
tags: [conditional-loading, performance, context-optimization, tokens, efficiency]
dependencies: []
tools: []
complexity: intermediate
estimated_tokens: 800
---

# Conditional Loading System for Skills

## Overview

This skill provides a framework for implementing conditional loading of skills content based on user needs and context requirements. It addresses the performance implications of large skills by implementing progressive disclosure and just-in-time loading mechanisms.

### Key Benefits

- **Reduced Context Usage**: Skills load essential content first, with deeper details available on-demand
- **Faster Activation**: Users get immediate value without waiting for full content to load
- **Scalable Architecture**: Supports growing skill libraries without linear context growth
- **Better User Experience**: Progressive disclosure matches how users naturally explore complex topics

## Implementation Strategy

### 1. Tiered Content Structure

```
SKILL.md
├── Frontmatter (metadata, triggers, tools)
├── Quick Start (essential info, ~200 tokens)
├── Core Content (main functionality, ~400 tokens)
├── Advanced Topics (on-demand loading)
└── Resources (references, examples)
```

### 2. Progressive Loading Patterns

#### Pattern A: Essential First
```markdown
## Quick Start

### Essential Information
- **Purpose**: One-sentence description
- **When to Use**: Clear trigger conditions
- **Basic Usage**: 1-2 line example
- **Tools**: List of available tools

<!-- MORE_CONTENT marker -->

## Detailed Information
[Full content loads on-demand]
```

#### Pattern B: Section-Based Loading
```markdown
## Overview
[Essential overview only]

<!-- DETAILED_GUIDE -->
## Implementation Guide
[Loads when user asks "how to implement"]

<!-- ADVANCED_TOPICS -->
## Advanced Patterns
[Loads for complex use cases]
```

### 3. Conditional Loading Triggers

#### Automatic Triggers
- **Keyword Detection**: "how to", "example", "advanced"
- **Question Context**: User asks for specific implementation details
- **Tool Usage**: When user executes skill tools
- **Session Duration**: Load additional content after initial interaction

#### Manual Triggers
- **Explicit Requests**: "tell me more about", "show me examples"
- **Section References**: User mentions specific sections
- **Follow-up Questions**: Indicate need for deeper understanding

## Quick Start Implementation

### 1. Add Loading Markers
```bash
# Add conditional loading markers to existing skills
find skills/ -name "*.md" -exec sed -i 's/^## <!--.*-->$/## <!-- ADVANCED_CONTENT -->/g' {} \;
```

### 2. Create Quick-Start Variants
```bash
# Generate lightweight versions of skills
for skill in skills/*/SKILL.md; do
  skill_dir=$(dirname "$skill")
  skill_name=$(basename "$skill_dir")

  # Claude Code only reads SKILL.md files automatically
  # Use progressive disclosure WITHIN SKILL.md instead:
  # - Keep frontmatter + Quick Start section minimal
  # - Move detailed content to modules/ directory
  # - Reference modules with "See modules/detailed-guide.md"
done
```

- Claude Code only automatically discovers and loads `SKILL.md` files
- Separate files create maintenance burden (need to keep them in sync)
- Better approach: Use progressive disclosure within SKILL.md + modules pattern

### 3. Implement Token Usage Monitoring
```bash
# Monitor token usage before and after optimization
skills/skills-eval/scripts/token-usage-tracker --skill-path skills/ --before-optimization
skills/skills-eval/scripts/token-usage-tracker --skill-path skills/ --after-optimization
```

## When to Use It

**Use this approach when:**
- Skills exceed 800 tokens regularly
- Users complain about slow skill activation
- Context windows are frequently full
- Skills have multiple distinct use cases
- You need to support both quick overview and deep dive scenarios

**Don't use when:**
- Skills are naturally small and focused (<300 tokens)
- All content is essential for basic usage
- Skills have single, simple purpose
- Users always need full content

## Performance Targets

### Token Reduction Goals
- **Quick Start**: <300 tokens (70% reduction)
- **Core Content**: <500 tokens (50% reduction)
- **Full Load**: User-triggered, <1500 tokens total

### Loading Performance
- **Initial Load**: <2 seconds for Quick Start
- **On-Demand Load**: <1 second for additional sections
- **Context Optimization**: 40-60% reduction in average usage

## Validation and Monitoring

### Performance Metrics
```bash
# Track loading performance
skills/skills-eval/scripts/token-usage-tracker --benchmark loading-performance

# Monitor user engagement with progressive loading
skills/skills-eval/scripts/user-engagement-tracker --metric progressive-loading
```

### Quality Assurance
- Quick Start provides sufficient information for basic tasks
- Progressive loading feels natural and unobtrusive
- Full content remains accessible when needed
- No functionality is lost in optimization

## Implementation Examples

### Example 1: Modular Skills Quick Start
```markdown
---
name: modular-skills-quick
description: Design modular skills with reduced initial token load
estimated_tokens: 280
---

# Modular Skills Design (Quick Start)

## Purpose
Break complex skills into focused, maintainable modules.

## When to Use
✅ Creating skills >150 lines
✅ Multiple distinct topics in one skill
✅ Planning skill architecture

## Quick Usage
```bash
# Analyze skill complexity
python scripts/skill_analyzer.py --path skill.md

# Design modules
# Follow guide.md for step-by-step process
```

## Tools Available
- `skill-analyzer`: Complexity analysis
- `token-estimator`: Usage planning
- `module-validator`: Structure validation

<!-- NEED_MORE_DETAIL? -->
<!-- Full content available: implementation patterns, examples, detailed workflows -->
```

### Example 2: Progressive Loading Implementation
```python
# Token usage optimization for conditional loading
def calculate_optimal_load(skill_path, user_context):
    """Calculate optimal content to load based on context"""
    quick_start_tokens = estimate_tokens(skill_path, sections=['quick-start'])
    available_context = get_available_context()

    if available_context < 1000:
        return load_quick_start_only(skill_path)
    elif user_context.get('needs_examples'):
        return load_with_examples(skill_path)
    else:
        return load_full_content(skill_path)
```

## Migration Strategy

### Phase 1: Quick Start Variants
2. Add loading markers to original skills
3. Test token reduction (target: 50-70%)

### Phase 2: Progressive Loading
1. Implement conditional loading logic
2. Add user engagement tracking
3. Optimize loading triggers

### Phase 3: Performance Optimization
1. Monitor actual usage patterns
2. Optimize loading thresholds
3. Fine-tune content boundaries

## Tools and Automation

### Content Analysis
```bash
# Analyze skills for optimization opportunities
python scripts/skill_analyzer.py --path skills/ --optimization-suggestions

# Generate optimization report
skills/skills-eval/scripts/token-usage-tracker --optimization-report skills/
```

### Automated Migration
```bash
# Auto-generate quick-start variants
skills/scripts/quick-start-generator --source skills/ --target skills-quick/

# Add progressive loading markers
skills/scripts/loading-marker-adder --skills skills/ --pattern tiered
```

## Quality Assurance Checklist

- [ ] Quick Start versions contain essential information
- [ ] Loading markers are correctly placed
- [ ] Progressive loading triggers work reliably
- [ ] Token usage reduction meets targets
- [ ] User experience is improved, not degraded
- [ ] Full content remains accessible
- [ ] Performance metrics are positive
- [ ] Documentation is updated

## Monitoring and Maintenance

### Regular Checks
```bash
# Weekly token usage analysis
skills/skills-eval/scripts/token-usage-tracker --weekly-report

# Monthly performance review
skills/skills-eval/scripts/performance-analyzer --monthly
```

### Continuous Optimization
- Monitor user engagement patterns
- Adjust loading thresholds based on usage
- Update content boundaries as skills evolve
- Maintain performance targets over time