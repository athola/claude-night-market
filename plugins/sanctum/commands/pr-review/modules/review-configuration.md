# PR Review: Configuration & Options

Command options, configuration, best practices, and integration details.

> **See Also**: [Main Command](../pr-review.md) | [Workflow](review-workflow.md) | [Framework](review-framework.md)

## Advanced Features

### 1. Automated Issue Creation
```bash
# For each backlog item:
gh issue create \
  --title "[Enhancement] <title>" \
  --body="## Context
Identified during PR #<number> review

## Details
<finding details>

## Suggested Approach
<implementation notes>

## Priority
Medium - Improvement opportunity

---
*Auto-created by pr-review*" \
  --label="enhancement,backlog"
```

### 2. Quality Metrics Integration
```markdown
### Quality Metrics
- **Code Coverage**: 85% (target: 80%) PASS
- **Complexity**: Low (new functions < 10 cyclomatic) PASS
- **Duplication**: 2% (target: <5%) PASS
- **Security**: 0 high-severity issues PASS
```

### 3. Reviewer Guidance
```markdown
### Review Focus Areas
Based on scope and analysis:
1. Verify JWT implementation (security)
2. Check password hashing (security)
3. Validate error handling (robustness)
4. Review test coverage (quality)
```

## Integration Benefits

### For Reviewers
- Clear understanding of PR scope
- Prioritized feedback (blocking vs suggestions)
- Context-aware recommendations
- Reduced review time through automation

### For Authors
- Specific, actionable feedback
- Clear path to approval
- Backlog items automatically created
- Quality metrics provided

### For Teams
- Consistent review standards
- Scope discipline enforced
- Technical debt tracked
- Quality gates automated

## Error Handling

### No Scope Artifacts Found
```markdown
Warning: No plan/spec found for this PR
Using PR description as scope baseline
Recommendation: Create plan.md for future PRs
```

### Analysis Failures
```bash
Error: Superpowers code review failed
Falling back to manual review mode
```

### GitHub API Issues
```bash
Warning: Cannot create backlog issues (rate limit)
Please create manually from backlog section
```

### GitHub Review Submission Errors

**No PR Found:**
```bash
# If no PR exists for current branch
gh pr view --json number -q '.number'
# Returns empty - skip GitHub submission
Warning: No PR found for current branch. Review saved locally only.
```

**Cannot Approve Own PR:**
```bash
# Error: "Review Can not approve your own pull request"
# This occurs when using --approve or REQUEST_CHANGES on your own PR

# SOLUTION: Check authorship first, use COMMENT event for own PRs
PR_AUTHOR=$(gh pr view $PR_NUMBER --json author -q '.author.login')
CURRENT_USER=$(gh api user -q '.login')
if [[ "$PR_AUTHOR" == "$CURRENT_USER" ]]; then
  # Use COMMENT instead of APPROVE/REQUEST_CHANGES
  gh pr review $PR_NUMBER --comment --body "Review summary..."
fi
```

**Line Comment API Errors:**
```bash
# Error: "line is not a permitted key" or "No subschema in oneOf matched"
# This happens when using the comments endpoint with line/side parameters

# WRONG - Individual comments endpoint doesn't support line/side:
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f body="..." -f path="file.rs" -f line=45 -f side="RIGHT"  # FAILS

# CORRECT - Use the reviews endpoint with comments array:
gh api repos/{owner}/{repo}/pulls/{pr}/reviews \
  --method POST \
  -f event="COMMENT" \
  -f body="" \
  -f 'comments[][path]=file.rs' \
  -F 'comments[][line]=45' \              # Note: -F for integer
  -f 'comments[][body]=Comment text'
```

**Line Not In Diff (422 Unprocessable Entity):**
```bash
# Error: "Line could not be resolved"
# This occurs when the line number isn't part of the PR diff

# SOLUTION: Post as a general PR comment instead
gh pr comment $PR_NUMBER --body "**[G2] Suggestion**

Location: app.rs:1933 (not in PR diff - general observation)
Issue: File approaching size threshold

**Suggestion:** Consider modularization."
```

