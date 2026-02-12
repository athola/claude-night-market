# Model Optimization Guide

Recommendations for which Claude models to use for different plugin tasks.

## Model Selection Framework

| Model | Use For | Latency | Cost | Context |
|-------|---------|---------|------|---------|
| **Haiku** | Validation, formatting, lookup, counting | Fast | Low | 200K |
| **Sonnet** | Moderate analysis, code generation, summaries | Medium | Medium | 200K |
| **Opus 4.6** | Deep reasoning, architecture, creative tasks | Slow | High | 200K (1M beta) |

### Opus 4.6 Capabilities (Claude Code 2.1.32+)

Opus 4.6 introduces features that affect model selection strategy:

- **Adaptive Thinking**: `thinking: {type: "adaptive"}` lets Claude decide when and how deeply to think
- **Effort Controls**: 4 levels — `low`, `medium`, `high` (default), `max` — trade reasoning depth against speed/cost
- **128K Max Output**: Significantly larger output window for complex generation tasks
- **Server-Side Compaction**: Automatic context summarization on the API side, enabling effectively infinite conversations
- **1M Context Window (Beta)**: Available for workloads requiring massive context

### Effort Controls as an Alternative to Model Escalation

Instead of always escalating haiku→sonnet→opus, consider effort controls on Opus 4.6:

| Approach | When to Use | Trade-off |
|----------|-------------|-----------|
| **Haiku→Sonnet→Opus** | Cost-sensitive workflows, high-volume automation | Cheapest per-token, but model switching adds complexity |
| **Opus@low→@high→@max** | Quality-sensitive workflows, complex orchestration | Higher per-token cost, but simpler single-model pipeline |
| **Hybrid** | Mixed workloads | Haiku for deterministic tasks, Opus with effort controls for reasoning tasks |

The hybrid approach is recommended: use Haiku for Tier 1 deterministic tasks, and Opus 4.6 with adaptive effort for Tier 2/3 tasks that previously required sonnet-to-opus escalation.

## Decision Flowchart

```
Is the task deterministic (same input → same output)?
├── YES → Use Haiku
└── NO ↓

Does it require subjective judgment or nuanced reasoning?
├── YES → Use Opus 4.6 (effort: high or max)
└── NO ↓

Is it pattern matching with moderate complexity?
├── YES → Use Sonnet or Opus 4.6 (effort: low/medium)
└── NO → Use Opus 4.6 (default safe choice)
```

## Tier 1: Haiku Candidates (High Confidence)

These tasks are deterministic, rule-based, and don't require reasoning:

### Abstract Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `validate-plugin` | command | JSON schema validation, path checks |
| `estimate-tokens` | command | Token counting algorithm |
| `context-report` | command | File metrics and statistics |
| `analyze-hook` | command | Static analysis checks |
| `validate-hook` | command | Compliance rule checking |

### Sanctum Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `commit-msg` | command | Conventional commit formatting |
| `version-updates` | skill | Semantic versioning rules |
| `file-analysis` | skill | File structure enumeration |
| `git-workspace-review` | skill | Git status/diff parsing |

### Conservation Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `analyze-growth` | command | Git history metrics |
| `optimize-context` | command | Token budget calculations |
| `performance-monitoring` | skill | Metrics collection |
| `token-conservation` | skill | Budget tracking |

### Parseltongue Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `run-profiler` | command | Profiling output parsing |
| `python-packaging` | skill | Template/config generation |
| `python-performance` | skill | Pattern reference lookup |

### Memory-Palace Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `navigate` | command | Search and retrieval |
| `knowledge-locator` | skill | Index lookup |

### Leyline Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `error-patterns` | skill | Pattern reference |
| `mecw-patterns` | skill | Principle lookup |
| `progressive-loading` | skill | Template application |
| `pytest-config` | skill | Config generation |
| `quota-management` | skill | Quota calculations |
| `storage-templates` | skill | Template generation |
| `usage-logging` | skill | Log formatting |

### Archetypes Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| All `architecture-paradigm-*` | skills | Reference lookup (not design) |

### Imbue Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `evidence-logging` | skill | Log formatting |
| `structured-output` | skill | Output formatting |

## Tier 2: Sonnet Candidates (Moderate Complexity)

These involve pattern analysis with some judgment but not deep reasoning:

### Abstract Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `analyze-skill` | command | Structure analysis (not design) |
| `create-skill` | command | Template generation phase only |

