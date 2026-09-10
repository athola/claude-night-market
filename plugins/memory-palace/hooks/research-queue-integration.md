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

> Implemented by `research_queue.py` in this directory and registered
> on `SessionEnd` in `hooks.json`. The sections below describe the
> contract; the script is the behavior. Thresholds live in
> `research_queue.py` as `MIN_WEB_SEARCHES` and `QUEUE_DIR`.

## Purpose

Automatically captures research session outputs into the knowledge corpus queue for later evaluation, preventing loss of valuable findings.

## Trigger Conditions

This hook activates when ALL conditions are met:

1. **Session contains web research**: At least 3 WebSearch or
   WebFetch tool calls, counted from the session transcript
2. **Research-focused prompt**: A prompt the user typed includes
   keywords like:
   - "research", "investigate", "deep dive"
   - "brainstorm", "explore", "analyze"
   - "find tools", "best practices", "patterns"
3. **NOT already queued**: No queue entry exists for this session

The SessionEnd payload carries a `transcript_path` and nothing else
about the session: no prompt, no tool list, no counts. The transcript
is where both conditions are read from. Records marked `isMeta` are
skipped, because an expanded slash command or skill body is long
enough to contain a research cue the user never typed.

## Behavior

### Detection Phase

```python
# Shape of the detection, implemented in research_queue.py
searches, topic = _transcript_signal(payload["transcript_path"])
if searches >= MIN_WEB_SEARCHES and topic:
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

3. **Leaves the queue file as the only record**:

   The hook is registered `async`, so it outlives the session it
   describes and nothing it prints reaches a transcript. Claude Code
   bounds the SessionEnd batch by `max(1500ms, max timeout declared in
   settings-level hooks)`, a ceiling a plugin's own `timeout` does not
   raise, and interpreter startup alone can exceed it. A synchronous
   registration is cancelled before the hook does any work.

   Review the queue directly:

   ```bash
   ls -1t docs/knowledge-corpus/queue/*.yaml
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
    "research",
    "investigate",
    "deep dive",
    "detailed",
    "brainstorm",
    "explore",
    "analyze",
    "study",
    "find tools",
    "best practices",
    "patterns",
    "techniques",
    "survey",
    "landscape",
    "comparison",
    "evaluation",
]
```

### Thresholds
```python
MIN_WEB_SEARCHES = 3  # Minimum searches to trigger
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
1. User: "/superpowers:brainstorming bloat detection research"
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
