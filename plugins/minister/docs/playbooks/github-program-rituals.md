# GitHub Program Rituals Playbook

Use this playbook with `skills/github-initiative-pulse` to keep every ritual tied to a tracker-generated GitHub comment. Each checklist item starts with an owner so anyone can run the loop without re-reading process docs.

> Prep once per day: `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md`

## Monday – Pulse Review (Owner: Program Lead)

Saved search: [`Blockers needing escalation`](https://github.com/<org>/<repo>/issues?q=is%3Aopen+label%3Ablocker+sort%3Aupdated-desc)

- [ ] 09:00 PT – Program Lead runs `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/latest.md` using the Initiative Pulse skill preset.
- [ ] 09:02 PT – Push the comment into the Program Review issue: `gh issue comment <pulse-issue-id> --body-file .claude/minister/latest.md`.
- [ ] 09:05 PT – Copy the GitHub comment permalink into the Projects “Initiative Pulse” note field (`https://github.com/orgs/<org>/projects/<project-id>/views/1`) so the board stays traceable.
- [ ] 09:10 PT – Open the saved search above in a new tab and file follow-up issues for any blocker >3 days old via `gh issue create --title "... blocker" --label blocker`.
- [ ] 09:15 PT – Update swimlanes so every card shows an owner and due date; tag missing data with `@` mentions directly from the Program Review issue thread.

## Wednesday – Risk Radar (Owner: Risk Captain)

Saved search: [`High-risk slippage`](https://github.com/<org>/<repo>/issues?q=is%3Aopen+label%3Arisk%3Ared+sort%3Aupdated-desc)

- [ ] 11:00 PT – Run the tracker hotlist: `uv run python plugins/minister/scripts/tracker.py status --module metrics-hotlist --github-comment > .claude/minister/risk.md`.
- [ ] 11:03 PT – Publish a triage discussion with the hotlist attached: `gh discussion create 123 --title "Weekly Risk Radar" --body-file .claude/minister/risk.md`.
- [ ] 11:06 PT – Link the discussion URL back into `.claude/minister/risk.md` and paste the snippet into the standing Risk issue using `gh issue comment <risk-issue-id> --body-file .claude/minister/risk.md`.
- [ ] 11:10 PT – Mass-update labels from the saved search by running `gh issue edit <id> --add-label risk:yellow` (or `risk:red`) for every item that needs escalation.
- [ ] 11:15 PT – Add the discussion permalink to the Projects “Risk Radar” lane notes so downstream squads can subscribe.

## Friday – Demo + Planning (Owner: Delivery Lead)

Saved search: [`Demo-ready pull requests`](https://github.com/<org>/<repo>/pulls?q=is%3Aopen+label%3Ademo+sort%3Aupdated-desc)

- [ ] 14:00 PT – Delivery Lead refreshes tracker output: `uv run python plugins/minister/scripts/tracker.py status --github-comment > .claude/minister/demo.md`.
- [ ] 14:05 PT – Drop the Initiative Pulse snippet into the Demo Log issue: `gh issue comment <demo-issue-id> --body-file .claude/minister/demo.md`.
- [ ] 14:07 PT – Export supporting metrics for slides: `uv run python plugins/minister/scripts/tracker.py export --output docs/artifacts/demo.csv` and upload to the Demo Log issue as an attachment.
- [ ] 14:10 PT – Open the saved search to confirm every demo-tagged PR has reviewers assigned; @mention missing reviewers directly in each PR thread.
- [ ] 14:15 PT – Clone prioritized backlog cards into the Projects “Next Week” section and link the Demo Log issue comment URL in the project note for historical context.

## Monthly – Executive Packet (Owner: Program Lead + Exec Partner)

Saved search: [`Executive packet follow-ups`](https://github.com/<org>/<repo>/issues?q=is%3Aopen+label%3Aexec-packet+sort%3Aupdated-desc)

- [ ] First business day – Consolidate four weekly Initiative Pulse snippets by concatenating the previous `.claude/minister/latest.md` files into `.claude/minister/executive.md`.
- [ ] Same day – Paste the consolidated snippet into the Executive Packet discussion: `gh discussion comment <exec-discussion-id> --body-file .claude/minister/executive.md`.
- [ ] Within 30 minutes – Attach burndown CSV (`uv run python plugins/minister/scripts/tracker.py export --output docs/artifacts/burndown.csv`) and link the artifact from the discussion.
- [ ] Before publishing – Reference release-train gate history by linking to `plugins/minister/docs/playbooks/release-train-health.md#gate-status` and capturing any blockers as `exec-packet` labeled issues.
- [ ] After publishing – Store the discussion permalink inside the Projects custom field `status_comment_url` so the Initiative Pulse skill can quote it next month.
