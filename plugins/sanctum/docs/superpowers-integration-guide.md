# Sanctum × Superpowers Integration Guide

**Date**: 2025-12-08
**Version**: 1.0.0
**Target**: Phase 2 Task 1 - Plugin Superpowers Linking Project

## Overview

This guide documents the enhanced command patterns (formerly wrappers) created to integrate Sanctum's PR workflow capabilities with `superpowers:receiving-code-review`. The commands maintain backward compatibility while adding enhanced code review automation and quality validation.

## Enhanced Command Architecture

### Design Principles

1. **Backward Compatibility**: Original Sanctum commands remain functional
2. **Progressive Enhancement**: Superpowers capabilities are additive, not replacements
3. **Clear Delegation**: Wrappers explicitly delegate to superpowers for code review
4. **Sanctum Extensions**: Preserve Sanctum's unique GitHub integrations and scope validation

### Enhanced Command Pattern Structure

Each command follows this consistent pattern:

```yaml
---
name: <command>
description: Enhanced <command> that combines Sanctum's <feature> with superpowers:receiving-code-review
extends: "superpowers:receiving-code-review"
---
```

## Implemented Enhanced Commands

### 1. `/pr` - Enhanced PR Preparation

**File**: `/commands/pr.md`

**Purpose**: Combines PR preparation workflow with automated code review

**Key Features**:
- Workspace validation via `sanctum:git-workspace-review`
- Quality gate execution (format, lint, test)
- Code review integration via `superpowers:receiving-code-review`
- Structured PR template generation with review findings

**Extension Points**:
- `--no-code-review`: Skip superpowers integration for speed
- `--reviewer-scope`: Adjust review strictness (strict/standard/lenient)
- Custom output destinations for PR descriptions

**Workflow**:
1. Analyze repository state (Sanctum)
2. Run quality gates (Sanctum)
3. Perform code review (Superpowers)
4. Generate detailed PR description (Command synthesis)

### 2. `/fix-pr` - Enhanced PR Fix Automation

**File**: `/commands/fix-pr.md`

**Purpose**: Systematically address PR review comments with intelligent fix generation

**Key Features**:
- Intelligent comment triage (Critical/In-Scope/Suggestion/Backlog)
- Superpowers-powered fix suggestions
- GitHub thread resolution automation
- Batch fix operations
- Backlog item creation for out-of-scope feedback

**Extension Points**:
- `--dry-run`: Preview fixes without applying
- `--commit-strategy`: Choose commit approach (single/separate/manual)
- PR targeting by number or URL

**Workflow**:
1. Fetch review comments (Sanctum GitHub integration)
2. Analyze with superpowers for fix suggestions
3. Classify comments by impact and scope
4. Apply fixes systematically
5. Resolve GitHub threads automatically

### 3. `/pr-review` - Enhanced PR Review

**File**: `/commands/pr-review.md`

**Purpose**: Scope-aware code review that validates against requirements

**Key Features**:
- Scope baseline establishment from plan/spec artifacts
- Requirements compliance validation
- Superpowers detailed code analysis
- Structured finding classification
- Automated GitHub issue creation for backlog items

**Extension Points**:
- `--scope-mode`: Set validation strictness (strict/standard/flexible)
- `--auto-approve-safe-prs`: Auto-approve PRs with no issues
- `--create-backlog-issues`: Track improvements as GitHub issues

**Workflow**:
1. Establish scope from artifacts (Sanctum)
2. Perform code review (Superpowers)
3. Triage findings against scope (Wrapper)
4. Generate structured report (Wrapper)
5. Create backlog items (Optional)

## Integration Benefits

### For Developers

**Enhanced Workflow**:
- Early detection of issues before PR creation
- Automated fix suggestions for review feedback
- Clear understanding of PR scope and requirements
- Consistent PR descriptions and formatting

**Quality Improvements**:
- detailed code quality checks
- Security vulnerability scanning
- Performance impact assessment
- Best practices validation

### For Reviewers

**Efficiency Gains**:
- Pre-validated changes reduce review time
- Clear classification of findings by priority
- Focused review areas based on scope
- Consistent feedback format

**Better Context**:
- Scope baseline clearly established
- Requirements traceability maintained
- Out-of-scope suggestions properly routed
- Quality metrics provided

