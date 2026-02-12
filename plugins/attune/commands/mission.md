---
name: mission
description: "Run the full attune project lifecycle as a single mission with automatic state detection, phase routing, and session recovery"
---

# Attune Mission Command

Orchestrate the entire attune development lifecycle — brainstorm, specify, plan, execute — as a single mission with automatic state detection and recovery.

## When To Use

Use this command when you need to:
- Start a new project and run through the full development lifecycle
- Resume an interrupted project workflow from where you left off
- Execute a focused tactical implementation from existing artifacts
- Quick-fix from an existing implementation plan

## When NOT To Use

Avoid this command if:
- You want to run a single phase without auto-chaining (use `/attune:brainstorm --standalone`, `/attune:specify --standalone`, etc.)
- Task is non-project work (debugging, code review, research)
- You need fine-grained control over each phase transition

> **Note**: Individual commands (`/brainstorm`, `/specify`, `/blueprint`) now auto-chain forward by default. Use `--standalone` to run a single phase without continuing. Use `/attune:mission` when you need state persistence, resume support, and damage-control.

## Usage

```bash
# Auto-detect mission type and start
/attune:mission

# Resume a paused or interrupted mission
/attune:mission --resume

# Override mission type
/attune:mission --type full
/attune:mission --type standard
/attune:mission --type tactical
/attune:mission --type quickfix

# Custom phase sequence
/attune:mission --phases brainstorm,execute

# Skip user checkpoints between phases
/attune:mission --auto
```

## What This Command Does

1. **Detects project state** — scans for existing artifacts (brief, spec, plan)
2. **Selects mission type** — chooses the appropriate phase sequence
3. **Routes through phases** — invokes `Skill(attune:{phase})` for each step
4. **Checkpoints between phases** — lets you review, pause, or adjust
5. **Handles errors** — recovers from failures via `leyline:damage-control`
6. **Saves mission state** — enables resume from any point

## Mission Types

| Type | Phases | When |
|------|--------|------|
| `full` | brainstorm → specify → plan → execute | No artifacts exist |
| `standard` | specify → plan → execute | Project brief exists |
| `tactical` | plan → execute | Specification exists |
| `quickfix` | execute only | Implementation plan exists |

## Workflow

```bash
# 1. Invoke mission orchestrator skill
Skill(attune:mission-orchestrator)

# 2. Orchestrator detects state and selects type:
#    "Detected: specification.md exists → tactical mission"

# 3. Routes through phases:
#    Phase 1: plan
#      → Skill(attune:project-planning)
#      → Produces: docs/implementation-plan.md
#      → Checkpoint: "Continue to execute? [Y/n]"
#
#    Phase 2: execute
#      → Skill(attune:project-execution)
#      → Produces: implemented code + tests

# 4. Mission complete, state saved to .attune/mission-state.json
```

## Session Recovery

Mission state is automatically saved to `.attune/mission-state.json`.

```bash
# Resume after interruption
/attune:mission --resume

# Force-resume a failed mission (resets failed phase)
/attune:mission --resume --force
```

The resume command:
1. Loads saved mission state
2. Validates artifacts still exist
3. Continues from the last completed phase
4. Displays a summary of progress so far

## Arguments

| Argument | Description |
|----------|-------------|
| `--type <type>` | Override auto-detected mission type: `full`, `standard`, `tactical`, `quickfix` |
| `--phases <list>` | Custom phase sequence (comma-separated): `brainstorm,specify,plan,execute` |
| `--resume` | Resume from saved mission state |
| `--force` | With `--resume`: reset failed phase and retry |
| `--auto` | Skip user checkpoints between phases |

## Integration with Full Cycle

```
/attune:mission              ← Orchestrates everything below
  ├─ /attune:brainstorm      ← Phase 1 (if full/standard)
  ├─ /attune:specify         ← Phase 2 (if full/standard)
  ├─ /attune:blueprint       ← Phase 3 (if full/standard/tactical)
  └─ /attune:execute         ← Phase 4 (always)
```

The mission command wraps the existing phase commands — you can still use individual commands for fine-grained control.

## Examples

### Example 1: Full New Project

```bash
/attune:mission
# Auto-detects: no artifacts → full mission
# Runs: brainstorm → specify → plan → execute
```

### Example 2: Tactical from Existing Spec

```bash
/attune:mission
# Auto-detects: specification.md exists → tactical mission
# Runs: plan → execute
```

### Example 3: Resume After Interruption

```bash
/attune:mission --resume
# Loads: .attune/mission-state.json
# Shows: "Resuming tactical mission, 12/24 tasks complete"
# Continues: execute phase from task T013
```

### Example 4: Force Full Lifecycle

```bash
/attune:mission --type full
# Ignores existing artifacts, starts from brainstorm
```

## Mission vs. Individual Command Chaining

| Capability | Individual Commands | `/attune:mission` |
|------------|--------------------|--------------------|
| Auto-chains forward | Yes (default) | Yes |
| `--standalone` opt-out | Yes | N/A |
| State persistence (`.attune/mission-state.json`) | No | Yes |
| Session resume (`--resume`) | No | Yes |
| Damage-control on failure (`leyline:damage-control`) | No | Yes |
| Risk classification (`leyline:risk-classification`) | No | Yes |
| Custom phase sequences (`--phases`) | No | Yes |
| User checkpoints between phases | Lightweight (non-blocking) | Interactive (can pause/adjust) |
| Auto-detect mission type from artifacts | No | Yes |

**When to use which**:
- **Individual commands**: Quick runs, familiar projects, no need for recovery — auto-chain handles the happy path
- **Mission**: New or complex projects, need resume support, want error recovery, or require artifact-based state detection

## Related Commands

- `/attune:brainstorm` - Run brainstorm phase independently
- `/attune:specify` - Run specification phase independently
- `/attune:blueprint` - Run planning phase independently
- `/attune:execute` - Run execution phase independently
- `/attune:war-room` - Strategic deliberation (used within phases)

## Related Skills

- `Skill(attune:mission-orchestrator)` - Orchestration methodology
- `Skill(leyline:risk-classification)` - Task risk assessment
- `Skill(leyline:damage-control)` - Error recovery