### Sanctum Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `catchup` | command | Change enumeration + basic summary |
| `pr` | command | PR template population |
| `update-docs` | command | Doc structure updates |
| `update-readme` | command | README section updates |

### Imbue Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `catchup` | command | Change summary generation |
| `diff-analysis` | skill | Pattern categorization |

### Parseltongue Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `analyze-tests` | command | Coverage analysis |
| `check-async` | command | Pattern detection |
| `python-async` | skill | Pattern matching |
| `python-testing` | skill | Template application |

### Memory-Palace Plugin
| Component | Type | Rationale |
|-----------|------|-----------|
| `garden` | command | Curation workflow |
| `palace` | command | Structure creation |

## Tier 3: Keep on Opus (Deep Reasoning Required)

These require creative, architectural, or adversarial thinking:

### Pensive Plugin (ALL)
- All review commands require critical analysis
- `api-review`, `architecture-review`, `bug-review`, `math-review`, `rust-review`, `test-review`
- Deep domain expertise needed

### Spec-Kit Plugin (MOST)
- `specify`, `plan`, `clarify`, `tasks`, `analyze`, `constitution`, `implement`
- Architectural reasoning and design decisions

### Abstract Plugin
- `bulletproof-skill` - Adversarial thinking for anti-rationalization
- `skill-authoring` - Behavioral psychology for effectiveness
- `hook-authoring` - Security reasoning for hook design
- `skills-eval` - Nuanced quality assessment
- `hooks-eval` - Security/performance evaluation

### Imbue Plugin
- `review` - Evidence-driven critical thinking

### Memory-Palace Plugin
- `memory-palace-architect` - Architecture design

## Implementation Patterns

### Pattern 1: Agent with Explicit Model

When spawning agents for simple tasks:

```markdown
# In agent definition or when calling Task tool
Use model: haiku for this agent when:
- Task is validation or formatting
- Output is deterministic
- No subjective judgment needed
```

### Pattern 2: Hybrid Workflows

Split complex workflows into phases:

```
Phase 1 (Haiku): Gather data, validate inputs, format outputs
Phase 2 (Opus): Analyze, reason, decide
Phase 3 (Haiku): Format final output, generate reports
```

### Pattern 3: Escalation Path

```
Start with Haiku
├── If confidence < threshold → Escalate to Sonnet
│   └── If still uncertain → Escalate to Opus
└── Otherwise → Complete task
```

## Escalation Governance

Escalation (upgrading from a lower model to a higher one) must be principled, not convenient.

### Core Principle

**Escalation is for tasks that genuinely require deeper reasoning, not for "maybe a smarter model will figure it out."**

### Agent Schema

Agents declare escalation hints in frontmatter:

```yaml
model: haiku
escalation:
  to: sonnet                 # Suggested escalation target
  hints:                     # Advisory triggers (orchestrator may override)
    - security_sensitive     # Touches auth, secrets, permissions
    - ambiguous_input        # Multiple valid interpretations
    - novel_pattern          # No existing patterns apply
    - high_stakes            # Error would be costly
    - reasoning_required     # Needs judgment, not just pattern matching
```

### Escalation Hints Reference

| Hint | Description | Typical Use |
|------|-------------|-------------|
| `security_sensitive` | Task touches auth, secrets, permissions | Validation finding sensitive patterns |
| `ambiguous_input` | Multiple valid interpretations exist | Unclear requirements or specs |
| `novel_pattern` | No existing patterns apply | First-of-kind implementation |
| `high_stakes` | Error would be costly to fix | Production, breaking changes |
| `reasoning_required` | Needs judgment beyond pattern matching | Trade-off decisions |

### Orchestrator Authority

Hints are **advisory rules** - they should typically be followed, but the orchestrator can override based on broader context:

| Scenario | Orchestrator Action |
|----------|---------------------|
| Hint fires, context confirms complexity | Follow hint, escalate |
| Hint fires, task is actually simple | Override, stay at current model |
| No hint fires, orchestrator senses complexity | Override, escalate anyway |
| Hint suggests sonnet, opus is needed | Override target, go to opus |

### When NOT to Escalate

Escalation is never appropriate for:

| Anti-Pattern | Why It's Wrong | Correct Action |
|--------------|----------------|----------------|
| "Maybe smarter model will figure it out" | Thrashing, not reasoning | Investigate systematically |
| Multiple failed attempts | Wrong approach, not capability gap | Question your assumptions |
| Time pressure | Urgency ≠ complexity | Systematic is faster |
| "Just to be safe" | False safety, wastes resources | Assess actual complexity |

