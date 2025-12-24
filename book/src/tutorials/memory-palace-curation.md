# Memory Palace Curation Workflow

Learn how the research interceptor collaborates with knowledge-intake for effective curation.

## Prerequisites

- Memory Palace plugin installed
- Understanding of cache modes (see [Cache Modes](cache-modes.md))

## Objectives

By the end of this tutorial, you'll:

- Understand the intake flag payload
- Process the intake queue
- Use dual-output workflows
- Maintain curation quality

## The Intake Flow

When a research query runs, Memory Palace evaluates whether new information should be captured:

```
Query Execution
      |
      v
[Hook Evaluation]
      |
      +-- Build IntakeFlagPayload
      |   - should_flag_for_intake
      |   - novelty_score
      |   - domain_alignment
      |   - duplicate_entry_ids
      |
      v
[Decision]
      |
      +-- High novelty + domain match --> Flag for intake
      |
      +-- Low novelty or duplicate --> Skip intake
      |
      v
[Output]
      - Telemetry row
      - Queue entry (if flagged)
```

## Step 1: Understanding IntakeFlagPayload

The `IntakeFlagPayload` dataclass tracks three signals:

| Field | Description |
|-------|-------------|
| `should_flag_for_intake` | Should this query be queued? |
| `novelty_score` | Heuristic for new information (0-1) |
| `domain_alignment` | Matches against interests config |

```python
# memory_palace/curation/models.py
@dataclass
class IntakeFlagPayload:
    should_flag_for_intake: bool
    novelty_score: float
    domain_alignment: List[str]
    duplicate_entry_ids: List[str]
    intake_delta_reasoning: str
```

## Step 2: Monitoring the Hook

The hook outputs intake context to the runtime transcript:

```
[Memory Palace Intake]
Novelty: 0.75
Domains: python, async
Duplicates: []
Flag: True
Reasoning: High novelty content in aligned domain
```

## Step 3: Processing the Intake Queue

When `should_flag_for_intake=True`, the hook writes to:

```
data/intake_queue.jsonl
```

Process the queue:

```bash
# View pending items
cat data/intake_queue.jsonl | jq .

# Process with CLI
uv run python skills/knowledge-intake/scripts/intake_cli.py \
  --queue data/intake_queue.jsonl \
  --review
```

## Step 4: Intake Decision Options

For each queued item:

| Action | When to Use |
|--------|-------------|
| **Accept** | High value, unique information |
| **Merge** | Similar to existing entry |
| **Reject** | Low value or duplicate |
| **Defer** | Need more context |

```bash
# Accept item
uv run python intake_cli.py --item abc123 --accept

# Merge with existing
uv run python intake_cli.py --item abc123 --merge entry-456

# Reject
uv run python intake_cli.py --item abc123 --reject
```

## Step 5: Using Dual-Output Mode

Generate both palace entry and developer documentation:

```bash
uv run python intake_cli.py \
  --candidate /tmp/candidate.json \
  --dual-output \
  --prompt-pack marginal-value-dual \
  --auto-accept
```

This creates:
1. **Palace entry**: Stored in corpus
2. **Developer doc**: Added to `docs/`
3. **Prompt artifact**: Saved to `docs/prompts/<pack>.md`

## Step 6: Telemetry Review

Check telemetry for intake patterns:

```bash
# View recent decisions
tail -20 data/telemetry/memory-palace.csv
```

Columns include:
- `novelty_score`
- `aligned_domains`
- `intake_delta_reasoning`
- `duplicate_entry_ids`

## Curation Best Practices

### Regular Review Cadence

1. **Daily**: Check intake queue
2. **Weekly**: Review telemetry patterns
3. **Monthly**: KonMari session (prune low-value entries)

### Document Decisions

Update `docs/curation-log.md` after each session:

```markdown
## 2025-01-15 Curation Session

### Promoted
- async-patterns.md: High usage, evergreen

### Merged
- context-managers.md + async-context.md: Redundant

### Archived
- python-3.8-features.md: Outdated
```

### Maintain Vitality Scores

Keep `data/indexes/vitality-scores.yaml` current:

```yaml
entries:
  async-patterns:
    vitality: evergreen
    last_accessed: 2025-01-15
  python-3.8-features:
    vitality: probationary
    last_accessed: 2024-06-01
```

## Troubleshooting

### Too many intake flags

**Solution**: Raise intake threshold

```yaml
# In config
intake_threshold: 0.7  # Higher = fewer flags
```

### Missing domain alignment

**Solution**: Update domains of interest

```yaml
# hooks/shared/config.py
domains_of_interest:
  - python
  - async
  - testing
  - architecture
```

### Duplicate detection failing

**Solution**: Rebuild indexes

```bash
uv run python scripts/build_indexes.py
```

## Verification

Confirm the workflow:

1. Make a research query
2. Check telemetry for decision
3. View intake queue if flagged
4. Process queue item
5. Verify corpus update

```bash
# After processing
ls docs/knowledge-corpus/ | grep new-entry
```

## Next Steps

- Return to [Plugin Overview](../plugins/README.md)
- Explore [Capabilities Reference](../reference/capabilities-reference.md)

<div class="achievement-unlock" data-achievement="curation-complete">
Achievement Unlocked: Knowledge Curator
</div>
