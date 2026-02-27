# Memory Palace: Knowledge Management

Build a persistent knowledge base that grows with your work. This tutorial covers the core Memory Palace workflows: capturing knowledge, organizing it in palaces, maintaining it over time, and finding what you need.

---

## Scenario

You're working on a project with technologies you'll reference repeatedly: API patterns, architecture decisions, library quirks. Instead of re-researching every session, you want a knowledge base that remembers what you've learned.

## Step 1: Create a Palace

A palace is a themed container for knowledge. Create one for your project's domain:

```
/palace create "API Patterns" "rest-api" --metaphor library
```

This creates a palace named "API Patterns" in the `rest-api` domain using the `library` metaphor. Metaphors determine how knowledge is organized:

| Metaphor | Best for |
|----------|----------|
| `library` | Research, documentation |
| `workshop` | Practical skills, tools |
| `garden` | Evolving knowledge |
| `fortress` | Security, production systems |
| `building` | General organization (default) |

Check what you have:

```
/palace list
```

This shows all palaces with entry counts and last-modified dates.

## Step 2: Capture Knowledge

Knowledge enters the palace through two paths.

### Automatic Capture

When you research topics during a Claude Code session (web searches, reading docs, analyzing code), the Memory Palace hooks queue findings for later processing. This happens in the background. You don't need to do anything special.

Check the queue:

```
/palace status
```

This shows total palaces, entry counts, and the intake queue size (how many items are waiting to be processed).

### Manual Intake

To explicitly capture something you've learned:

```
/garden seed ~/my-garden.json "OAuth2 PKCE Flow" --section auth --links "Authentication,Security"
```

This adds a new entry with links to related concepts, which helps with navigation later.

## Step 3: Process the Queue

Queued research needs to be synced into palaces. Preview first:

```
/palace sync --dry-run
```

This shows what would be processed: which items match existing palaces, which would create new entries, and which have no matching palace.

When it looks right:

```
/palace sync
```

Items are matched to palaces by domain and tags, then organized into districts within each palace.

## Step 4: Find What You Know

Search across all your palaces:

```
/navigate search "rate limiting" --type semantic
```

This searches by meaning, not just keywords. It returns matches with:

- Which palace and district contains the result
- Relevance score
- Related concepts nearby

For a specific concept:

```
/navigate locate "OAuth 2.0"
```

To explore connections between concepts:

```
/navigate path "OAuth" "JWT"
```

This shows the navigation path between two concepts, revealing how your knowledge connects.

## Step 5: Maintain the Garden

Knowledge goes stale. Regularly check palace health:

```
/garden health ~/my-garden.json
```

This reports metrics like link density (are entries well-connected?) and freshness (when were entries last updated?).

Prune stale entries:

```
/palace prune --stale-days 90
```

This identifies entries older than 90 days, low-quality entries, and duplicates. It shows recommendations and **asks for your approval** before making any changes.

After reviewing:

```
/palace prune --apply
```

### Garden Metrics

Track the health of your knowledge base over time:

```
/garden metrics ~/my-garden.json --format brief
```

Output: `plots=42 link_density=3.2 avg_days_since_tend=4.5`

Healthy gardens have link density above 2.0 and average staleness under 7 days.

## Step 6: Use Knowledge in Reviews

The Memory Palace integrates with PR reviews through the review chamber:

```
/review-room
```

This captures review patterns and decisions, building a knowledge base of your team's code review preferences over time.

## What You've Learned

- **Palaces** organize knowledge by domain with architectural metaphors
- **Automatic capture** queues findings from research sessions
- **Sync** processes the queue into organized palace entries
- **Navigation** finds knowledge using semantic, exact, or fuzzy search
- **Maintenance** keeps the knowledge base healthy through pruning and metrics

## Command Reference

| Task | Command | Description |
|------|---------|-------------|
| Create | `/palace create <name> <domain>` | Create a new palace |
| List | `/palace list` | See all palaces |
| Status | `/palace status` | Queue size and health |
| Sync | `/palace sync` | Process intake queue |
| Search | `/navigate search "<query>"` | Find across palaces |
| Locate | `/navigate locate "<concept>"` | Find specific concept |
| Path | `/navigate path "<from>" "<to>"` | Show concept connections |
| Health | `/garden health <path>` | Assess garden health |
| Prune | `/palace prune` | Clean stale entries |
| Metrics | `/garden metrics <path>` | Track garden health |

---

**Difficulty:** Intermediate
**Prerequisites:** [Your First Session](skills-showcase.md), Memory Palace plugin installed
**Duration:** 15 minutes
