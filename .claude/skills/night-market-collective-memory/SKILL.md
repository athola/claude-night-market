---
name: night-market-collective-memory
description: 'Search and record project memory (Discussions, journal, ADRs). Use before re-investigating anything. Do not use for settled battles; see failure-archaeology.'
---

# Night Market Collective Memory

This repo treats GitHub Discussions as agent collective memory
(ADR-0007, `docs/adr/0007-github-discussions-integration.md`,
accepted 2026-02-19). Sessions are amnesiac by default. The memory
system fixes that with four layers: Discussions (cross-session,
searchable), the decision journal (append-only tradeoff and lesson
logs), numbered ADRs (architecture decisions), and dated research
syntheses in `docs/research/`. One caveat on the fourth layer:
`docs/research/` is gitignored and machine-local, so it exists only
on the authoring machine and is empty on fresh clones. A synthesis
counts as collective memory only after promotion to a Discussion,
ADR, or rule. This skill tells you where each kind of knowledge
lives, how to read it, and how to write to it.

One hard fact first: there is NO `gh discussion` subcommand.
Discussions are GraphQL-only. Minister playbooks once referenced a
CLI that does not exist, and ADR-0007 replaced every reference with
`gh api graphql` calls. Never guess a `gh discussion` command.

## Routing table: which memory layer

| You have | Record or read it via |
|----------|----------------------|
| Settled battle, revert, dead end | `night-market-failure-archaeology` skill (read only, do not relitigate) |
| Tradeoff (chose A, sacrificed B) | Decision journal `docs/tradeoffs.md`, TR-NNN entry |
| Lesson, failed approach, rework | Decision journal `docs/lessons-learned.md`, LL-NNN entry |
| Architecture decision | Numbered ADR in `docs/adr/` (0001-0017 exist today) |
| Session insight, skill stats | `[Learning]` Discussion (auto-posted daily, see below) |
| Strategy debate, big design | `[War Room]` Discussion (Decisions category) |
| Durable synthesis, audit result | `[Knowledge]` Discussion (Knowledge category) |
| PR review finding worth keeping | `[PR Finding]` Discussion (Learnings category) |
| Multi-source research output | Dated file in `docs/research/` (LOCAL ONLY: gitignored, absent on fresh clones). Promote durable syntheses to a `[Knowledge]` Discussion, ADR, or rule to make them collective memory |

## Retrieval discipline: search before re-investigating

Before investigating any question about this repo's history, design,
or past failures, run these searches first. Re-deriving a settled
answer wastes a session and risks contradicting an accepted decision.

```bash
# 1. Search Discussions by keyword (tested 2026-07-02)
gh api graphql -f query='
query($q: String!) {
  search(query: $q, type: DISCUSSION, first: 10) {
    nodes { ... on Discussion { number title url category { name } } }
  }
}' -f q='repo:athola/claude-night-market YOUR SEARCH TERMS'

# 2. Search local docs of record. Note: docs/research/ is gitignored
#    and machine-local, so it is empty on fresh clones and this
#    search only helps on the authoring machine.
rg -il "your terms" docs/research/ docs/adr/ CHANGELOG.md

# 3. Check the decision journal (if the files exist yet, see below)
rg -in "your terms" docs/tradeoffs.md docs/lessons-learned.md
```

Also check the `night-market-failure-archaeology` sibling for
settled battles. A leyline SessionStart hook
(`plugins/leyline/hooks/fetch-recent-discussions.sh`) already
injects the 5 most recent Decisions discussions at session start,
bounded to under 600 tokens with a 3-second timeout.

## Discussion taxonomy (verified live 2026-07-02)

Repo categories include the four ADR-0007 ones (Decisions,
Deliberations, Learnings, Knowledge) plus GitHub defaults. Title
prefixes are the working taxonomy:

