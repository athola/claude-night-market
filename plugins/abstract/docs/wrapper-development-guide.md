# Wrapper Development Guide

**Date**: 2025-12-08
**Version**: 1.0.0
**Target Audience**: Plugin developers migrating from monolithic skills to modular wrappers

## Overview

This guide explains how to create wrapper skills that leverage the modular skills architecture. Wrappers provide a clean interface to complex functionality while maintaining the benefits of modular design.

## What is a Wrapper Skill?

A wrapper skill is a lightweight SKILL.md file that:
- Delegates implementation to modular skills
- Provides a focused, domain-specific interface
- Maintains backward compatibility
- Reduces code duplication

## Wrapper Structure

### Basic Wrapper Template

```yaml
---
name: your-wrapper-skill
description: Brief description focused on user benefit (≤1024 chars)
version: 1.0.0
category: appropriate-category
tags: [wrapper, delegation, modular]
dependencies: [modular-skills, shared-patterns]
estimated_tokens: 800
---
```

### Essential Components

1. **Clear Delegation Statement**
   ```markdown
   This skill delegates to [specific-modular-skill] for core functionality.
   ```

2. **Focused Scope**
   - Domain-specific language
   - Targeted use cases
   - Simplified interface

3. **Dependency Management**
   - Always include `modular-skills` as base dependency
   - Add specific module dependencies
   - Version pinning for stability

## Creating a Wrapper

### Step 1: Identify Core Functionity

Determine which existing modular skills provide the needed functionality:

- `skill-authoring` - For creating new skills
- `skills-eval` - For evaluation and analysis
- `modular-skills` - For migration and refactoring
- `shared-patterns` - For common workflows

### Step 2: Create Wrapper Directory

```bash
mkdir -p plugins/abstract/skills/your-wrapper-skill
cd plugins/abstract/skills/your-wrapper-skill
```

### Step 3: Write SKILL.md

Key considerations:
- Keep under 500 lines
- Focus on the "what" not the "how"
- Include clear usage examples
- Reference underlying modules

### Step 4: Add Optional Modules

Only add modules if the wrapper needs:
- Custom validation rules
- Domain-specific examples
- Specialized workflows
- Integration patterns

## Wrapper Patterns

### 1. Direct Delegation

Simplest pattern - delegates entirely to one modular skill:

```markdown
This skill uses [skill-authoring] to guide you through creating effective skills.

To use this skill:
1. Invoke the skill directly
2. Follow the guided workflow
3. Let skill-authoring handle the implementation

The skill-authoring module provides:
- TDD methodology guidance
- Progressive disclosure patterns
- Anti-rationalization techniques
```

### 2. Composite Wrapper

Combines multiple modular skills:

```markdown
This skill orchestrates multiple modules to provide comprehensive analysis:

1. **Discovery Phase** - Uses [skills-eval] for baseline assessment
2. **Implementation Phase** - Uses [skill-authoring] for creation
3. **Validation Phase** - Uses [skills-eval] for quality checks

Key modules involved:
- skills-eval/modules/evaluation-workflows.md
- skill-authoring/modules/tdd-methodology.md
- shared-patterns/modules/validation-patterns.md
```

### 3. Domain-Specific Wrapper

Adds domain knowledge to general functionality:

```markdown
This skill adapts [modular-skills] patterns specifically for API development:

API-Specific Considerations:
- Endpoint documentation requirements
- Authentication pattern handling
- Rate limiting considerations
- Error response standards

Uses these modules:
- modular-skills/modules/implementation-patterns.md
- shared-patterns/modules/workflow-patterns.md
- Custom API guidelines in modules/api-specific.md
```

## Best Practices

### DO
- ✅ Keep wrappers focused and simple
- ✅ Always declare dependencies
- ✅ Use clear delegation language
- ✅ Provide domain-specific context
- ✅ Include usage examples
- ✅ Maintain token efficiency

### DON'T
- ❌ Duplicate module functionality
- ❌ Create deep dependency chains
- ❌ Override module behavior without clear reason
- ❌ Include implementation details
- ❌ Make wrappers overly complex

