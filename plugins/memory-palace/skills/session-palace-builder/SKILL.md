---
name: session-palace-builder
description: Builds session-scoped temporary memory palaces for extended conversations. Use when tracking state across interruptions in a multi-step project.
alwaysApply: false
category: session-management
tags:
- session
- context
- project-memory
- conversation-state
- temporary-storage
dependencies:
- memory-palace-architect
scripts: []
usage_patterns:
- session-context
- project-tracking
- state-management
complexity: intermediate
model_hint: standard
estimated_tokens: 500
---

# Session Palace Builder

Construct temporary, session-specific memory palaces for extended conversations and complex projects. Preserves context across interruptions and enables structured information accumulation.

## What It Is

Session palaces are lightweight, temporary memory structures that:
- Preserve context for extended conversations
- Track decisions and their rationale
- Organize project artifacts spatially
- Enable context recovery after interruptions
- Support collaborative information gathering

## Quick Start

### Build Commands
\`\`\`bash
# Run build
make build

# Clean and rebuild
make clean && make build
\`\`\`

### Testing
\`\`\`bash
# Run tests
make test

# Run with verbose output
make test VERBOSE=1
\`\`\`

**Verification**: Run `make test` to confirm the plugin gate passes.
## When To Use

- Extended conversations requiring context preservation
- Complex, multi-step projects with interrelated components
- Workflows requiring state management across interactions
- Collaborative sessions accumulating information over time
- Code review or debugging sessions with many findings

## When NOT To Use

- Permanent knowledge structures
  needed - use memory-palace-architect
- Searching existing knowledge
  - use knowledge-locator
- Permanent knowledge structures
  needed - use memory-palace-architect
- Searching existing knowledge
  - use knowledge-locator

## Session Palace Templates

| Template | Purpose | Key Areas |
|----------|---------|-----------|
| **Workshop** | Active development | Workbench, tools, materials |
| **Library** | Research and analysis | Stacks, reading room, archives |
| **Council Chamber** | Decision-making | Round table, evidence wall, vote board |
| **Observatory** | Exploration and discovery | Telescope, star charts, log book |
| **Forge** | Implementation tasks | Anvil, cooling rack, finished goods |

## Information Categories

Organize session content into these standard areas:

- **Conversations** - Dialogue threads and key exchanges
- **Decisions** - Choices made with rationale
- **Code** - Snippets and technical artifacts
- **Research** - Findings and references
- **Requirements** - Specifications and constraints
- **Progress** - Completed milestones
- **Issues** - Blockers and challenges
- **Next Steps** - Pending action items

## Core Workflow

1. **Analyze Context** - Assess session scope and complexity
2. **Design Palace** - Select template and layout
3. **Structure State** - Organize information spatially
4. **Build Navigation** - Create access shortcuts
5. **Test Integration** - Verify context preservation

## Session Lifecycle

```
Create → Populate → Navigate → Export/Archive
   ↑         ↓          ↓
   └─── Checkpoint ←────┘
```
**Verification:** Run the command with `--help` flag to verify availability.

## Clarity Checkpoints

A session palace decays silently: each `Populate` step can add
ambiguity that only surfaces at `Export`, when it is too late to
recover the lost state. MMPO (arXiv:2605.30159, Section 3) frames
this as a case for sub-trajectory dense rewards: check intermediate
quality at each transition, not just the final outcome.

At every `Checkpoint` arrow in the lifecycle above (and before any
`Export/Archive`), run the dual-probe gate against the current
palace state:

```
Skill(memory-palace:memory-clarity-probe)
```

The probe returns a `Clarity Assessment` with progress/gap verdicts
and a `Recommendation`:

| Recommendation | Action at the checkpoint |
|----------------|--------------------------|
| Proceed | Palace state is clear; continue the session |
| Expand memory | Add the gap probe's open items to the palace before continuing |
| Regenerate | Flag the session as ambiguous: the progress probe hedges, so reconstruct the current-state room before more work lands on it |

Flagging at the checkpoint, not at export, is the point: an
ambiguous palace caught early costs one room rebuild; caught at
export it costs the session.

When `memory-clarity-probe` is not installed, ask the two anchor
questions inline (progress: what is done and what state is the task
in; gap: what concrete items remain) and apply the same table.

## Detailed Resources

- **Template Details**: See `modules/templates.md`
- **State Management**: See `modules/templates.md`
- **Export Patterns**: See `modules/templates.md`

## Integration

- `memory-palace-architect` - Export important concepts to permanent palaces
- `knowledge-locator` - Search session content
- `digital-garden-cultivator` - Seed garden with session insights
- `memory-clarity-probe` - Dual-probe clarity gate at session checkpoints

## Exit Criteria

- [ ] A session palace is created with a template and spatial layout
  before any state is populated
- [ ] The dual-probe clarity gate runs at each `Checkpoint` transition
  and before `Export/Archive`, not only at the end
- [ ] A checkpoint returning `Expand memory` or `Regenerate` is acted
  on (gap items added or current-state room rebuilt) before more work
  lands, and the ambiguous session is flagged
- [ ] Exported concepts round-trip into a permanent palace via
  `memory-palace-architect`
