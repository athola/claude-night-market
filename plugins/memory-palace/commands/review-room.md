# /review-room Command

Manage PR review knowledge in project memory palaces.

## Usage

```bash
# Capture knowledge from a PR
/review-room capture <pr_number> [options]

# Search the review chamber
/review-room search "<query>" [options]

# List entries
/review-room list [options]

# View entry details
/review-room view <entry_id>

# Export for documentation
/review-room export [options]

# Statistics
/review-room stats
```

## Subcommands

### capture

Capture PR review knowledge into the review chamber.

```bash
# Capture from PR (auto-detects repo)
/review-room capture 42

# Capture to specific room
/review-room capture 42 --room decisions

# Force capture (skip evaluation threshold)
/review-room capture 42 --force

# Interactive selection
/review-room capture 42 --interactive

# From GitHub URL
/review-room capture https://github.com/owner/repo/pull/42
```

**Options:**
| Option | Description |
|--------|-------------|
| `--room <type>` | Target room: decisions, patterns, standards, lessons |
| `--force` | Capture even if below threshold |
| `--interactive` | Select which findings to capture |
| `--tags <tags>` | Add additional tags (comma-separated) |

### search

Search the review chamber for knowledge.

```bash
# Semantic search
/review-room search "authentication"

# Filter by room
/review-room search "error handling" --room patterns

# Filter by tags
/review-room search "api" --tags security

# Filter by date
/review-room search "performance" --since 2025-01-01

# Search specific project
/review-room search "cache" --palace <project_id>
```

**Options:**
| Option | Description |
|--------|-------------|
| `--room <type>` | Filter by room type |
| `--tags <tags>` | Filter by tags |
| `--since <date>` | Entries after date (YYYY-MM-DD) |
| `--before <date>` | Entries before date |
| `--palace <id>` | Search specific project palace |
| `--limit <n>` | Max results (default: 10) |

### list

List entries in the review chamber.

```bash
# List all entries
/review-room list

# List by room
/review-room list --room decisions

# List recent
/review-room list --limit 5 --sort created

# List by access count
/review-room list --sort access_count
```

**Options:**
| Option | Description |
|--------|-------------|
| `--room <type>` | Filter by room |
| `--limit <n>` | Max entries to show |
| `--sort <field>` | Sort by: created, access_count, title |
| `--palace <id>` | Specific project palace |

### view

View details of a specific entry.

```bash
# View by entry ID
/review-room view abc123

# View in markdown format
/review-room view abc123 --format markdown

# View with related entries
/review-room view abc123 --related
```

**Options:**
| Option | Description |
|--------|-------------|
| `--format <fmt>` | Output format: json, markdown, yaml |
| `--related` | Include related entries |

### export

Export review chamber content.

```bash
# Export all to markdown
/review-room export --format markdown --output docs/review-decisions.md

# Export specific room
/review-room export --room decisions --format markdown

# Export as JSON
/review-room export --format json --output data/reviews.json
```

**Options:**
| Option | Description |
|--------|-------------|
| `--format <fmt>` | Output: markdown, json, yaml |
| `--output <path>` | Output file path |
| `--room <type>` | Filter by room |
| `--palace <id>` | Specific project palace |

### stats

Show review chamber statistics.

```bash
# Overall stats
/review-room stats

# Stats for specific palace
/review-room stats --palace <project_id>

# Detailed breakdown
/review-room stats --detailed
```

## Examples

### Capture Decisions from PR

```bash
> /review-room capture 42

Analyzing PR #42 for knowledge capture...

Found 3 candidates:

| # | Title | Score | Room |
|---|-------|-------|------|
| 1 | JWT over sessions | 95 | decisions |
| 2 | Token refresh pattern | 77 | patterns |
| 3 | API error format | 72 | standards |

Capture all? [Y/n/select]: y

✓ Captured 3 entries to review-chamber
  - abc123: decisions/jwt-over-sessions
  - def456: patterns/token-refresh
  - ghi789: standards/api-error-format
```

### Search Past Decisions

```bash
> /review-room search "authentication"

Found 5 entries:

| Room | Title | PR | Date |
|------|-------|-----|------|
| decisions | JWT over sessions | #42 | 2025-01-15 |
| patterns | Token refresh | #67 | 2025-02-20 |
| patterns | Rate limiting | #55 | 2025-01-28 |
| standards | Auth testing | #48 | 2025-01-20 |
| lessons | Token expiry outage | #89 | 2025-03-01 |

View details: /review-room view <entry_id>
```

### Context-Aware Search

```bash
> /review-room search --context auth/

Starting work in auth/ directory...

📚 Relevant Review Knowledge:

**Past Decisions:**
- [#42] JWT over sessions → decisions/jwt-over-sessions
- [#67] Token refresh pattern → patterns/token-refresh

**Quality Standards:**
- [#48] Auth testing conventions → standards/auth-testing

**Known Patterns:**
- [#55] Rate limiting → patterns/rate-limiting
```

### Export for Documentation

```bash
> /review-room export --room decisions --format markdown

Exported 12 decision entries to docs/review-decisions.md

Preview:
# Architectural Decisions from PR Reviews

## JWT over sessions
**Source:** PR #42 - Add authentication
**Date:** 2025-01-15

Chose JWT tokens over server-side sessions for stateless scaling...

---
```

## Integration

This command integrates with:

- **`sanctum:pr-review`**: Automatic capture after reviews
- **`memory-palace:review-chamber`**: Storage and evaluation
- **`memory-palace:knowledge-locator`**: Search across palaces

## Configuration

Settings in `~/.config/memory-palace/settings.json`:

```json
{
  "review_chamber": {
    "auto_capture": true,
    "capture_threshold": 60,
    "require_confirmation": true,
    "default_project": null
  }
}
```
