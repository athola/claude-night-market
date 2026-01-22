# War Room Specification: Data Structures

**Part of**: [War Room Specification](war-room-spec-overview.md)

---

## Anonymization with Merkle-DAG

### Rationale

Research shows LLMs exhibit "self-preference bias" - favoring their own outputs. Anonymization eliminates this while maintaining full traceability for post-decision analysis.

### Data Structure

```python
from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

@dataclass
class DeliberationNode:
    """A single contribution in the deliberation graph."""

    node_id: str           # SHA-256 hash of content + metadata
    parent_id: Optional[str]  # Previous version (for revisions)
    round_number: int      # Which deliberation round
    phase: str             # intel, coa, red_team, vote, etc.

    # Anonymized during deliberation
    anonymous_label: str   # "Response A", "Expert 2", etc.
    content: str           # The actual contribution

    # Revealed after decision
    expert_role: str       # "Intelligence Officer", "Red Team", etc.
    expert_model: str      # "gemini-2.5-pro", "qwen-turbo", etc.

    # Merkle linkage
    content_hash: str      # SHA-256 of content only
    metadata_hash: str     # SHA-256 of role + model
    combined_hash: str     # SHA-256 of content_hash + metadata_hash

    timestamp: str         # ISO format


@dataclass
class MerkleDAG:
    """
    Directed Acyclic Graph tracking deliberation history.

    Properties:
    - Each node is content-addressable via its hash
    - Parent links create revision history
    - Root hash summarizes entire deliberation
    - Attribution is masked until root is "unsealed"
    """

    session_id: str
    root_hash: Optional[str] = None
    nodes: dict[str, DeliberationNode] = field(default_factory=dict)

    def get_anonymized_view(self) -> list[dict]:
        """Return contributions with attribution masked."""

    def unseal(self) -> list[dict]:
        """Reveal full attribution after decision is made."""
```

### Version Tracking Across Rounds

```
Round 1                    Round 2                    Round 3
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ COA-A (v1)   │────────▶ │ COA-A (v2)   │────────▶ │ COA-A (v3)   │
│ hash: abc123 │  revises │ hash: def456 │  revises │ hash: ghi789 │
│ parent: null │          │ parent: abc123│          │ parent: def456│
└──────────────┘          └──────────────┘          └──────────────┘

Root Hash (Round 3): SHA256(ghi789 + ... all leaf hashes)
```

---

## Aggregation and Synthesis

### Hybrid Method

```python
def aggregate_votes(votes: list[VoteResult]) -> AggregatedResult:
    """
    Hybrid aggregation: voting to narrow, then synthesis.

    Step 1: Collect rankings from all experts
    Step 2: Apply weighted scoring (equal weights by default)
    Step 3: Identify top 2-3 approaches
    Step 4: Check for meritocracy override
    Step 5: Pass to Chairman for synthesis
    """

    # Compute aggregate scores using Borda count
    scores = defaultdict(float)
    for vote in votes:
        for rank, approach_id in enumerate(vote.ranking):
            points = len(vote.ranking) - rank
            scores[approach_id] += points

    # Sort and return top 2-3 for synthesis
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return AggregatedResult(finalists=ranked[:3], full_ranking=ranked)
```

### Meritocracy Override

The Supreme Commander may override voting when:
- Expert with domain expertise strongly disagrees
- Voting converged on popular but flawed approach
- Critical insight from minority position
- Strategic considerations beyond tactical voting

Override MUST include written justification.

---

## Session Persistence

### Local JSON Cache

```json
{
  "session_id": "war-room-20260120-153022",
  "created_at": "2026-01-20T15:30:22Z",
  "status": "completed",
  "problem_statement": "...",

  "configuration": {
    "mode": "lightweight",
    "escalated": true,
    "escalation_reason": "High architectural complexity detected",
    "deliberation_rounds": 2,
    "experts_invoked": ["strategist", "intel_officer", "red_team"]
  },

  "merkle_dag": {
    "root_hash": "a1b2c3d4...",
    "nodes": { ... }
  },

  "phases": {
    "intel": { "status": "complete", "artifacts": [...] },
    "assessment": { "status": "complete", "artifact": "..." },
    "coa_development": { "status": "complete", "coas": [...] },
    "red_team": { "status": "complete", "challenges": [...] },
    "voting": { "status": "complete", "results": {...} },
    "premortem": { "status": "complete", "failure_modes": [...] },
    "synthesis": { "status": "complete", "decision": {...} }
  },

  "final_decision": {
    "selected_approach": "Approach B",
    "rationale": "...",
    "dissenting_views": [...],
    "watch_points": [...]
  },

  "metrics": {
    "total_tokens": 145000,
    "total_cost_usd": 8.50,
    "duration_seconds": 342,
    "experts_consulted": 5
  }
}
```

### Strategeion Archive Structure

```
~/.claude/memory-palace/strategeion/
├── war-table/
│   └── war-room-20260120-153022/
│       ├── session.json
│       ├── intelligence/
│       │   ├── scout-report.md
│       │   └── intel-officer-report.md
│       ├── battle-plans/
│       │   ├── coa-a.md
│       │   ├── coa-b.md
│       │   └── coa-c.md
│       ├── wargames/
│       │   ├── red-team-challenges.md
│       │   └── premortem-analysis.md
│       └── orders/
│           └── final-decision.md
│
├── campaign-archive/
│   └── claude-night-market/
│       └── 2026-01-20-war-room-feature/
│
└── doctrine/
    ├── patterns/
    │   └── escalation-triggers.md
    └── lessons/
        └── 2026-01-20-multi-llm-deliberation.md
```

---

**Next**: See [Integration](war-room-spec-integration.md) for conjure and command specs.
