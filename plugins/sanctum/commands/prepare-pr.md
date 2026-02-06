---
name: prepare-pr
aliases: [pr]
description: Complete PR preparation - updates documentation, dogfooding, README, tests, then validates with code review
usage: /prepare-pr [--no-code-review] [--reviewer-scope strict|standard|lenient] [--skip-updates] [destination-file]
extends: "superpowers:receiving-code-review"

# Claude Code 2.1.0+ lifecycle hooks
hooks:
  PreToolUse:
    - matcher: "Skill|Task"
      command: |
        # Log PR preparation start with options
        echo "[cmd:prepare-pr] PR preparation started at $(date) | User: ${USER:-unknown}" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        # Track code review option (important for quality metrics)
        if echo "$CLAUDE_TOOL_INPUT" | grep -q "no-code-review"; then
          echo "[cmd:prepare-pr] ⚠️  Option: --no-code-review (automated review SKIPPED)" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
        # Track reviewer scope
        if echo "$CLAUDE_TOOL_INPUT" | grep -q "reviewer-scope"; then
          scope=$(echo "$CLAUDE_TOOL_INPUT" | grep -oP 'reviewer-scope["\s:=]+\K\w+')
          echo "[cmd:prepare-pr] Reviewer scope: ${scope:-standard}" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
        # Track update skip option
        if echo "$CLAUDE_TOOL_INPUT" | grep -q "skip-updates"; then
          echo "[cmd:prepare-pr] ⚠️  Option: --skip-updates (documentation updates SKIPPED)" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
      once: true
  PostToolUse:
    - matcher: "Bash"
      command: |
        # Log quality gate execution
        if echo "$CLAUDE_TOOL_INPUT" | grep -qE "(make|npm|cargo) (test|lint|fmt|build)"; then
          cmd=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // empty' 2>/dev/null || echo 'N/A')
          echo "[cmd:prepare-pr] ✓ Quality gate executed: $cmd" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        fi
  Stop:
    - command: |
        echo "[cmd:prepare-pr] === PR preparation completed at $(date) ===" >> ${CLAUDE_CODE_TMPDIR:-/tmp}/command-audit.log
        # Could push to PR metrics dashboard
---

# Complete PR Preparation Workflow

Orchestrates the full PR preparation workflow by running documentation updates, dogfooding checks, README updates, and test reviews before validating with code review. This is the "one command to prepare everything" before submitting a PR.

## Key Features

- **Documentation Updates**: Runs `/sanctum:update-docs` to sync documentation
- **Dogfooding Checks**: Runs `/abstract:make-dogfood` to update Makefile demonstrations
- **README Sync**: Runs `/sanctum:update-readme` to keep README current
- **Test Coverage**: Runs `/sanctum:update-tests` to review test quality
- **Workspace Validation**: Uses sanctum:git-workspace-review for repository state analysis
- **Quality Gates**: Runs project-specific formatting, linting, and tests
- **Code Review Integration**: uses superpowers:receiving-code-review for automated review
- **Scope Compliance**: Validates changes against branch requirements
- **PR Template Generation**: Creates structured PR descriptions

## When To Use

- **Before every PR**: Complete preparation workflow
- **Feature completion**: Ensures all documentation and tests are current
- **Governance compliance**: Follows Mandatory Post-Implementation Protocol
- **Quality assurance**: Full validation before requesting reviews

## When NOT To Use

- Simple changes that don't need the full workflow
- Work already completed through another sanctum command

## Workflow

### Phase 0: Pre-Flight Updates (NEW)

Unless `--skip-updates` is specified:

1. **Update Documentation**
   ```bash
   /sanctum:update-docs
   ```
   - Syncs technical documentation
   - Updates guides and references
   - Ensures documentation completeness

2. **Update Makefile Dogfooding**
   ```bash
   /abstract:make-dogfood
   ```
   - Updates Makefile demonstration targets
   - Ensures Makefile reflects current features
   - Validates make targets work correctly

3. **Update README**
   ```bash
   /sanctum:update-readme
   ```
   - Syncs README with new features
   - Updates command listings
   - Refreshes examples and usage

4. **Update Tests**
   ```bash
   /sanctum:update-tests
   ```
   - Reviews test coverage
   - Identifies missing tests
   - Validates test quality

### Phase 1: Foundation (Sanctum)

5. **Workspace Review**
   ```bash
   Skill(sanctum:git-workspace-review)
   ```
   - Captures repository status and diffs
   - Identifies staged changes
   - Establishes branch context

6. **Quality Gates**
   ```bash
   # Project-specific commands detected automatically
   make fmt  # or equivalent
   make lint  # or equivalent
   make test  # or equivalent
   ```

### Phase 2: Code Review (Superpowers)

7. **Automated Code Review**
   ```bash
   Skill(superpowers:receiving-code-review)
   ```
   - Reviews staged changes against best practices
   - Identifies potential issues before human review
   - Generates review findings and recommendations

### Phase 3: Synthesis

8. **PR Template Generation**
   - Combines workspace analysis with code review findings
   - Generates detailed PR description
   - Includes quality gates results and review recommendations
   - Verifies content quality via `scribe:slop-detector` principles
   - Applies `scribe:doc-generator` guidelines to avoid AI-sounding text