## Migration Examples

### From Monolithic to Wrapper

**Before (Monolithic)**:
```yaml
---
name: complex-analysis-skill
description: Performs comprehensive analysis including evaluation, creation, and validation...
dependencies: []
---
# 500+ lines of implementation
# Duplicated evaluation logic
# Inline TDD methodology
# Custom validation rules
```

**After (Wrapper)**:
```yaml
---
name: complex-analysis-skill
description: Performs comprehensive analysis using proven modular patterns
dependencies: [skills-eval, skill-authoring, shared-patterns]
estimated_tokens: 300
---
# Delegates to skills-eval for analysis
# Uses skill-authoring for creation workflow
# Leverages shared-patterns for validation
# Domain-specific guidance only
```

## Testing Wrappers

### Validation Checklist

1. **Dependency Resolution**
   ```bash
   # Verify all dependencies exist
   make check-dependencies
   ```

2. **Token Efficiency**
   ```bash
   # Check token usage
   make check-tokens skills/your-wrapper-skill
   ```

3. **Functional Testing**
   ```bash
   # Test wrapper functionality
   make test-wrapper WRAPPER=your-wrapper-skill
   ```

### Test Scenarios

1. **Basic Delegation**
   - Verify wrapper correctly invokes module
   - Check error handling for missing modules
   - Validate output formatting

2. **Dependency Management**
   - Test with missing dependencies
   - Verify version compatibility
   - Check circular dependency prevention

3. **User Experience**
   - Validate clarity of delegation
   - Check example accuracy
   - Verify help text completeness

## Common Pitfalls

### 1. Wrapper Bloat
**Problem**: Wrapper grows too complex, becomes monolithic again
**Solution**: Regular refactoring, move domain logic to modules

### 2. Dependency Hell
**Problem**: Too many or conflicting dependencies
**Solution**: Use shared-patterns for common functionality

### 3. Unclear Delegation
**Problem**: Users don't understand what the wrapper does
**Solution**: Clear documentation, explicit module references

### 4. Version Drift
**Problem**: Wrapper expects different module versions
**Solution**: Pin dependency versions, regular updates

## Troubleshooting

### Module Not Found
```bash
Error: Cannot find module 'specific-module'
```
**Solution**: Check module exists, verify path, update dependency list

### Token Overrun
```bash
Warning: Wrapper exceeds 500 line limit
```
**Solution**: Refactor to modules, reduce inline content

### Circular Dependency
```bash
Error: Circular dependency detected
```
**Solution**: Review dependency tree, extract to shared-patterns

## Maintenance

### Regular Tasks

1. **Dependency Updates**
   - Monthly review of module versions
   - Test with latest module updates
   - Update pinned versions

2. **Token Optimization**
   - Quarterly token usage review
   - Refactor bloated sections
   - Remove outdated content

3. **User Feedback**
   - Collect wrapper usage patterns
   - Identify common issues
   - Improve documentation

### Evolution Path

1. **Start Simple** - Basic delegation wrapper
2. **Add Value** - Domain-specific enhancements
3. **Optimize** - Token efficiency and performance
4. **Mature** - Stable, well-documented interface

## Resources

### Related Documentation
- [Modular Skills Architecture](../architecture/modular-skills.md)
- [Skill Authoring Guide](../skills/skill-authoring/SKILL.md)
- [Shared Patterns Reference](../skills/shared-patterns/SKILL.md)
- [Skills Evaluation Framework](../skills/skills-eval/SKILL.md)

### Tools and Commands
```bash
# Create new wrapper template
make create-wrapper NAME=your-wrapper-skill

# Validate wrapper structure
make validate-wrapper WRAPPER=your-wrapper-skill

# Test wrapper functionality
make test-wrapper WRAPPER=your-wrapper-skill

# Check wrapper dependencies
make check-deps WRAPPER=your-wrapper-skill
```

### Examples
- [API Development Wrapper](../examples/api-wrapper.md)
- [Testing Workflow Wrapper](../examples/testing-wrapper.md)
- [Documentation Generation Wrapper](../examples/docs-wrapper.md)