| Prefix | Category | What it is | Verified examples |
|--------|----------|------------|-------------------|
| `[Learning]` | Learnings | Daily digest, auto-posted | #601, #602 (2026-07-01/02) |
| `[Knowledge]` | Knowledge | Durable syntheses | #448, #449 (April 2026 skill audit synthesis and Wave-3 backlog) |
| `[War Room]` | Decisions | Strategy deliberations | #222 (collective memory design), #271 (wiring publishing into workflows) |
| `[PR Finding]` | Learnings | Review findings worth keeping | #424, #595 |

### The [Learning] pipeline

Daily digests are auto-posted by abstract's Stop hook, part of the
improvement feedback loop (Issue #69). The chain:

1. `plugins/abstract/hooks/skill_execution_logger.py`
   (PreToolUse/PostToolUse) logs skill executions.
2. `plugins/abstract/scripts/aggregate_skill_logs.py` writes
   `~/.claude/skills/LEARNINGS.md` with skill-performance stats
   (skills analyzed, high-impact issues, slow and low-rated skills).
3. `plugins/abstract/hooks/post_learnings_stop.py` (Stop hook,
   registered in `plugins/abstract/hooks/hooks.json`) posts a
   `[Learning] YYYY-MM-DD` digest, deduplicated by title. Opt-out:
   `~/.claude/skills/discussions/config.json`.
4. Promotion: 3 or more fire-emoji reactions on a Learnings
   discussion promote it to a GitHub Issue via
   `plugins/abstract/scripts/promote_discussion_to_issue.py`
   (default threshold 3, configurable via `promotion_threshold`).

## Reading Discussions (tested queries)

List recent discussions, newest first (tested 2026-07-02, returned
#602 and siblings):

```bash
gh api graphql -f query='
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    discussions(first: 10,
                orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes { number title category { name } createdAt url }
    }
  }
}' -f owner=athola -f name=claude-night-market
```

Fetch one discussion by number. The number is a GraphQL `Int`, so
pass it with `-F` (typed), not `-f` (string). Passing `-f` fails
with a type error:

```bash
gh api graphql -f query='
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    discussion(number: $number) {
      title body url category { name }
      comments(first: 10) { nodes { body } }
    }
  }
}' -f owner=athola -f name=claude-night-market -F number=222
```

## Writing Discussions (mutations: shapes verified, NOT executed)

Publishing rules from ADR-0007: prompt the user `[Y/n]` before any
create or comment (no auto-publish), cap bodies at 2000 words and
link to local files for detail, and pass all values as `-f`/`-F`
variables (never string-interpolate into the query).

Mutations need node IDs. Resolve them first (this read query was
tested 2026-07-02):

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    id
    hasDiscussionsEnabled
    discussionCategories(first: 25) { nodes { id name slug } }
  }
}' -f owner=athola -f repo=claude-night-market
```

Create a comment (mutation shape from the canonical leyline
templates, untested here to avoid posting):

```bash
gh api graphql -f query='
mutation($discussionId: ID!, $body: String!) {
  addDiscussionComment(input: {
    discussionId: $discussionId,
    body: $body
  }) {
    comment { id url }
  }
}' -f discussionId="$DISCUSSION_ID" -f body="$COMMENT_BODY"
```

Creating a discussion uses `createDiscussion(input: {repositoryId,
categoryId, title, body})` (same status: shape verified against the
canonical templates, untested here). For threaded replies, mark-as-
answer, and updates, use the canonical template file:
`plugins/leyline/skills/git-platform/modules/command-mapping.md`,
section "Discussion Operations". GitHub only: GitLab and Bitbucket
have no Discussions equivalent, so skip with a warning there.

## Decision journal (leyline:decision-journal contract)

The contract lives in
`plugins/leyline/skills/decision-journal/SKILL.md`. Two append-only
logs, co-located with the code:

- `docs/tradeoffs.md`: decisions and the alternatives sacrificed.
  Entry IDs `TR-NNN`, status `proposed`, then `accepted`, then
  `superseded-by: TR-NNN` or `deprecated`.
- `docs/lessons-learned.md`: failed approaches and rework, framed
  blamelessly. Entry IDs `LL-NNN`, status `open`, then `actioned`,
  then `closed`.

Discipline: append-only, never edit or delete an accepted entry. A
reversal adds a new entry, flips the old one's status, and links
both ways. Every entry links to its PR, commit, or issue. Draft the
entry, show it to the human, and append only on confirm.

Status as of 2026-07-02: neither `docs/tradeoffs.md` nor
`docs/lessons-learned.md` exists in the repo yet. The contract is
defined and the files are created on first use (scaffolding belongs
to `attune:project-init`). The append helper:

```bash
python3 plugins/leyline/scripts/journal_append.py tradeoffs \
  --project-root . --title "Compliance check" \
  --field context="verify" --dry-run