**Integer vs String Parameters:**
```bash
# Error: "128 is not an integer" (when passed as string)

# WRONG - Using -f passes as string:
-f 'comments[][line]=128'

# CORRECT - Using -F passes as raw/integer:
-F 'comments[][line]=128'
```

**Pending Review Already Exists:**
```bash
# Check for existing pending review
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --jq '.[] | select(.state == "PENDING")'

# If pending review exists, add comments to it instead of creating new
# Use the existing review_id for subsequent comments
```

**Authentication Issues:**
```bash
# Verify gh is authenticated
gh auth status
# If not authenticated, proceed with dry-run mode
Warning: GitHub CLI not authenticated. Running in dry-run mode.
```

## Configuration

```yaml
pr_review:
  default_scope_mode: "standard"
  auto_approve_threshold: 0  # No blocking issues
  auto_create_issues: true   # Automatic issue creation for out-of-scope items (default: true)
  require_test_coverage: true
  min_coverage_percent: 80

  quality_gates:
    max_complexity: 10
    max_duplication: 5
    require_documentation: true

  issue_creation:
    enabled: true              # Set to false to disable auto-creation
    check_duplicates: true     # Search for existing issues before creating
    default_priority: "medium"
    assign_to_author: false
    labels:
      suggestion: ["enhancement", "low-priority", "small-effort"]
      backlog: ["enhancement", "low-priority"]
      deferred: ["enhancement", "medium-priority"]
```

> **Module Reference**: See `plugins/sanctum/skills/shared/modules/auto-issue-creation.md` for implementation details.

## Best Practices

### Before Review
1. validate PR description is clear
2. Verify CI pipeline passed
3. Check for scope artifacts
4. Confirm tests are running

### During Review
1. Establish scope baseline first
2. Classify findings consistently
3. Provide actionable feedback
4. Create issues for improvements

### After Review
1. Verify all issues are tracked
2. Check recommendation accuracy
3. Update scope artifacts if needed
4. Follow up on backlog items

## Migration Notes

- `/pr-review` now includes the enhanced superpowers-driven workflow (formerly `/pr-review-wrapper`).
- Options like `--scope-mode` and `--create-backlog-issues` remain unchanged.

## Notes

- Maintains full backward compatibility with /pr-review
- Requires superpowers plugin for enhanced analysis
- GitHub CLI (`gh`) required for review submission and issue creation
- All Sanctum scope validation preserved
- Adds detailed code quality checks
- **Automatically posts findings as GitHub PR review comments**
- **⚠️ MUST post test plan as a SEPARATE PR comment** (for `/fix-pr` integration)
  - This is NOT optional - test plan must be a distinct `gh pr comment` call
  - Do NOT just include in review summary or conversational output
  - `/fix-pr` searches for "Test Plan for PR" to find verification steps
- Use `--dry-run` to generate report without posting to GitHub
- Use `--no-line-comments` to only submit summary without inline comments
- Test plan includes verification steps for all blocking and in-scope issues

### Version Validation Enforcement (NEW)

**MANDATORY on every PR** unless explicitly bypassed:
- Runs in Phase 1.5 (after scope, before code analysis)
- Checks version consistency across:
  - Claude marketplace: marketplace.json ↔ plugin.json files
  - Python: pyproject.toml ↔ __version__ in code
  - Node: package.json ↔ package-lock.json
  - Rust: Cargo.toml ↔ Cargo.lock
  - CHANGELOG: Has entry for new version
- **All version mismatches are BLOCKING** (unless waived)
- Bypass with: `--skip-version-check`, `skip-version-check` label, or `[skip-version-check]` in PR description
- See `modules/version-validation.md` for complete validation procedures

## See Also

- `/fix-pr` - Address PR review comments and resolve threads
- `/resolve-threads` - Batch-resolve unresolved review threads
- `/pr` - Prepare a PR for submission
