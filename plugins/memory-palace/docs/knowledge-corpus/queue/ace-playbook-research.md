# ACE Playbook Research: Semantic Memory Patterns for Memory Palace

**Research Date**: 2026-01-13
**Source**: https://github.com/jmanhype/ace-playbook
**Issue**: #7 - Investigate ace-playbook for memory-palace improvements
**Status**: COMPLETED

## Executive Summary

The ACE Playbook project implements semantic memory and reasoning capabilities that could significantly enhance the memory-palace plugin. Key innovations include semantic deduplication, counter-based reinforcement, and guardrails-as-sensors patterns.

## Key Findings

### 1. Semantic Deduplication via FAISS

**Current Gap in Memory Palace**: Memory palace stores knowledge without semantic similarity checking, potentially leading to redundant entries.

**ACE Pattern**:
- Uses FAISS (Facebook AI Similarity Search) with 0.8 cosine similarity threshold
- When similar insights emerge, increments counters rather than creating duplicates
- Mirrors how human memory reinforces patterns through repetition

**Recommended Integration**:
```python
# Proposed enhancement for memory-palace
class SemanticDeduplicator:
    """Prevent redundant knowledge storage using embedding similarity."""

    SIMILARITY_THRESHOLD = 0.8  # From ACE research

    def should_store(self, new_content: str, existing_embeddings: list) -> bool:
        """Check if content is semantically distinct from existing knowledge."""
        new_embedding = self.embed(new_content)
        for existing in existing_embeddings:
            if cosine_similarity(new_embedding, existing) > self.SIMILARITY_THRESHOLD:
                return False  # Increment counter instead
        return True
```

### 2. Generator-Reflector-Curator Triad

**Pattern Description**:
- **Generator**: Executes reasoning chains (ReAct/CoT patterns)
- **Reflector**: Analyzes outcomes, extracting labeled insights (Helpful/Harmful/Neutral)
- **Curator**: Deduplicates semantically similar knowledge using FAISS indices

**Memory Palace Mapping**:
| ACE Component | Memory Palace Equivalent |
|---------------|-------------------------|
| Generator | Skill execution / knowledge-intake |
| Reflector | Post-intake evaluation / marginal-value-filter |
| Curator | Digital garden cultivator / knowledge-librarian agent |

### 3. Domain Isolation Strategy

**Key Innovation**: Per-tenant namespaces with separate FAISS indices prevent category collapse.

**Application to Memory Palace Rooms**:
```
memory-palace/
├── review-chamber/     # Separate index for PR reviews
├── lessons/            # Separate index for learnings
├── patterns/           # Separate index for patterns
└── decisions/          # Separate index for decisions
```

Each "room" should maintain its own semantic index to prevent cross-contamination of knowledge domains.

### 4. Counter-Based Reinforcement

**Instead of duplicating, track access frequency**:
```json
{
  "content": "Always validate user input before processing",
  "counters": {
    "helpful": 15,
    "harmful": 0,
    "neutral": 2
  },
  "first_seen": "2026-01-01",
  "last_accessed": "2026-01-13"
}
```

**Benefits**:
- Surfaces frequently-reinforced knowledge
- Natural importance scoring via counter ratios
- Preserves decision history without bloat

### 5. Guardrails-as-Sensors Model

**Pattern**:
1. **Detect** precision failures (e.g., ±0.4% drift in calculations)
2. **Distill** signals into tactical lessons
3. **Persist** typed deltas with counters
4. **Reuse** via runtime adapter to prevent repeated errors

**Application to Memory Palace**:
- Attach guardrails to high-stakes retrievals
- Certify knowledge freshness before surfacing to LLM
- Chain domain-specific heuristics for validation

### 6. Performance Constraints

ACE maintains strict performance budgets:
- **≤10ms P50** for playbook retrieval
- **≤+15% overhead** for end-to-end operations

Memory palace hooks should respect similar constraints to avoid impacting Claude Code responsiveness.

## Recommended Enhancements

### Priority 1: Semantic Deduplication (High Value)
- Integrate FAISS or similar for semantic similarity checking
- Use 0.8 threshold for deduplication decisions
- Implement counter increment instead of duplicate storage

### Priority 2: Room-Based Indices (Medium Value)
- Separate semantic indices per memory palace room
- Prevent cross-domain knowledge bleed
- Enable domain-specific retrieval optimization

### Priority 3: Counter-Based Importance (Medium Value)
- Add helpful/harmful/neutral counters to knowledge entries
- Use counter ratios for retrieval ranking
- Implement vitality decay based on access patterns

### Priority 4: Guardrail Cascades (Lower Priority)
- Add validation hooks for high-stakes domains
- Implement freshness certification for retrieved knowledge
- Chain guardrails for complex retrievals

## Implementation Roadmap

| Phase | Enhancement | Effort | Impact |
|-------|-------------|--------|--------|
| 1 | Counter-based reinforcement | Low | Medium |
| 2 | Per-room semantic indices | Medium | High |
| 3 | Semantic deduplication | High | High |
| 4 | Guardrail cascades | Medium | Medium |

## References

- ACE Playbook: https://github.com/jmanhype/ace-playbook
- FAISS: https://github.com/facebookresearch/faiss
- DSPy Modules: Used for reasoning chains

## Next Steps

1. Create GitHub issues for each recommended enhancement
2. Prototype semantic deduplication in knowledge-intake skill
3. Add counter fields to existing knowledge storage schema
4. Benchmark performance impact of FAISS integration
