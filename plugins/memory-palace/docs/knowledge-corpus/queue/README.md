# Knowledge Corpus Queue

Staging area for research and external content awaiting knowledge-intake evaluation.

## Purpose

The queue serves as an intermediate holding area for valuable content that needs review before being added to the main knowledge corpus. This prevents loss of research while maintaining quality standards through curator review.

## When Queue Entries Are Created

1. **After Research Sessions**: Brainstorming sessions with WebSearch automatically create queue entries
2. **Manual Addition**: User or Claude can manually add items for later review
3. **Bulk Import**: Processing multiple articles/papers at once
4. **Hook Triggers**: Memory palace hooks detecting valuable content

## Queue Entry Format

Each entry is a YAML file with metadata and content summary:

```yaml
---
queue_entry_id: YYYY-MM-DD_topic-slug
created_at: ISO-8601 timestamp
session_type: brainstorming|research|manual
topic: "Brief topic description"
status: pending_review|in_review|approved|rejected|processed
priority: low|medium|high|urgent
---

# Entry Title

## Context
Why this was queued...

## Key Findings Summary
Main insights...

## Evaluation Scores
Knowledge-intake rubric scores...

## Routing Recommendation
Where this should go...

## Sources
List of URLs and references...

## Next Actions
Checklist of follow-ups...
```

## Processing Queue

### Review Queue
```bash
ls -1t queue/*.yaml | head -10
```

### Process Single Entry
```bash
# Read entry
cat queue/2025-12-31_topic.yaml

# If approved for storage:
# 1. Create memory palace entry in docs/knowledge-corpus/
# 2. Update queue entry status to 'processed'
# 3. Move to queue/archive/ or delete

# If rejected:
# Update status to 'rejected' with rationale
```

### Batch Processing
```bash
# Future: CLI tool for batch processing
# uv run python scripts/process-queue.py --interactive
```

## Queue Statuses

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `pending_review` | Awaiting curator review | Review and decide |
| `in_review` | Currently being evaluated | Complete evaluation |
| `approved` | Approved for corpus | Create memory palace entry |
| `rejected` | Does not meet criteria | Archive with rationale |
| `processed` | Successfully added to corpus | Archive or delete |

## Priority Levels

| Priority | When | Response Time |
|----------|------|---------------|
| `urgent` | Time-sensitive, blocking work | Review within hours |
| `high` | High-value research, recent session | Review within 1-2 days |
| `medium` | Valuable but not urgent | Review within 1 week |
| `low` | Nice-to-have, reference material | Review when convenient |

## Maintenance

### Archive Old Entries
```bash
# Move processed entries to archive
mkdir -p queue/archive
mv queue/*-processed.yaml queue/archive/
```

### Clean Rejected Entries
```bash
# Remove rejected entries after review
rm queue/*-rejected.yaml
```

### Queue Health Check
```bash
# Count by status
grep -h "^status:" queue/*.yaml | sort | uniq -c

# Oldest pending entry
ls -t queue/*.yaml | tail -1
```

## Integration with Knowledge-Intake

The queue system integrates with the `knowledge-intake` skill:

1. **Auto-Queue**: Research sessions automatically populate queue
2. **Review Workflow**: `/knowledge-intake --process-queue` to review entries
3. **Approval Flow**: Curator approves/rejects each entry
4. **Storage**: Approved entries become memory palace entries

## Best Practices

1. **Review Regularly**: Check queue weekly to prevent buildup
2. **Prioritize**: Use priority field to focus on high-value content
3. **Be Selective**: Not everything needs to go in the corpus
4. **Update Status**: Keep status field accurate
5. **Archive Processed**: Move completed items to archive/

## Future Enhancements

- [ ] CLI tool for interactive queue processing
- [ ] Automatic priority scoring based on signals
- [ ] Queue dashboard showing age and priority
- [ ] Integration with memory palace hooks
- [ ] Duplicate detection before queueing
- [ ] Scheduled reminders for old pending items
