# Subagent Stability Testing - January 2026

**Purpose**: Verify Claude Code 2.1.16+ memory fixes benefit our subagent-heavy workflows
**Claude Code Version**: 2.1.17 (confirmed)
**Date**: 2026-01-23

## Background

Claude Code 2.1.16 fixed critical subagent memory issues:
- JavaScript heap out of memory crashes (#19100)
- Subagent process cleanup (#19045)
- Memory leaks during initialization (#7020)
- Memory issues from .claude logs (#19476)

## Testing Checklist

### Phase 1: Validate Stability (Immediate)

> **Session Analysis**: Based on review of 53 recent commits and session files (largest: 20MB),
> the most subagent-heavy workflows are: War Room (3-7 experts), Auto-Clear (continuation agents),
> and PR workflows with lifecycle hooks.

#### 1. War Room - Multi-Expert Deliberation (HIGH PRIORITY)

**Test**: `/attune:war-room` with multiple expert subagents

**Why Critical**: War Room spawns 3-7 parallel subagents (Opus, Sonnet, Gemini, GLM, Qwen).
This is the most memory-intensive workflow in the ecosystem.

| Test Case | Expected Behavior | Status |
|-----------|------------------|--------|
| Lightweight mode (3 experts) | All experts respond, no OOM | [ ] |
| Full Council (7 experts) | Parallel execution stable | [ ] |
| Delphi mode (iterative) | Multi-round convergence | [ ] |
| Session resume after War Room | Context preserved | [ ] |

**Commands to run**:
```bash
# Quick test - Express mode (1 expert)
/attune:war-room "Which logging library to use" --express

# Standard test - Lightweight mode (3 experts)
/attune:war-room "API versioning strategy" --assess-only

# Stress test - Full Council (7 experts)
/attune:war-room "Database migration to MongoDB" --full-council
```

**Monitor during test**:
```bash
# Watch subagent spawning (in separate terminal)
watch -n 2 'ps aux | grep -c "[c]laude"; ls ~/.claude/projects/-home-alext-claude-night-market/*/subagents 2>/dev/null | wc -l'
```

**Evidence to capture**:
- [ ] Number of subagents spawned
- [ ] Memory usage during multi-expert deliberation
- [ ] Clean termination after decision

---

#### 2. Auto-Clear - Continuation Agents (HIGH PRIORITY)

**Test**: `Skill(conserve:clear-context)` at 80% threshold

**Why Critical**: Auto-clear spawns continuation subagents to hand off work.
Historical issue: Memory leaks during subagent initialization (#7020).

| Test Case | Expected Behavior | Status |
|-----------|------------------|--------|
| Manual continuation trigger | State preserved in handoff | [ ] |
| Automatic 80% threshold | Clean subagent spawn | [ ] |
| Multiple continuations | No memory accumulation | [ ] |

**Commands to run**:
```bash
# Check current context usage
/context

# Trigger manual continuation (if needed)
Skill(conserve:clear-context)

# Check audit log
cat ${CLAUDE_CODE_TMPDIR:-/tmp}/clear-context-audit.log 2>/dev/null
```

**Evidence to capture**:
- [ ] Session state file created (`.claude/session-state.md`)
- [ ] Continuation subagent spawned successfully
- [ ] Work resumed without loss

---

#### 3. Attune Execute - TDD Enforcement (MEDIUM PRIORITY)

**Test**: `/attune:execute` with project-implementer agent (50 iterations)

**Why Critical**: Recent work added TDD gate enforcement (commit d9240fc).
Long-running execution tests subagent stability over time.

| Test Case | Expected Behavior | Status |
|-----------|------------------|--------|
| Execute 5+ tasks in sequence | No OOM crashes | [ ] |
| TDD red-green-refactor cycle | Gates enforced | [ ] |
| Resume from checkpoint | State restored | [ ] |

**Commands to run**:
```bash
# Start execution
/attune:execute

# Check execution state
cat .attune/execution-state.json 2>/dev/null | jq '.metrics'

# Monitor memory
free -h | grep Mem
```

**Evidence to capture**:
- [ ] Tasks completed count
- [ ] Memory trend over execution
- [ ] TDD gates enforced (evidence in logs)

---

#### 4. Sanctum PR - Lifecycle Hooks (MEDIUM PRIORITY)

**Test**: PR workflow with session_complete_notify and pr-agent hooks

**Why Critical**: Recent work split stop hook into modular components (commit 1839078).
Tests hook chain execution and subagent cleanup.

| Test Case | Expected Behavior | Status |
|-----------|------------------|--------|
| PR with 10+ changed files | Quality gates complete | [ ] |
| Multi-commit PR (like current branch) | All commits analyzed | [ ] |
| Hook chain execution | All hooks fire, no deadlock | [ ] |

**Commands to run**:
```bash
# Use current branch (already has changes)
git status

# Run PR prep
/sanctum:pr-prep

# Check hook audit logs
cat ${CLAUDE_CODE_TMPDIR:-/tmp}/pr-audit.log 2>/dev/null
```

**Evidence to capture**:
- [ ] PR description generated
- [ ] Notification fired (if enabled)
- [ ] Clean process termination

---

#### 5. Subagent Cleanup Verification (REQUIRED FOR ALL)

**Test**: Verify subagents terminate correctly after all workflows

| Test Case | Expected Behavior | Status |
|-----------|------------------|--------|
| After War Room | No orphan expert processes | [ ] |
| After Auto-Clear | Continuation agent exits | [ ] |
| After error/abort | Clean termination | [ ] |

**Baseline (run before tests)**:
```bash
# Record baseline
echo "Baseline: $(ps aux | grep -c '[c]laude') claude processes"
echo "Baseline: $(free -h | grep Mem)"
```

**After each test**:
```bash
# Check for orphans
ps aux | grep -E "[c]laude|[n]ode" | grep -v "skrills"

# Check subagent directories
find ~/.claude/projects/-home-alext-claude-night-market/ -name "subagents" -type d -exec ls {} \;
```

**Evidence to capture**:
- [ ] Process count returns to baseline
- [ ] Memory released
- [ ] No zombie processes

---

### Phase 2: Document Improvements (After Testing)

#### Observed Improvements

| Area | Before 2.1.16 | After 2.1.17 | Notes |
|------|---------------|--------------|-------|
| Session stability | TBD | TBD | |
| Memory usage | TBD | TBD | |
| Subagent cleanup | TBD | TBD | |
| Auto-compaction | TBD | TBD | |

#### Issues Found

| Issue | Severity | Workaround | Report To |
|-------|----------|------------|-----------|
| (none yet) | | | |

---

## Test Execution Log

### Test 1: Attune Execute

**Date/Time**: _______________
**Tester**: _______________

**Steps**:
1. [ ] Opened fresh Claude Code session
2. [ ] Invoked `/attune:execute` on test project
3. [ ] Monitored memory during execution
4. [ ] Verified task completion
5. [ ] Checked for orphan processes

**Results**:
```
(paste output here)
```

**Assessment**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

---

### Test 2: Spec-Kit Workflow

**Date/Time**: _______________
**Tester**: _______________

**Steps**:
1. [ ] Prepared specification document
2. [ ] Ran spec-analyzer
3. [ ] Ran task-generator
4. [ ] Checked for compaction events
5. [ ] Verified state preservation

**Results**:
```
(paste output here)
```

**Assessment**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

---

### Test 3: Sanctum PR Workflow

**Date/Time**: _______________
**Tester**: _______________

**Steps**:
1. [ ] Created test branch with changes
2. [ ] Invoked PR preparation workflow
3. [ ] Verified quality gates executed
4. [ ] Checked lifecycle hook logs
5. [ ] Confirmed clean termination

**Results**:
```
(paste output here)
```

**Assessment**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

---

### Test 4: Subagent Cleanup

**Date/Time**: _______________
**Tester**: _______________

**Steps**:
1. [ ] Recorded baseline process count
2. [ ] Ran multiple subagent workflows
3. [ ] Verified processes terminated
4. [ ] Checked memory trend
5. [ ] Confirmed no zombie processes

**Results**:
```
(paste output here)
```

**Assessment**: [ ] PASS / [ ] FAIL / [ ] PARTIAL

---

## Summary

**Overall Assessment**: [ ] ALL PASS / [ ] ISSUES FOUND / [ ] NEEDS RETEST

**Recommendations**:
- (fill in after testing)

**Next Steps**:
- [ ] Update CHANGELOG with test results
- [ ] Close Phase 1 testing items
- [ ] Begin Phase 2 exploration (if all pass)

---

## Related Documents

- [Ecosystem Update Summary](../ecosystem-update-summary-2026-01-23.md)
- [Claude Code 2.1.16 Impact Analysis](../claude-code-2.1.16-impact-analysis.md)
- [Subagent Coordination Module](../../plugins/conserve/skills/context-optimization/modules/subagent-coordination.md)