## Options

- `--skip-updates`: Skip documentation/dogfooding/README/test updates (Phase 0)
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

## Documentation & Tests
- [x] Documentation updated
- [x] Makefile dogfooding updated
- [x] README synchronized
- [x] Test coverage reviewed

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

### Update Command Failures
```bash
# If documentation update fails
Warning: /sanctum:update-docs failed
You may need to update documentation manually
Continuing with PR preparation...
```

## Integration with Existing Workflows

### Backward Compatibility
- `/pr` now aliases to `/prepare-pr` with full update workflow
- Use `--skip-updates` to get previous behavior (skip Phase 0)
- Use `--no-code-review` to skip the review step when needed
- Gradual adoption remains available

### Governance Compliance
This command implements the **Mandatory Post-Implementation Protocol**:
- `/sanctum:update-docs` - Update project documentation
- `/abstract:make-dogfood` - Update Makefile demonstration targets
- `/sanctum:update-readme` - Update README with new features
- `/sanctum:update-tests` - Review and update test coverage

## Integration Benefits

### For Developers
- Single command for complete PR preparation
- Automated governance compliance
- detailed validation before PR
- Consistent PR descriptions
- Early issue detection
- Streamlined workflow

### For Reviewers
- Better context in PRs
- Pre-validated changes
- Clear issue descriptions
- Focused review areas
- Documentation already updated

### For Teams
- Consistent quality standards
- Automated pre-review checks
- Reduced review cycle time
- Better PR hygiene
- Enforced documentation updates

## Examples

```bash
# Full PR preparation (recommended)
/prepare-pr

# Also works as /pr (alias)
/pr

# Quick PR without updates (legacy behavior)
/prepare-pr --skip-updates

# Skip both updates and code review (fastest)
/prepare-pr --skip-updates --no-code-review

# Strict review for critical changes
/prepare-pr --reviewer-scope strict

# Custom output location
/prepare-pr docs/changes/pr-feature-x.md
```

## Implementation Details

The command orchestrates these commands/skills in sequence:

### Phase 0: Pre-Flight Updates
1. **/sanctum:update-docs** - Documentation sync
2. **/abstract:make-dogfood** - Makefile dogfooding
3. **/sanctum:update-readme** - README sync
4. **/sanctum:update-tests** - Test coverage review

### Phase 1: Foundation
5. **sanctum:git-workspace-review** - Repository context
6. **Quality Gates** - Format, lint, test commands

### Phase 2: Code Review
7. **superpowers:receiving-code-review** - Automated review

### Phase 3: Synthesis
8. **sanctum:pr-prep** - PR template generation

## Benefits

### For Developers
- Complete automation of pre-PR checklist
- Governance compliance built-in
- Single command replaces 5+ manual steps
- detailed validation before PR
- Consistent PR descriptions
- Early issue detection

### For Reviewers
- Better context in PRs
- Pre-validated changes
- Documentation already current
- Clear issue descriptions
- Focused review areas

### For Teams
- Consistent quality standards
- Automated pre-review checks
- Reduced review cycle time
- Better PR hygiene
- Enforced governance compliance

## Migration Notes

- `/pr` is now aliased to `/prepare-pr` with full update workflow
- Previous `/pr` behavior available with `--skip-updates` flag
- `--no-code-review` preserves the lightweight behavior
- **Breaking Change**: `/pr` now includes Phase 0 updates by default
- To opt out, use `--skip-updates` or update your workflow

## Configuration

Add to your project's `.claude/config.md`:

```yaml
prepare-pr:
  default_reviewer_scope: "standard"
  skip_updates_by_default: false  # Set true to skip Phase 0 by default
  quality_gates:
    format_command: "make fmt"
    lint_command: "make lint"
    test_command: "make test"
  output_template: "standard"  # or "detailed", "minimal"
```

## Troubleshooting

### Update Commands Not Found
```bash
Error: /sanctum:update-docs not found
Solution: Install sanctum and abstract plugins
```

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

## Comparison: /pr vs /prepare-pr

| Feature | Old /pr | New /prepare-pr |
|---------|---------|-----------------|
| Documentation updates | ❌ Manual | ✅ Automatic |
| Makefile dogfooding | ❌ Manual | ✅ Automatic |
| README sync | ❌ Manual | ✅ Automatic |
| Test coverage review | ❌ Manual | ✅ Automatic |
| Workspace review | ✅ | ✅ |
| Quality gates | ✅ | ✅ |
| Code review | ✅ | ✅ |
| PR template | ✅ | ✅ |
| **Governance compliance** | ❌ Manual | ✅ Automatic |

## Notes

- Requires sanctum, abstract, superpowers, and scribe plugins
- GitHub CLI (gh) recommended for full functionality
- Supports custom quality gate commands
- `/pr` alias maintains backward compatibility (with new defaults)
- Phase 0 updates can be skipped with `--skip-updates` flag
- Implements Mandatory Post-Implementation Protocol automatically
- PR descriptions are verified with scribe to avoid AI-sounding content

## See Also

- `/slop-scan` - Direct AI slop detection (scribe plugin)
- `/doc-polish` - Interactive documentation cleanup (scribe plugin)
- `/pr-review` - Review existing PRs with documentation quality checks
