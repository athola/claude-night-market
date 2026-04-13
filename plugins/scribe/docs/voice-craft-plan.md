# Voice Craft Implementation Plan

## Phase 1: Foundation (Storage + Extraction)

### T1: Storage model and manifest
- Create ~/.claude/voice-profiles/ directory structure
- manifest.json schema (samples list, metadata, dates)
- Helper functions for profile CRUD operations
- Per-project .voice/ detection and merge logic

### T2: Voice extraction skill (SICO Phase 1)
- Sample intake (directory scan + interactive paste)
- Sample anonymization (strip labels, number sequentially)
- Baseline generation (Claude's default on matched topics)
- Comparative extraction prompt (what does writer do differently?)
- Pressure-test pass (force specificity, reject generic output)
- Write extraction.md to profile

### T3: Register creation from extraction
- Parse extraction into register format
- Default register auto-created from extraction
- Additional registers via focused re-extraction on subset

## Phase 2: Generation

### T4: Voice generation skill
- Source material framing ("raw notes to think through")
- Register selection (default or named)
- Craft rules application (detection-neutral techniques only)
- Banned phrases enforcement (pre-generation filter)
- Model routing (Opus for generation)

### T5: Commands for extract and generate
- /voice-extract command (intake + extraction workflow)
- /voice-generate command (source material + register)

## Phase 3: Review Agents

### T6: Prose reviewer agent
- AI vocabulary detection (tier system from slop-detector)
- Frictionless transition detection
- Structural monotony detection
- Voice drift scoring against register features
- Hard fail auto-fix vs advisory table output

### T7: Craft reviewer agent
- 5-dimension evaluation framework
- Rating system (Strong/Adequate/Opportunity)
- Proposed improvement generation
- Advisory table output format

### T8: Voice review skill (orchestrator)
- Dispatch prose + craft reviewers in parallel
- Merge results into unified output
- Present advisory tables to user
- Apply accepted fixes

## Phase 4: Learning Loop

### T9: Snapshot system
- Pre-review text capture
- Post-review (user-accepted) capture
- Manually-edited final capture
- Diff generation between stages

### T10: Learning agent
- Pattern extraction from edit diffs
- Register update proposals with evidence
- Accumulator for below-threshold patterns
- Accumulator review on subsequent passes

## Phase 5: Integration

### T11: Plugin registration
- Add skills to plugin.json
- Add agents to plugin.json
- Add commands to plugin.json
- Update scribe openpackage.yml

### T12: Documentation
- Extraction guide (how to collect good samples)
- Usage guide (generation workflow)
- Learning loop guide

## Execution Order

T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8 -> T9 -> T10 -> T11 -> T12

Parallelizable: T6 + T7 (independent agents)
Parallelizable: T9 + T10 (can develop together)