### For Teams

**Process Improvements**:
- Consistent review standards across team
- Automated quality gates
- Reduced review cycle time
- Better technical debt tracking

**Quality Assurance**:
- Scope creep prevention
- Requirements compliance validation
- detailed security checks
- Performance regression detection

## Technical Implementation

### Dependency Management

```yaml
dependencies:
  # Sanctum skills (existing)
  - sanctum:git-workspace-review
  - sanctum:pr-prep
  - sanctum:pr-review
  - sanctum:shared

  # Superpowers integration
  - superpowers:receiving-code-review
```

### Skill Orchestration

The commands implement a consistent orchestration pattern:

1. **Foundation Phase**: Sanctum provides context and workflow
2. **Analysis Phase**: Superpowers performs deep code analysis
3. **Synthesis Phase**: Wrapper combines insights into actionable output

### Error Handling

Each command implements production-grade error handling:

```yaml
# Superpowers not available
fallback_to_sanctum_mode: true

# GitHub API issues
graceful_degradation: true

# Analysis failures
manual_review_mode: true
```

## Migration Guide

### For Existing Users

**Gradual Adoption Path**:
1. Continue using original commands (`/pr`, `/fix-pr`, `/pr-review`)
2. Try the enhanced command with `--dry-run` to preview enhancements
3. Adopt enhanced features progressively
4. Full migration when comfortable

**Backward Compatibility**:
- All original commands remain functional
- Wrapper features are additive, not breaking
- Configuration can be incremental

### For New Projects

**Recommended Starting Points**:
```bash
# New PR workflow
/pr

# Addressing review feedback
/fix-pr

# Code review process
/pr-review --scope-mode standard --create-backlog-issues
```

## Configuration

### Project-Level Settings

Add to `.claude/config.md`:
```yaml
sanctum_superpowers:
  default_reviewer_scope: "standard"
  auto_create_backlog_issues: true
  quality_gates:
    require_tests: true
    min_coverage: 80
    security_scan: true
```

### User Preferences

```yaml
personal_settings:
  commit_strategy: "single"
  scope_mode: "standard"
  auto_approve_safe: true
```

## Testing and Validation

### Integration Tests

Run the provided test suite:
```bash
cd plugins/sanctum
python3 test-wrapper-integration.py
```

### Test Coverage

- Wrapper file structure validation
- Frontmatter compliance checks
- Required section presence
- Dependency verification
- Backward compatibility confirmation

## Future Enhancements

### Planned Features

1. **Additional Superpowers Integration**
   - `superpowers:systematic-debugging` for complex issue resolution
   - `superpowers:defense-in-depth` for security-focused reviews

2. **Advanced Workflow Automation**
   - CI/CD pipeline integration
   - Automated PR status updates
   - Smart reviewer assignment

3. **Enhanced Analytics**
   - Review time tracking
   - Quality metrics dashboard
   - Technical debt visualization

### Extension Points

The enhanced-command architecture supports easy extension:
- New superpowers skills can be added as dependencies
- Custom Sanctum integrations preserved
- Additional workflow steps can be inserted

## Troubleshooting

### Common Issues

**Superpowers Plugin Not Found**:
```bash
# Install from superpowers-marketplace
claude plugin install superpowers-marketplace
claude plugin install superpowers
```

**GitHub API Limits**:
- Use `--dry-run` mode for testing
- Implement retry logic for rate limits
- Cache results where possible

**Performance Concerns**:
- Use `--no-code-review` for faster operation
- Implement incremental analysis
- Cache quality gate results

## Resources

### Documentation
- [Wrapper Development Guide](../../abstract/docs/wrapper-development-guide.md)
- [Sanctum Plugin Documentation](../README.md)
- [Superpowers Documentation](https://github.com/superpowers-marketplace/docs)

### Support
- Issues: Create in respective plugin repositories
- Discussions: GitHub Discussions for each plugin
- Examples: See `/examples/` directories

---

**Summary**: The Sanctum × Superpowers integration successfully creates enhanced PR workflows that combine the best of both plugins while maintaining full backward compatibility. The enhanced command pattern provides a clean architecture for future integrations and extensions.
