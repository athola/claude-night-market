# War Room Specification: Architecture

**Part of**: [War Room Specification](war-room-spec-overview.md)

---

## The Strategeion: Memory Palace Integration

### Concept: The War Palace

The **Strategeion** (Greek: στρατηγεῖον, "general's headquarters") is a dedicated chamber within the Memory Palace for strategic deliberation. It extends the existing palace metaphor with spaces for war council sessions.

### Architectural Metaphor

```
memory-palace/
├── entrance/           # README, getting started
├── library/            # Documentation, ADRs
├── workshop/           # Development patterns
├── review-chamber/     # PR Reviews (existing)
├── garden/             # Evolving knowledge
│
└── strategeion/        # NEW: War Palace
    ├── war-table/      # Active deliberation sessions
    │   └── {session-id}/
    │       ├── intelligence/   # Expert reports
    │       ├── battle-plans/   # Courses of action
    │       ├── wargames/       # Red team challenges
    │       └── orders/         # Final decisions
    │
    ├── campaign-archive/  # Historical sessions
    │   └── {project}/
    │       └── {decision-date}/
    │
    ├── doctrine/          # Strategic principles learned
    │   ├── patterns/      # Recurring decision patterns
    │   └── lessons/       # Post-campaign analysis
    │
    └── armory/            # Expert configurations
        ├── panels/        # Saved expert compositions
        └── protocols/     # Custom deliberation flows
```

### The Crucible

Within the Strategeion, **The Crucible** is where raw ideas are pressure-tested:

```mermaid
flowchart TD
    PS[PROBLEM STATEMENT<br/>Central Hub]

    PS --> IR[INTELLIGENCE<br/>REPORTS<br/>Gemini]
    PS --> SP[STRATEGY<br/>PROPOSALS<br/>Sonnet]
    PS --> FA[FEASIBILITY<br/>ASSESSMENTS<br/>GLM-4.7]

    IR --> RT[RED TEAM<br/>CHALLENGE<br/>Gemini Flash]
    SP --> RT
    FA --> RT

    RT --> PM[PREMORTEM<br/>ANALYSIS]

    PM --> SC[SUPREME<br/>COMMANDER<br/>SYNTHESIS<br/>Opus]
```

### Integration Commands

```bash
# Access the Strategeion
/memory-palace:strategeion

# Review past campaigns
/memory-palace:strategeion archive --project claude-night-market

# Extract doctrine from campaign
/memory-palace:strategeion doctrine --extract {session-id}
```

---

## System Components

```mermaid
flowchart TB
    subgraph WAR_ROOM["WAR ROOM SYSTEM"]
        CMD["/attune:war-room"]
        SKL["Skill(attune:war-room)"]
        CMD --> SKL

        subgraph ORCH["WAR ROOM ORCHESTRATOR"]
            SM[Session management]
            ED[Expert dispatch]
            RA[Response aggregation]
            MT[Merkle-DAG tracking]
            SI[Strategeion integration]
        end

        SKL --> ORCH

        ORCH --> DEL_GEM["DELEGATION<br/>EXECUTOR<br/>Gemini"]
        ORCH --> DEL_QWEN["DELEGATION<br/>EXECUTOR<br/>Qwen"]
        ORCH --> DEL_GLM["CLAUDE CLI<br/>--model<br/>GLM-4.7"]

        subgraph STRAT["MEMORY PALACE: STRATEGEION"]
            SP2[Session persistence]
            CA[Campaign archive]
            DE[Doctrine extraction]
        end
    end
```

---

## Data Flow

```mermaid
flowchart TD
    UR[User Request] --> SI[Session Initialize<br/>Generate session_id<br/>Create Merkle root]

    SI --> P1[Phase 1: Intel<br/>Scout + Intel Officer<br/>gather context]

    P1 --> P2[Phase 2: Situation<br/>Assessment<br/>Chief Strategist<br/>synthesizes intel]

    P2 --> P3[Phase 3: COA<br/>Development<br/>Multiple experts<br/>generate approaches]

    P3 --> CR{Commander Review<br/>Lightweight?}

    CR -->|No| ESC[Escalate to Full<br/>Council?]
    ESC --> CR

    CR -->|Yes| P4[Phase 4: Red Team<br/>+ Wargaming<br/>Adversarial review]

    P4 --> P5[Phase 5: Voting<br/>+ Narrowing<br/>Hybrid aggregation<br/>to top 2-3]

    P5 --> P6[Phase 6: Premortem<br/>Analysis<br/>Imagine failure<br/>on selected COA]

    P6 --> P7[Phase 7: Supreme<br/>Commander Decision<br/>Final synthesis<br/>+ rationale]

    P7 --> PS[Persist to<br/>Strategeion<br/>JSON + archive]
```

---

**Next**: See [Expert Panel](war-room-spec-experts.md) for expert roles and escalation.
