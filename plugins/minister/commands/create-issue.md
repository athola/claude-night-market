---
name: create-issue
description: Create a new GitHub issue with formatted description, labels, and optional reference links
usage: /create-issue <title> [--body <text>] [--labels <label>...] [--assignee <user>] [--milestone <milestone>] [--refs <url>...]
---

# Create Issue

Creates a new GitHub issue in the current repository (or specified repo) with formatted description, labels, assignees, and optional reference links to related issues, PRs, or documentation.

## Arguments

- `<title>` - Issue title (wrap in quotes if it contains spaces)
- `--body <text>` - Issue body/description (wrap in quotes)
- `--labels <label>...` - One or more labels to apply
- `--assignee <user>` - GitHub username to assign
- `--milestone <milestone>` - Milestone name or number
- `--project <project>` - Add to GitHub Project (name or number)
- `--refs <url>...` - Reference URLs to include in the issue body
- `--repo <owner/repo>` - Create in specific repository (default: current)
- `--template` - Use interactive template mode with guided prompts

## Workflow

### Phase 1: Parse Arguments

1. **Extract Title**

   The first positional argument is the title. If no flags follow, the entire argument string is the title.

2. **Parse Optional Flags**

   Extract all optional parameters from the command arguments.

3. **Determine Target Repository**

   ```bash
   # If --repo not specified, use current repository
   gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
   ```

### Phase 2: Build Issue Body

Construct the issue body from the provided description and references.

#### Body Structure

```markdown
${body_text}

${references_section}
```

#### References Section

If `--refs` URLs are provided, analyze and categorize them:

```
Use the WebFetch tool to retrieve metadata for each URL:
- GitHub issue URLs → Extract issue number, title, status
- GitHub PR URLs → Extract PR number, title, status
- Documentation URLs → Extract page title
- Other URLs → Use raw URL with domain name

Format as a "Related Links" section:
## Related Links

- [#123: Original feature request](https://github.com/owner/repo/issues/123)
- [PR #456: Initial implementation](https://github.com/owner/repo/pull/456)
- [Design Doc: Architecture](https://example.com/docs/architecture)
```

### Phase 3: Interactive Template Mode (Optional)

When `--template` flag is used, guide the user through structured prompts:

```
Use the AskUserQuestion tool for each section:

1. **Issue Type**
   Options: "Bug", "Feature", "Enhancement", "Documentation", "Question"

2. **Description Prompts** (based on type):

   For Bug:
   - What is the expected behavior?
   - What is the actual behavior?
   - Steps to reproduce?
   - Environment details?

   For Feature/Enhancement:
   - What problem does this solve?
   - Proposed solution?
   - Acceptance criteria?
   - Alternatives considered?

3. **Labels** (suggest based on type):
   - bug → "bug", "needs-triage"
   - feature → "enhancement", "feature"
   - documentation → "documentation"

4. **Priority** (optional):
   Options: "critical", "high", "medium", "low"
   → Adds corresponding label

5. **Related Links**:
   Prompt: "Any related issues, PRs, or docs? (URLs, one per line, empty to finish)"
   Loop until empty input.
```

The template mode builds the full `gh issue create` command from responses.

### Phase 4: Create Issue

Execute the GitHub CLI command to create the issue:

```bash
gh issue create \
  --repo "${repo}" \
  --title "${title}" \
  --body "${body}" \
  ${labels:+--label "$labels"} \
  ${assignee:+--assignee "$assignee"} \
  ${milestone:+--milestone "$milestone"} \
  ${project:+--project "$project"}
```

**Command Construction Notes:**
- Use `--body-file` if body is long (>500 chars) to avoid shell limits
- Multiple labels: `--label "bug" --label "needs-triage"`
- Escape quotes in title/body properly

### Phase 5: Post-Creation Actions

After successful creation, perform follow-up actions:

1. **Capture Issue URL**

   ```bash
   gh issue create [...] --json url,number -q '"\(.number): \(.url)"'
   ```

2. **Display Summary**

   ```markdown
   Created issue #${number}

   Title: ${title}
   URL: ${url}
   Labels: ${labels}
   Assigned: ${assignee}
   ```

3. **Optional: Add to Project Board**

   If `--project` specified:
   ```bash
   gh project item-add ${project_number} --url ${issue_url}
   ```

4. **Optional: Link Related Issues**

   If `--refs` contains GitHub issue/PR URLs, add automatic cross-references:
   ```bash
   # For each GitHub ref URL
   gh issue comment ${ref_number} --body "Related: ${new_issue_url}"
   ```

## Examples

### Example 1: Simple Issue

```bash
/create-issue "Fix login timeout on slow connections"
```

**Result:**
```
Created issue #234

Title: Fix login timeout on slow connections
URL: https://github.com/athola/skrills/issues/234
```

### Example 2: Full Issue with Labels and References