```

Big decisions do not go in the journal. They get a numbered ADR in
`docs/adr/`, and a journal entry may reference the ADR number.

## Monitoring: a starved digest is an alert

If the newest `[Learning]` discussion is more than about 2 days
old, treat it as an incident signal. Precedent: the digest was once
starved for two months because hooks read `CLAUDE_TOOL_*` env vars
Claude Code never sets, and the missing digest was the only visible
symptom (full record: night-market-failure-archaeology SB9; fix:
stdin-first `shared/hook_io.read_hook_payload`, CHANGELOG 1.9.14).

Check the gap with the tested list query above. If starved, verify
each chain segment in order: is `~/.claude/skills/LEARNINGS.md`
fresh, is the Stop hook registered in
`plugins/abstract/hooks/hooks.json`, and does the logger receive a
stdin payload. Then follow `night-market-debugging-playbook` for
hook triage.

## When NOT to use

- Settled failures, reverts, and dead ends you are tempted to
  re-try: read `night-market-failure-archaeology` instead.
- Classifying or gating a change you are about to make: use
  `night-market-change-control`.
- Running the hunch-to-accepted-result pipeline that produces
  `docs/research/` syntheses: use
  `night-market-research-methodology`. This skill only covers where
  the outputs are stored and retrieved.
- House style for the documents themselves: use
  `night-market-docs-and-writing`.

## Exit Criteria

- [ ] Before any re-investigation, a Discussions search and a
  `docs/research/` search ran, and hits (or "no hits") were stated.
- [ ] Any Discussions access used `gh api graphql`. Zero
  `gh discussion` invocations appear in the transcript.
- [ ] New knowledge was routed per the routing table (correct layer
  named before writing anything).
- [ ] Any journal write produced a stable TR-NNN/LL-NNN entry with
  an index row, and no prior entry was edited or deleted.
- [ ] Any Discussion create or comment was confirmed by the user
  first, and used `-f`/`-F` variables (no string interpolation).
- [ ] The newest `[Learning]` digest date was checked, and any gap
  over 2 days was reported as a starvation alert.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15, branch
discussions-fix-1.9.14. Read queries in this file were executed live
against athola/claude-night-market on 2026-07-02. Mutation snippets
were checked against the leyline templates but not executed.

Re-verification one-liners for facts that may drift:

```bash
# Taxonomy and digest freshness (also the starvation check)
gh api graphql -f query='query($o:String!,$n:String!){repository(owner:$o,name:$n){discussions(first:5,orderBy:{field:CREATED_AT,direction:DESC}){nodes{number title createdAt}}}}' -f o=athola -f n=claude-night-market

# Decision journal files exist yet?
ls docs/tradeoffs.md docs/lessons-learned.md

# Promotion threshold still 3 fire reactions?
rg -n "promotion_threshold" plugins/abstract/scripts/promote_discussion_to_issue.py

# Stop hook still registered?
rg -n "post_learnings_stop" plugins/abstract/hooks/hooks.json

# Canonical GraphQL templates still present?
rg -n "Discussion Operations" plugins/leyline/skills/git-platform/modules/command-mapping.md

# ADR count and 0007 status
ls docs/adr/ && rg -n "^Accepted" docs/adr/0007-github-discussions-integration.md
```
