# Phase 4: Knowledge Queue Promotion Check

Check the memory-palace research queue for items needing
evaluation.

## Step 1: Scan Queue for Pending Items

```bash
ls -lt plugins/memory-palace/docs/knowledge-corpus/queue/*.md 2>/dev/null | head -20
```

Check for:

- `webfetch-*.md` - Auto-captured web content
- `websearch-*.md` - Auto-captured search results
- Any file with `status: pending_review` in frontmatter

## Step 2: Report Queue Status

Display pending items using this format:

```markdown
## Knowledge Queue Status

### Pending Review (X items)
| File | Age | Topic | Priority |
|------|-----|-------|----------|
| webfetch-article-name-2026-01-15.md | 2 days | "Article Title" | medium |
| websearch-query-2026-01-10.md | 7 days | "Search Query" | medium |

### Action Required
- [ ] 3 items older than 7 days - review or archive
- [ ] 1 high-priority item awaiting decision
```

## Step 3: Prompt for Evaluation

For each pending item older than 3 days:

1. Display summary (topic, source, content preview)
2. Request decision:
   - Promote: Move to `knowledge-corpus/` (outside queue),
     update index
   - Archive: Move to `queue/archive/` with rejection
     rationale
   - Defer: Keep in queue, optionally adjust priority
3. Execute decision (move file, update frontmatter)

Example evaluation prompt:

```
Queue Item: webfetch-claude-plugins-guide-2026-01-10.md (7 days old)
Topic: "Claude Code Plugin Development Guide"
Source: https://docs.anthropic.com/plugins/guide
Content: 2,340 chars

Decision options:
  [P]romote to knowledge-corpus/
  [A]rchive (not valuable)
  [D]efer (review later)
  [S]kip (next item)
```

## Step 4: Execute Promotions

For items marked for promotion:

```bash
# 1. Move from queue to corpus
mv plugins/memory-palace/docs/knowledge-corpus/queue/webfetch-*.md \
   plugins/memory-palace/docs/knowledge-corpus/

# 2. Update frontmatter status
# Change: status: pending_review -> status: processed

# 3. Rename to permanent filename (remove webfetch- prefix, timestamp)
# webfetch-article-name-2026-01-15.md -> article-name.md
```

## Step 5: Track Decisions

Create TodoWrite items for each promotion decision:

```
queue-review:promoted:<filename>
queue-review:archived:<filename>
queue-review:deferred:<filename>
```

To skip queue check: use `--skip-queue` flag.
