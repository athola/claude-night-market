# GitHub Program Rituals

Weekly cadences that tie tracker output to GitHub comments. Each ritual has an owner and a saved search.

**Daily prep**: `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md`

## Monday – Pulse Review

**Owner**: Program Lead | **Search**: `is:open label:blocker sort:updated-desc`

1. Generate Initiative Pulse → `.claude/minister/latest.md`
2. Post to Program Review issue: `gh issue comment ISSUE_ID --body-file .claude/minister/latest.md`
3. Copy comment permalink into Projects "Initiative Pulse" note field
4. File follow-up issues for blockers >3 days: `gh issue create --title "..." --label blocker`
5. Update swimlanes: ensure every card has owner + due date

## Wednesday – Risk Radar

**Owner**: Risk Captain | **Search**: `is:open label:risk:red sort:updated-desc`

1. Generate hotlist: `tracker.py status --module metrics-hotlist --github-comment > .claude/minister/risk.md`
2. Create discussion: `gh discussion create --title "Weekly Risk Radar" --body-file .claude/minister/risk.md`
3. Post to standing Risk issue: `gh issue comment RISK_ISSUE_ID --body-file .claude/minister/risk.md`
4. Update labels: `gh issue edit ID --add-label risk:yellow` for escalations
5. Add discussion permalink to Projects "Risk Radar" lane notes

## Friday – Demo + Planning

**Owner**: Delivery Lead | **Search**: `is:open is:pr label:demo sort:updated-desc`

1. Refresh tracker → `.claude/minister/demo.md`
2. Post to Demo Log issue: `gh issue comment DEMO_ISSUE_ID --body-file .claude/minister/demo.md`
3. Export metrics: `tracker.py export --output docs/artifacts/demo.csv`
4. Verify demo PRs have reviewers; @mention missing ones
5. Clone backlog cards to "Next Week" section; link Demo Log permalink

## Monthly – Executive Packet

**Owner**: Program Lead + Exec Partner | **Search**: `is:open label:exec-packet`

1. Concatenate weekly `.claude/minister/latest.md` files → `.claude/minister/executive.md`
2. Post to Executive Packet discussion: `gh discussion comment EXEC_ID --body-file .claude/minister/executive.md`
3. Attach burndown CSV: `tracker.py export --output docs/artifacts/burndown.csv`
4. Link to [release-train-health.md](release-train-health.md) gate history
5. Store discussion permalink in Projects `status_comment_url` field