### Investigation Before Escalation

Before escalating, the agent/orchestrator must verify:

1. **Understanding**: Can articulate why current model is insufficient
2. **Investigation**: Systematic analysis was attempted
3. **Capability Gap**: Issue is reasoning depth, not knowledge or approach
4. **Proportionality**: Benefit justifies cost (latency, tokens, money)

See `skills/escalation-governance/SKILL.md` for the complete framework and pressure tests.

## Expected Impact

### Cost Reduction
- Tier 1 tasks (20+ components): ~70-80% cost reduction per invocation
- Tier 2 tasks (20+ components): ~40-50% cost reduction per invocation

### Latency Improvement
- Haiku: 2-5x faster response times
- Sonnet: 1.5-2x faster than Opus

### Quality Considerations
- Tier 1: No quality loss (deterministic tasks)
- Tier 2: Minimal quality impact with proper scoping
- Tier 3: Would significantly degrade quality - keep on Opus

## Monitoring Recommendations

Track these metrics after optimization:
1. Task success rate by model
2. Escalation frequency (Haiku → Opus)
3. User satisfaction with outputs
4. Cost per task category

## Context Management for Subagents

### Server-Side Compaction (Opus 4.6 / Claude Code 2.1.32+)

Opus 4.6 introduces **server-side context compaction** — the API automatically summarizes earlier conversation parts when context approaches the window limit. This is separate from Claude Code's client-side auto-compaction and provides an additional safety net for long-running workflows.

### Auto-Compaction (Claude Code 2.1.1+)

Subagent conversations automatically compact when context reaches ~160k tokens (on standard 200K windows). This is a system-level feature requiring no configuration. With the 1M context beta, thresholds scale proportionally.

**Log signature**:
```json
{
  "isSidechain": true,
  "type": "system",
  "subtype": "compact_boundary",
  "compactMetadata": { "trigger": "auto", "preTokens": 167189 }
}
```

### Design Implications

| Consideration | Guidance |
|--------------|----------|
| **Long-running subagents** | Safe - won't crash at context limits |
| **State preservation** | Write critical state to files, not just conversation |
| **Progress tracking** | Use TodoWrite or explicit checkpoints |
| **Context reliance** | Avoid depending on early conversation context for late decisions |

### Context Thresholds

| Usage | Behavior |
|-------|----------|
| < 80% (~128k) | Normal operation |
| 80-90% | Warning zone |
| > 90% | Compaction imminent |
| ~160k | Auto-compaction triggers |

See `conserve:context-optimization/modules/subagent-coordination` for detailed patterns.

## Migration Checklist

- [x] Identify agents that spawn for Tier 1 tasks
- [x] Add `model: haiku` parameter to those agents
- [x] Add `model: sonnet` parameter to Tier 2 agents
- [x] Add escalation hints to all optimized agents
- [ ] Test with representative inputs
- [ ] Monitor for quality regressions
- [ ] Track escalation frequency
- [ ] Expand to additional candidates if successful

## Implemented Agents

### Haiku Agents (with escalation to Sonnet)
| Plugin | Agent | Escalation Hints |
|--------|-------|------------------|
| abstract | plugin-validator | security_sensitive, novel_pattern |
| conserve | context-optimizer | ambiguous_input, high_stakes |
| memory-palace | knowledge-navigator | ambiguous_input, novel_pattern |
| sanctum | commit-agent | ambiguous_input, high_stakes |
| sanctum | git-workspace-agent | security_sensitive, high_stakes |

### Sonnet Agents (with escalation to Opus)
| Plugin | Agent | Escalation Hints |
|--------|-------|------------------|
| memory-palace | garden-curator | reasoning_required, novel_pattern |
| memory-palace | knowledge-librarian | reasoning_required, high_stakes |
| parseltongue | python-pro | reasoning_required, security_sensitive |
| parseltongue | python-tester | reasoning_required, novel_pattern |
| parseltongue | python-optimizer | reasoning_required, high_stakes |
| sanctum | pr-agent | reasoning_required, high_stakes, security_sensitive |

### Opus Agents (no escalation needed)
- All pensive agents (architecture-reviewer, code-reviewer, rust-auditor)
- All spec-kit agents (implementation-executor, spec-analyzer, task-generator)
- memory-palace: palace-architect
- imbue: review-analyst
- abstract: meta-architect, skill-auditor
