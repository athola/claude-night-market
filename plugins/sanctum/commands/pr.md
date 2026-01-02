---
name: pr
description: Enhanced PR preparation that combines Sanctum's workspace review with superpowers:receiving-code-review for detailed PR validation
usage: /pr [--no-code-review] [--reviewer-scope strict|standard|lenient] [destination-file]
extends: "superpowers:receiving-code-review"
---

# Enhanced PR Preparation

Integrates Sanctum's proven PR preparation workflow with superpowers:receiving-code-review to provide detailed validation before creating pull requests.

## Key Features

- **Workspace Validation**: Uses sanctum:git-workspace-review for repository state analysis
- **Quality Gates**: Runs project-specific formatting, linting, and tests
- **Code Review Integration**: uses superpowers:receiving-code-review for automated review
- **Scope Compliance**: Validates changes against branch requirements
- **PR Template Generation**: Creates structured PR descriptions

## When to Use

- Preparing any pull request for merge
- Ensuring quality standards before requesting reviews
- Validating branch scope before PR creation
- Automating PR preparation workflow

## Workflow

### Phase 1: Foundation (Sanctum)

1. **Workspace Review**
   ```bash
   Skill(sanctum:git-workspace-review)
   ```
   - Captures repository status and diffs
   - Identifies staged changes
   - Establishes branch context

2. **Quality Gates**
   ```bash
   # Project-specific commands detected automatically
   make fmt  # or equivalent
   make lint  # or equivalent
   make test  # or equivalent
   ```

### Phase 2: Code Review (Superpowers)

3. **Automated Code Review**
   ```bash
   Skill(superpowers:receiving-code-review)
   ```
   - Reviews staged changes against best practices
   - Identifies potential issues before human review
   - Generates review findings and recommendations

### Phase 3: Synthesis

4. **PR Template Generation**
   - Combines workspace analysis with code review findings
   - Generates detailed PR description
   - Includes quality gates results and review recommendations

## Options

- `--no-code-review`: Skip superpowers code review (faster, less detailed)
- `--reviewer-scope`: Set review strictness (default: standard)
- `destination-file`: Output path for PR description (default: pr_description.md)

## Reviewer Scope Levels

### Strict
- All suggestions must be addressed
- detailed validation
- Suitable for critical code paths

### Standard (Default)
- Balanced approach
- Critical issues must be fixed
- Suggestions are recommendations

### Lenient
- Focus on blocking issues only
- Minimal validation
- Suitable for experimental features

## Output Structure

The generated PR description includes:

```markdown
## Summary
[Brief description of changes]

## Changes
- [Feature] What was implemented
- [Fix] What was resolved
- [Refactor] What was improved

## Code Review Findings
### Critical Issues (0)
### Suggestions (3)
### Observations (2)

## Quality Gates
- [x] Formatting: Passed
- [x] Linting: Passed (2 warnings)
- [x] Tests: Passed (142/142)

## Testing
- Unit tests: New coverage for X module
- Integration tests: Verified API endpoints
- Manual testing: Confirmed CLI behavior

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Error Handling

### Quality Gate Failures
```bash
# If quality gates fail
Error: Linting failed with 3 errors
Run 'make lint' to see details
Fix issues before creating PR
```

### Code Review Findings
```bash
# If critical issues found
Warning: 2 critical issues found in code review
Address these before creating PR:
1. Missing error handling in api.py:45
2. Potential SQL injection in query.py:123
```

## Integration with Existing Workflows

### Backward Compatibility
- `/pr` now includes automated code review
- Use `--no-code-review` to skip the review step when needed
- Gradual adoption remains available

### Enhanced Features
- Automated code quality checks
- Consistent PR descriptions
- Reviewer guidance
- Quality gate reporting

## Integration Benefits

### For Developers
- detailed validation before PR
- Consistent PR descriptions
- Early issue detection
- Streamlined workflow

### For Reviewers
- Better context in PRs
- Pre-validated changes
- Clear issue descriptions
- Focused review areas

### For Teams
- Consistent quality standards
- Automated pre-review checks
- Reduced review cycle time
- Better PR hygiene

## Examples

```bash
# Standard PR preparation with code review
/pr

# Quick PR without automated code review
/pr --no-code-review

# Strict review for critical changes
/pr --reviewer-scope strict

# Custom output location
/pr docs/changes/pr-feature-x.md
```

## Implementation Details

The command orchestrates these skills in sequence:

1. **sanctum:git-workspace-review**
   - Provides repository context
   - Identifies changed files
   - Captures diff statistics

2. **superpowers:receiving-code-review**
   - Reviews code changes
   - Generates findings
   - Provides recommendations

3. **sanctum:pr-prep**
   - Creates PR template
   - Incorporates review findings
   - Generates final description

## Benefits

### For Developers
- detailed validation before PR
- Consistent PR descriptions
- Early issue detection
- Streamlined workflow

### For Reviewers
- Better context in PRs
- Pre-validated changes
- Clear issue descriptions
- Focused review areas

### For Teams
- Consistent quality standards
- Automated pre-review checks
- Reduced review cycle time
- Better PR hygiene

## Migration Notes

- `/pr` is now the enhanced workflow (formerly `/pr-wrapper`).
- `--no-code-review` preserves the previous lightweight behavior.

## Configuration

Add to your project's `.claude/config.md`:

```yaml
pr:
  default_reviewer_scope: "standard"
  quality_gates:
    format_command: "make fmt"
    lint_command: "make lint"
    test_command: "make test"
  output_template: "standard"  # or "detailed", "minimal"
```

## Troubleshooting

### Skill Not Found
```bash
Error: superpowers:receiving-code-review not found
Solution: Install superpowers plugin from superpowers-marketplace
```

### Quality Gate Failures
```bash
Error: Tests failed
Solution: Fix test failures before proceeding
```

### Permission Issues
```bash
Error: Cannot write PR description
Solution: Check file permissions, provide alternative path
```

## Notes

- Requires both sanctum and superpowers plugins
- GitHub CLI (gh) recommended for full functionality
- Supports custom quality gate commands
- Maintains full backward compatibility
