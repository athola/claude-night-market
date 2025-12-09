# Weekly Status Report Template

> **Clarity Standard**: Follow the `writing-clearly-and-concisely` guidance from `plugins/abstract/docs/skill-selection.md` (active voice, ≤20-word sentences, GitHub-first references).

**Week**: [Week Number]
**Date Range**: [Start Date] – [End Date]
**Reporting Period**: [Sprint / Release]

## Executive Summary

> **Paste latest Initiative Pulse snippet (Tracker output)**
> 1. `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md`
> 2. `gh issue comment <issue_id> --body-file .claude/minister/latest.md`
> 3. Paste the rendered markdown block here and capture the comment permalink in the Appendix.

### Highlights (≤3 bullet sentences)
- `[GitHub Artifact] – one sentence on impact.`
- `[GitHub Artifact] – one sentence on impact.`
- `[GitHub Artifact] – one sentence on impact.`

### Blockers & Risks
- `[Issue/PR link] – impact – mitigation owner.`
- `[Project view link] – impact – mitigation owner.`

## GitHub Signals

| Signal | `gh` Command or Search URL | Tracker Field | Interpretation (≤15 words) |
| --- | --- | --- | --- |
| Open PRs awaiting review | ``gh pr list --search "label:needs-review is:open"`` | `prs_waiting_review` | `3 PRs idle >48h` |
| Risk issues | `https://github.com/org/repo/issues?q=label:risk:red+is:open` | `risk_issue_count` | `2 blocking risks` |
| Deployment checks | ``gh run list --workflow deploy`` | `deployment_status` | `Most recent run passed` |
| Custom signal | `[Link or command]` | `[tracker_field]` | `[One-line take]` |

*Update the table weekly; keep commentary short and reference the tracker field that feeds the number.*

## Initiative Checklists

> Copy this section per active initiative. Reference tracker IDs so the checklist mirrors `tracker.py` output.

### Architecture Review
- [ ] Tracker Task `AR-101` – Owner @handle – [PR/Issue link] – Status `(On track / At risk)`.
- [ ] Tracker Task `AR-115` – Owner @handle – [Project view note] – Status `(Blocked)`.
- **Pulse**: `[One sentence referencing Initiative Pulse metrics]`.

### Test Infrastructure Modernization
- [ ] Tracker Task `TI-210` – Owner @handle – [Issue search link] – Status `(In progress)`.
- [ ] Tracker Task `TI-214` – Owner @handle – [PR link] – Status `(Needs review)`.
- **Pulse**: `[Cycle time / coverage summary]`.

### Documentation Drive
- [ ] Tracker Task `DD-080` – Owner @handle – [Discussion link] – Status `(On track)`.
- [ ] Tracker Task `DD-085` – Owner @handle – [PR link] – Status `(Awaiting approvals)`.
- **Pulse**: `[Docs freshness, reviewers assigned]`.

*Remove unused initiatives; keep ≤6 checklist lines per initiative.*

## Next Week's Focus
1. `[GitHub milestone or issue] – expected outcome – owner.`
2. `[GitHub automation run] – verification step – owner.`
3. `[Tracker task] – due date – GitHub link.`

## Appendix

### GitHub References
- Status issue comment permalink: `<link>`
- Deployment PR thread: `<link>`
- Project board snapshot: `<link>`
- Discussion for approvals: `<link>`

### Refresh + Publish Checklist
1. `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/status.md`
2. `gh issue comment <issue_id> --body-file .claude/minister/status.md`
3. Paste the rendered snippet into the Executive Summary block and store the comment permalink above.
4. Re-read the report; trim sentences that exceed 20 words or lack a GitHub surface reference.

*Report prepared by: [Name]*
*Next report due: [Date]*
