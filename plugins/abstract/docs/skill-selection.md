# Meta-Skills Technical Reference

## Overview

The Abstract plugin provides a meta-skills framework for Claude Code, enabling structured skill development, evaluation, and optimization. This documentation describes the capabilities and architecture of each meta-skill.

## Meta-Skill Architecture

### Modular Skills (`modular-skills`)

**Purpose:** Design patterns and architectural frameworks for skill development.

**Core Capabilities:**
- Hub-and-spoke architecture implementation
- Progressive disclosure patterns
- Token optimization through modularization
- Dependency management and validation
- Module boundary definition

**Technical Components:**
```
modular-skills/
├── SKILL.md              # Hub with metadata and overview
├── guide.md              # Implementation guide
├── modules/              # Focused architectural modules
│   ├── core-workflow.md
│   ├── implementation-patterns.md
│   └── antipatterns-and-migration.md
├── scripts/              # Analysis and validation tools
│   ├── skill-analyzer
│   ├── module-validator
│   └── token-estimator
└── examples/             # Reference implementations
```

**Scripts:**
- `skill_analyzer.py`: Analyzes skill structure and provides modularization recommendations
- `abstract_validator.py`: Validates module dependencies and structure compliance
- `token_estimator.py`: Estimates token usage and optimization opportunities

**Use Cases:**
- Designing new skills with >150 lines of content
- Refactoring monolithic skills into modular architecture
- Token budget optimization
- Architectural reviews

**Not Intended For:** Quality evaluation of existing skills (use `skills-eval` instead)

---

### Skills Evaluation (`skills-eval`)

**Purpose:** Comprehensive quality assessment and improvement framework for existing skills.

**Core Capabilities:**
- Skill discovery and cataloging
- Quality metric assessment
- Improvement recommendation generation
- Compliance validation
- Performance benchmarking

**Technical Components:**
```
skills-eval/
├── SKILL.md              # Hub with metadata
├── modules/              # Evaluation frameworks
│   ├── quality-metrics.md
│   ├── improvement-strategies.md
│   └── compliance-standards.md
└── scripts/              # Evaluation tools
    ├── skills-auditor
    ├── improvement-suggester
    ├── compliance-checker
    └── tool-performance-analyzer
```

**Scripts:**
- `skills_auditor.py`: Discovers and analyzes skills across directories
- `improvement_suggester.py`: Generates actionable improvement recommendations
- `compliance_checker.py`: Validates skills against standards
- `tool_performance_analyzer.py`: Benchmarks tool execution and efficiency

**Quality Metrics:**
- Structure compliance (25%)
- Content quality (25%)
- Token efficiency (20%)
- Activation reliability (20%)
- Script integration (10%)

**Use Cases:**
- Systematic quality assessment of skill libraries
- Generating improvement roadmaps
- Standards compliance validation
- Performance optimization

**Not Intended For:** Initial skill architecture design (use `modular-skills` instead)

---

### Writing Standards (`writing-clearly-and-concisely`)

**Purpose:** Prose quality and clarity standards for human-readable content.

**Core Capabilities:**
- Strunk & White writing principles
- Technical documentation standards
- Conciseness patterns
- Active voice guidance

**Use Cases:**
- Documentation and README files
- Commit messages and PR descriptions
- Error messages and UI copy
- Technical explanations

**Not Intended For:** Code architecture, system design, or technical implementation planning

---

## Integration Patterns

### Typical Workflow

1. **Skill Creation** (`modular-skills`)
   ```bash
   # Design architecture
   python scripts/skill_analyzer.py --path new-skill.md --suggest-modules

   # Estimate token budget
   python scripts/token_estimator.py --target 600 --modules 3

   # Validate structure
   python scripts/abstract_validator.py --skill-path new-skill/
   ```

2. **Quality Assessment** (`skills-eval`)
   ```bash
   # Discover skills
   python skills/skills-eval/scripts/skills_auditor.py --discover --path skills/

   # Generate improvements
   python skills/skills-eval/scripts/improvement_suggester.py --skill new-skill/SKILL.md

   # Check compliance
   python skills/skills-eval/scripts/compliance_checker.py --skill new-skill/SKILL.md
   ```

3. **Content Refinement** (`writing-clearly-and-concisely`)
   - Apply to documentation, guides, and user-facing content
   - Focus on clarity, conciseness, and active voice

### Cross-Skill Script Usage

Some scripts appear in multiple skills but serve different purposes:

| Script | In `modular-skills` | In `skills-eval` |
|--------|-------------------|-----------------|
| `skill-analyzer` | Architecture analysis | N/A |
| `skills-auditor` | N/A | Quality assessment |
| `token-estimator` | Design planning | N/A |
| `token-usage-tracker` | N/A | Usage analysis |

---

## Technical Decision Matrix

| Scenario | Meta-Skill | Primary Script |
|----------|-----------|---------------|
| New skill design | `modular-skills` | `skill-analyzer` |
| Modularization planning | `modular-skills` | `token-estimator` |
| Structure validation | `modular-skills` | `module-validator` |
| Quality assessment | `skills-eval` | `skills-auditor` |
| Improvement planning | `skills-eval` | `improvement-suggester` |
| Standards validation | `skills-eval` | `compliance-checker` |
| Performance analysis | `skills-eval` | `tool-performance-analyzer` |
| Documentation writing | `writing-clearly-and-concisely` | N/A |

---

## Architecture Principles

### Hub-and-Spoke Pattern
- Central hub (`SKILL.md`) provides metadata and overview
- Spoke modules contain focused, specialized content
- Progressive disclosure minimizes token usage
- Maximum 2-level dependency depth

### Token Optimization
- Hub loading: 30-50 tokens
- Module loading: 100-300 tokens per module
- Target reduction: 30-50% compared to monolithic design
- Lazy loading of detailed content

### Script Integration
- All scripts executable via command line
- Consistent argument patterns (`--help`, `--path`, `--output`)
- Clear error messages and exit codes
- Self-contained with explicit dependencies

---

## Implementation Guidelines

### Creating Modular Skills
1. Use `skill-analyzer` to assess scope and complexity
2. Design module boundaries based on usage patterns
3. Validate with `module-validator` for structure compliance
4. Estimate tokens with `token-estimator`

### Evaluating Skills
1. Run `skills-auditor` for initial assessment
2. Generate recommendations with `improvement-suggester`
3. Validate compliance with `compliance-checker`
4. Benchmark performance with `tool-performance-analyzer`

### Quality Standards
- Frontmatter completeness
- Dependency availability
- Script functionality
- Token usage accuracy
- Content clarity and conciseness

---

## References

- Modular Skills Guide: `skills/modular-skills/guide.md`
- Skills Eval Guide: `skills/skills-eval/README.md`
- Writing Standards: `writing-clearly-and-concisely/SKILL.md`
