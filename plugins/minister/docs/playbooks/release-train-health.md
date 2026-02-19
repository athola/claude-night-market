# Release Train Health Playbook

Gate checklist for release managers. Use with `skills/release-health-gates` for automated validation.

## Gate 1 – Scope Freeze

**Owner**: Release Manager | **Trigger**: Feature branch creation

1. Run scope snapshot: `tracker.py status --github-comment > .claude/minister/scope-freeze.md`
2. Verify all blocking issues linked: `gh issue list --label release:train-X --state open`
3. Apply train label: `gh issue edit ID --add-label release:train-X`
4. Post sign-off request: `gh issue comment RELEASE_ID --body-file .claude/minister/scope-freeze.md`
5. Collect stakeholder approvals via GitHub reactions or comments

## Gate 2 – Quality Signals

**Owner**: QA Lead | **Trigger**: 24h before release cut

| Signal | Check Command | Pass Criteria |
|--------|---------------|---------------|
| CI Checks | `gh run list --branch release/X --limit 5` | Green for 24h or rerun justified |
| Docs | `gh issue list --label docs-needed --state open` | All closed or tracked |
| Support | `gh api graphql -f query='query($q: String!) { search(query: $q, type: DISCUSSION, first: 10) { nodes { ... on Discussion { number title url } } } }' -f q="repo:OWNER/REPO category:support"` | Known issues documented |

1. Run health check: `tracker.py status --module quality-signals --github-comment > .claude/minister/quality.md`
2. Post to release issue: `gh issue comment RELEASE_ID --body-file .claude/minister/quality.md`
3. Escalate failures with `risk:red` label

## Gate 3 – Communication

**Owner**: Release Manager | **Trigger**: Release PR approved

1. Generate release notes skeleton from merged PRs: `gh pr list --base main --state merged --search "milestone:vX.Y"`
2. Post status excerpt: `tracker.py status --module deployment-readiness`
3. Update Projects "Release Train" view with final burndown
4. Notify stakeholders via release PR description

## Gate 4 – Post-Ship Review

**Owner**: Release Manager | **Trigger**: 48h after deployment

1. Confirm tasks completed: `tracker.py status --github-comment > .claude/minister/post-ship.md`
2. Export archive: `tracker.py export --output docs/artifacts/release-X.csv`
3. Label issues found during bake: `gh issue edit ID --add-label post-release`
4. Post retrospective: `gh issue comment RELEASE_ID --body-file .claude/minister/post-ship.md`