```bash
/create-issue "Add MCP analytics dashboard" \
  --body "Create a web dashboard showing skill usage metrics and recommendations" \
  --labels "enhancement" "mcp" \
  --assignee "athola" \
  --refs "https://github.com/athola/skrills/issues/21" \
        "https://example.com/docs/analytics-spec"
```

**Generated Body:**
```markdown
Create a web dashboard showing skill usage metrics and recommendations

## Related Links

- [#21: Enhance MCP analytics](https://github.com/athola/skrills/issues/21)
- [Analytics Spec](https://example.com/docs/analytics-spec)
```

### Example 3: Interactive Template Mode

```bash
/create-issue --template

> Issue Type? [Bug/Feature/Enhancement/Documentation/Question]
Feature

> What problem does this solve?
Users need visibility into skill usage patterns.

> Proposed solution?
Build a dashboard using the MCP analytics API.

> Acceptance criteria? (one per line, empty to finish)
- Display skill co-occurrence graph
- Show recommendation quality metrics
- Allow date range filtering
[empty]

> Priority? [critical/high/medium/low/skip]
medium

> Related links? (URLs, one per line, empty to finish)
https://github.com/athola/skrills/issues/21
[empty]

Creating issue with:
  Title: Add MCP analytics dashboard
  Labels: enhancement, feature, priority:medium
  Body: [3 sections, 245 chars]

Created issue #234: https://github.com/athola/skrills/issues/234
```

### Example 4: Cross-Repo Issue

```bash
/create-issue "Document API changes" \
  --repo "athola/skrills-docs" \
  --body "Update docs to reflect v2.0 API changes" \
  --labels "documentation" \
  --refs "https://github.com/athola/skrills/pull/456"
```

## Error Handling

### Repository Not Found

```markdown
Error: Repository 'athola/unknown-repo' not found
Verify the repository exists and you have access.

Current repository: athola/skrills
```

### Invalid Label

```markdown
Warning: Label 'unknown-label' does not exist in athola/skrills

Available labels:
- bug, enhancement, documentation, question
- priority:high, priority:medium, priority:low
- needs-triage, in-progress, blocked

Continue without this label? [y/n]
```

### Missing Title

```markdown
Error: Issue title is required

Usage: /create-issue <title> [options]
```

### Authentication Required

```markdown
Error: GitHub authentication required

Run: gh auth login
```

## Template Formats

The command recognizes common issue types and formats accordingly:

### Bug Report Template

```markdown
## Description
${user_description}

## Expected Behavior
${expected}

## Actual Behavior
${actual}

## Steps to Reproduce
${steps}

## Environment
${environment}

## Related Links
${refs}
```

### Feature Request Template

```markdown
## Problem Statement
${problem}

## Proposed Solution
${solution}

## Acceptance Criteria
${criteria}

## Alternatives Considered
${alternatives}

## Related Links
${refs}
```

## Integration Notes

### Relationship to `/close-issue`

| Command | Purpose | Workflow |
|---------|---------|----------|
| `/create-issue` | Issue creation | Idea → Formatted issue |
| `/close-issue` | Issue analysis | Evidence → Closure decision |

Together they provide full issue lifecycle management.

### Minister Integration

The command integrates with minister's project tracking:

1. **Auto-Capture to Tracker**

   After creating an issue, optionally add it to minister's project tracker:
   ```bash
   uv run python plugins/minister/scripts/tracker.py add \
     --url "${issue_url}" \
     --status "Not Started"
   ```

2. **Initiative Linking**

   If `--project` references a tracked initiative, update initiative metadata.

### GitHub CLI Features

Leverages `gh` CLI capabilities:
- Uses user's authenticated session
- Respects repository defaults (labels, milestones)
- Supports GitHub Projects v2 via `gh project`
- Enables cross-repository operations

## Best Practices

### DO:
- Use descriptive, action-oriented titles
- Include acceptance criteria for features
- Link to related issues/PRs with `--refs`
- Apply appropriate labels for triage
- Use `--template` for consistent formatting

### DON'T:
- Create duplicate issues without checking
- Use vague titles like "Fix bug" or "Improve feature"
- Skip the description for complex issues
- Forget to assign if you know the owner
- Over-label (3-5 labels is usually enough)

## Advanced Usage

### Bulk Issue Creation

For creating multiple related issues from a list:

```bash
# Read from a CSV or structured file
# Parse each line and call /create-issue
```

### Issue Templates from Files

```bash
/create-issue "$(cat issue-title.txt)" \
  --body "$(cat issue-body.md)" \
  --labels "$(cat labels.txt)"
```

### Pipeline Integration

```bash
# Create issue from CI/CD failure
/create-issue "CI failure in ${JOB_NAME}" \
  --body "Build failed: ${BUILD_URL}" \
  --labels "ci" "bug" \
  --refs "${COMMIT_URL}"
```

## See Also

- `/close-issue` - Analyze and close completed issues
- `minister:github-initiative-pulse` - Initiative status tracking
- `minister:release-health-gates` - Release readiness checks
- GitHub CLI documentation: https://cli.github.com/manual/gh_issue_create
