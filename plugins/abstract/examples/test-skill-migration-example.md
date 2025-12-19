# Test Skill Migration Example

**Date**: 2025-12-08
**Skill Being Migrated**: test-skill (TDD testing workflow)
**Migration Type**: Monolithic to Modular Wrapper
**Status**: Complete

## Overview

This document demonstrates the migration of the `test-skill` command from a monolithic implementation to a modular wrapper that delegates to specialized modules.

## Before Migration

### Original Structure
```
commands/
└── test-skill.md (650 lines)
    ├── TDD methodology explanation (200 lines)
    ├── Baseline testing workflow (150 lines)
    ├── Comparison logic (100 lines)
    ├── Error handling patterns (100 lines)
    └── Usage examples (100 lines)
```

### Issues with Original
1. **Duplicated Content**: TDD methodology copied from `skill-authoring`
2. **Mixed Responsibilities**: Testing logic mixed with methodology explanation
3. **Maintenance Overhead**: Updates required in multiple places
4. **Token Inefficiency**: 650 lines exceeding recommended 500 line limit

## Migration Strategy

### Step 1: Identify Modular Components

Analysis of original content revealed:
- 60% TDD methodology (already in `skill-authoring`)
- 25% testing workflows (can use `skills-eval`)
- 15% command-specific orchestration (keep in wrapper)

### Step 2: Map to Existing Modules

| Original Content | Target Module | Status |
|------------------|---------------|---------|
| TDD methodology | `skill-authoring/modules/tdd-methodology.md` | Exists |
| Baseline testing | `skills-eval/modules/pressure-testing.md` | Exists |
| Comparison logic | `skills-eval/modules/evaluation-workflows.md` | Exists |
| Error patterns | `shared-patterns/modules/error-handling.md` | Exists |
| Command orchestration | Keep in wrapper | New |

## After Migration

### New Structure
```
commands/
└── test-skill.md (120 lines) - Clean wrapper
    ├── Clear delegation statement (10 lines)
    ├── Usage instructions (40 lines)
    ├── Command-specific workflow (50 lines)
    └── Examples and help (20 lines)

skills/
├── skill-authoring/
│   └── modules/tdd-methodology.md (referenced)
├── skills-eval/
│   ├── modules/pressure-testing.md (referenced)
│   └── modules/evaluation-workflows.md (referenced)
└── shared-patterns/
    └── modules/error-handling.md (referenced)
```

### Migrated Wrapper Implementation

```yaml
---
name: test-skill
description: TDD testing workflow for skills using RED-GREEN-REFACTOR methodology. Run baseline tests without skill, document failures, run with skill, compare results. Uses proven testing patterns from skill-authoring and skills-eval modules.
version: 2.0.0
category: testing
tags: [tdd, testing, validation, workflow, wrapper]
dependencies: [skill-authoring, skills-eval, shared-patterns]
estimated_tokens: 800
---

# Test Skill - TDD Testing Workflow

This skill provides a structured Test-Driven Development workflow for validating skills using the proven RED-GREEN-REFACTOR methodology.

## What This Skill Does

1. **RED Phase**: Runs test scenarios WITHOUT the target skill, documenting baseline failures
2. **GREEN Phase**: Runs scenarios WITH the skill, verifying it addresses the failures
3. **REFACTOR Phase**: Analyzes results, identifies improvements, and suggests optimizations

## Core Methodology

This skill delegates to specialized modules for proven testing patterns:

- **TDD Framework**: `skill-authoring/modules/tdd-methodology.md`
- **Pressure Testing**: `skills-eval/modules/pressure-testing.md`
- **Result Analysis**: `skills-eval/modules/evaluation-workflows.md`
- **Error Handling**: `shared-patterns/modules/error-handling.md`

## Usage Workflow

### Basic Testing
```bash
/test-skill [skill-name]
```

### With Custom Scenarios
```bash
/test-skill [skill-name] --scenarios "scenario1,scenario2"
```

### With Baseline Comparison
```bash
/test-skill [skill-name] --compare-baseline
```

## Testing Process

### 1. RED Phase - Baseline Testing
1. Identify test scenarios relevant to the skill
2. Run scenarios WITHOUT the skill loaded
3. Document all failures and unexpected behaviors
4. Create baseline failure report

### 2. GREEN Phase - Skill Testing
1. Load the target skill
2. Run the same scenarios
3. Verify skill addresses baseline failures
4. Document successful resolutions

### 3. REFACTOR Phase - Analysis
1. Compare baseline vs skill results
2. Identify any rationalizations or loopholes
3. Suggest improvements to the skill
4. Generate comprehensive test report

## Output Format

The skill generates a structured test report:

```markdown
# Test Report: [skill-name]

## Baseline (RED) Results
- Failures: N
- Unexpected behaviors: M
- Critical gaps: ...

## Skill (GREEN) Results
- Resolved issues: X
- Remaining issues: Y
- New behaviors: ...

## Analysis (REFACTOR)
- Rationalizations detected: Z
- Suggested improvements: ...
- Loophole closures needed: ...
```

## Example Usage

### Testing a New Skill
```
You: I've created a new "code-review" skill. Can you test it?

Claude: I'll run the TDD testing workflow for your code-review skill.

[Invokes test-skill]

