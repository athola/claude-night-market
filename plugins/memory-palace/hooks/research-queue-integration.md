---
name: research-queue-integration
description: |
  Automatically queue research sessions for knowledge corpus evaluation.
  Triggers after brainstorming sessions with WebSearch to prevent loss of
  valuable research.
triggers:
  - SessionEnd
priority: 40
enabled: true
---

# Research Queue Integration Hook

## Purpose

Automatically captures research session outputs into the knowledge corpus queue for later evaluation, preventing loss of valuable findings.

## Trigger Conditions

This hook activates when ALL conditions are met:

1. **Session contains WebSearch**: At least 3 WebSearch tool calls
2. **Research-focused context**: Session includes keywords like:
   - "research", "investigate", "deep dive"
   - "brainstorm", "explore", "analyze"
   - "find tools", "best practices", "patterns"
3. **Substantial output**: Session produced significant findings
4. **NOT already queued**: No queue entry exists for this session

## Behavior

### Detection Phase

```python
# Pseudocode for detection
if session.tool_calls.count('WebSearch') >= 3:
    if any(keyword in session.messages for keyword in RESEARCH_KEYWORDS):
        if session.output_length > 5000:  # Substantial output
            trigger_queue_creation()
```

### Queue Entry Creation

When triggered, the hook:

1. **Extracts Session Data**:
   - WebSearch queries and results
   - Key findings and summaries
   - Sources/URLs discovered
   - Topic/focus of research

2. **Generates Queue Entry**:
   - Creates YAML file in `docs/knowledge-corpus/queue/`
   - Filename: `YYYY-MM-DD_HH-MM-SS_topic-slug.yaml`
   - Includes metadata, findings summary, sources

3. **Emits Reminder**:
   ```
   📚 Research Session Queued for Knowledge Corpus

   Your research on "[topic]" has been saved to the corpus queue:
   - Queue entry: queue/2025-12-31_topic.yaml
   - Sources: [N] references found
   - Priority: high (recent research)

   Next steps:
   - Review queue: ls -1t docs/knowledge-corpus/queue/*.yaml
   - Process entry: Review and decide on storage
   - Or defer: Queue will persist for later review
   ```

### Queue Entry Template

```yaml
---
queue_entry_id: ${timestamp}_${topic_slug}
created_at: ${iso_timestamp}
session_type: research
topic: "${extracted_topic}"
status: pending_review
priority: high
auto_generated: true
web_searches: ${count}
---

# Research Session: ${topic}

## Context

${session_context}

## Web Searches Performed (${count} total)

${web_search_queries}

## Key Findings Summary

${extracted_findings}

## Sources (${url_count} total)

${unique_urls}

## Evaluation Scores (Auto-Generated)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Novelty | TBD | Review needed |
| Applicability | TBD | Review needed |
| Durability | TBD | Review needed |
| Connectivity | TBD | Review needed |
| Authority | TBD | Review needed |

## Routing Recommendation

Type: TBD (requires curator review)

## Next Actions

- [ ] Review findings for accuracy
- [ ] Score using knowledge-intake rubric
- [ ] Decide on storage location
- [ ] Create memory palace entry if approved
- [ ] Extract reusable patterns
```

## Safety Checks

Before creating queue entry, validate:

1. **No Duplicates**: Check if similar topic already queued
2. **Content Quality**: Verify findings are coherent
3. **Size Limits**: validate entry is reasonable size (< 100KB)
4. **No Secrets**: Scan for API keys, credentials

## Configuration

### Research Keywords
```python
RESEARCH_KEYWORDS = [
    'research', 'investigate', 'deep dive', 'detailed',
    'brainstorm', 'explore', 'analyze', 'study',
    'find tools', 'best practices', 'patterns', 'techniques',
    'survey', 'landscape', 'comparison', 'evaluation'
]
```

### Thresholds
```python
MIN_WEB_SEARCHES = 3        # Minimum searches to trigger
MIN_OUTPUT_LENGTH = 5000    # Minimum output tokens
QUEUE_DIR = "docs/knowledge-corpus/queue/"
```

## Integration with Knowledge-Intake

This hook complements the `knowledge-intake` skill:

1. **Hook**: Auto-queues research sessions
2. **Skill**: Provides evaluation framework
3. **Curator**: Reviews queue and approves storage
4. **Agent** (`knowledge-librarian`): Processes approved entries

## Example Flow

```
1. User: "/superpowers:brainstorm bloat detection research"
2. Claude: Performs 8 WebSearch calls, compiles findings
3. [SessionEnd Hook Triggers]
4. Hook: Detects research session, creates queue entry
5. Hook: Emits reminder with queue location
6. User: Reviews queue at convenience
7. User: Approves entry via knowledge-intake
8. Agent: Creates memory palace entry
```

## Disabling

To disable auto-queueing:

```yaml
# In .claude-config.yaml or hook metadata
hooks:
  research-queue-integration:
    enabled: false
```

Or use environment variable:
```bash
export MEMORY_PALACE_AUTO_QUEUE=false
```

## Metrics

Track hook effectiveness:
- Queue entries created
- Approval rate (approved / total)
- Time to review (queue creation → processing)
- Corpus growth from queued research

## Future Enhancements

- [ ] Smart topic extraction using LLM
- [ ] Auto-scoring based on session context
- [ ] Duplicate detection via semantic similarity
- [ ] Integration with digital garden for seedlings
- [ ] Slack/email notifications for high-priority queues