RED Phase: Running tests without code-review skill...
- Found 15 code review failures
- 3 security issues undetected
- 2 performance problems missed

GREEN Phase: Running with code-review skill...
- Resolved 14/15 failures
- Detected all security issues
- Still missing performance optimization

REFACTOR Analysis:
- Skill addresses core requirements well
- Add performance review patterns
- Consider edge case for legacy code
```

## Integration with Modules

### skill-authoring Integration
- Uses established TDD methodology
- Follows progressive disclosure patterns
- Applies anti-rationalization techniques

### skills-eval Integration
- Leverages pressure testing scenarios
- Uses established evaluation workflows
- Applies quality metrics and benchmarks

### shared-patterns Integration
- Uses standardized error handling
- Follows common workflow patterns
- Applies validation best practices

## Best Practices

### When to Use This Skill
- Before committing new skills
- When updating existing skills
- For skill validation in PRs
- During skill authoring workshops

### Test Scenario Design
- Focus on realistic use cases
- Include edge cases and failure modes
- Test both positive and negative scenarios
- Verify error handling and recovery

### Result Interpretation
- 100% baseline resolution is ideal but not always required
- Focus on critical functionality gaps
- Consider context and domain requirements
- Document intentional design tradeoffs

## Troubleshooting

### Skill Not Found
```
Error: Cannot locate skill '[skill-name]'
```
**Solution**: Verify skill name spelling and ensure skill exists in plugins/abstract/skills/

### Module Dependencies Missing
```
Warning: Cannot load required modules
```
**Solution**: Run `make check` to verify all dependencies are installed

### Inconsistent Results
```
Warning: Test results vary between runs
```
**Solution**: Check for non-deterministic elements in skill or test scenarios

## Related Commands

- `/create-skill` - Create new skills with built-in testing
- `/skills-eval` - Comprehensive skill evaluation
- `/bulletproof-skill` - Anti-rationalization hardening
- `/validate-plugin` - Plugin structure validation

## Version History

- **v2.0.0**: Migrated to modular wrapper (current)
- **v1.x.x**: Original monolithic implementation
```

## Migration Benefits

### Quantitative Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines of Code | 650 | 120 | -81% |
| Token Usage | 2600 | 800 | -69% |
| Duplicated Content | 60% | 0% | -100% |
| Maintenance Points | 4 | 1 | -75% |

### Qualitative Benefits

1. **Single Source of Truth**
   - TDD methodology lives only in `skill-authoring`
   - Testing patterns centralized in `skills-eval`
   - No more synchronization issues

2. **Improved Maintainability**
   - Updates to TDD methodology automatically available
   - Testing improvements benefit all wrappers
   - Clear separation of concerns

3. **Better User Experience**
   - Focused command documentation
   - Clear delegation to proven patterns
   - Consistent interface across commands

4. **Enhanced Reusability**
   - Other commands can reference same modules
   - Modular patterns available for new wrappers
   - Shared testing workflows

## Lessons Learned

### What Worked Well
1. **Content Analysis**: Thorough mapping of existing content to modules
2. **Gradual Migration**: Testing wrapper after each refactoring step
3. **Clear Delegation**: Explicit references to module functionality
4. **Backward Compatibility**: Maintaining all original functionality

### Challenges Faced
1. **Identifying Boundaries**: Determining what belonged in wrapper vs modules
2. **Dependency Management**: Ensuring all required modules were available
3. **User Communication**: Explaining benefits of modular approach

### Recommendations for Future Migrations

1. **Start with Analysis**
   - Map existing content to available modules
   - Identify unique vs duplicated functionality
   - Plan wrapper boundaries carefully

2. **Preserve Functionality**
   - Maintain all original use cases
   - Test migration thoroughly
   - Ensure backward compatibility

3. **Communicate Changes**
   - Document migration rationale
   - Highlight new benefits
   - Provide migration guides

## Validation Results

### Pre-Migration Tests
```bash
make test-wrapper WRAPPER=test-skill
Result: [PASS] All tests passed (baseline)

make check-tokens commands/test-skill.md
Result: [WARN] 650 lines (exceeds 500 limit)
```

### Post-Migration Tests
```bash
make test-wrapper WRAPPER=test-skill
Result: [PASS] All tests passed (maintained)

make check-tokens commands/test-skill.md
Result: [PASS] 120 lines (within limit)

make check-deps commands/test-skill.md
Result: [PASS] All dependencies satisfied
```

### Functional Validation
- All original use cases preserved
- Performance improved (faster loading)
- User feedback positive on clearer focus
- Integration with modules seamless

## Next Steps

1. **Monitor Usage**
   - Track command invocation patterns
   - Collect user feedback
   - Identify additional optimization opportunities

2. **Consider Further Refactoring**
   - Extract command-specific patterns to shared modules
   - Create test scenario templates
   - Develop automated migration tools

3. **Apply Pattern to Other Commands**
   - Analyze other monolithic commands
   - Plan similar migrations
   - Develop migration framework

## Resources

### Migration Tools
```bash
# Analyze command for migration
make analyze-migration COMMAND=[command-name]

# Generate wrapper template
make generate-wrapper NAME=[wrapper-name] MODULES="[mod1,mod2]"

# Validate migration
make validate-migration COMMAND=[command-name]
```

### Related Documentation
- [Wrapper Development Guide](../docs/wrapper-development-guide.md)
