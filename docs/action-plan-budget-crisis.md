# Action Plan: Budget Crisis Resolution
**Priority**: 🔴 CRITICAL
**Deadline**: Before v1.1.2 release
**Status**: In Progress

---

## Problem Statement

The Claude Night Market ecosystem **exceeds Claude Code's default system prompt budget by 202 characters** (15,202 / 15,000). This causes skills and commands beyond the budget to be silently excluded from Claude's awareness, resulting in unreliable skill activation.

**Impact**: Users report certain skills "not working" or "not triggering" - particularly those alphabetically later like `spec-kit` and `sanctum` commands.

---

## Immediate Actions (Completed ✅)

- [x] **Update skills-eval troubleshooting module** with budget information
- [x] **Add budget warning to README** with required environment variable
- [x] **Create ecosystem evaluation report** with detailed analysis
- [x] **Identify top budget offenders** and optimization targets

---

## Priority 1: User Communication (Week 1)

### 1. Update Installation Documentation

**Status**: ✅ DONE

Added prominent warning section in README:
- Clear explanation of budget issue
- Required environment variable setup
- Why it matters (invisible skills)
- Link to detailed evaluation

### 2. Add Troubleshooting Guide

**Status**: ⏳ TODO

Create `/docs/troubleshooting.md` with:
- Budget issues section
- Skill not triggering diagnostics
- Common installation problems
- LSP setup issues

**Assignee**: TBD
**Estimate**: 2 hours

### 3. Update Plugin READMEs

**Status**: ⏳ TODO

Add budget note to each plugin's README (13 plugins):
- sanctum (highest impact - 30 components)
- spec-kit (late alphabetically)
- archetypes (consolidation candidate)
- Others as needed

**Assignee**: TBD
**Estimate**: 1 hour

---

## Priority 2: Quick Wins (Week 1-2)

### 4. Optimize Verbose Descriptions

**Status**: ⏳ TODO

Target top 5 offenders for immediate reduction:

| Component | Current | Target | Savings |
|-----------|---------|--------|---------|
| abstract/validate-plugin (cmd) | 264 | 150 | 114 |
| sanctum/pr-review (cmd) | 247 | 150 | 97 |
| sanctum/tutorial-updates (skill) | 194 | 120 | 74 |
| sanctum/doc-updates (skill) | 187 | 120 | 67 |
| leyline/usage-logging (skill) | 160 | 100 | 60 |
| **TOTAL SAVINGS** | | | **412 chars** |

**Impact**: Brings usage to **14,790 / 15,000** (98.6%) - within budget!

**Assignee**: TBD
**Estimate**: 3 hours

**Guidelines**:
- Keep only trigger keywords in description
- Move explanatory content to skill body
- Format: "Action + target + when to use"
- Target: <150 chars for commands, <120 chars for skills

### 5. Document Description Writing Standards

**Status**: ⏳ TODO

Update `abstract/skills/skill-authoring/modules/description-writing.md` with:
- Character budget awareness
- Trigger keyword optimization
- Budget calculation examples
- Common bloat patterns to avoid

**Assignee**: TBD
**Estimate**: 2 hours

---

## Priority 3: Structural Optimization (Month 1)

### 6. Consolidate Architecture Paradigm Skills

**Status**: ⏳ TODO

**Current State**: 13 separate skills, 1,823 total chars
- architecture-paradigm-layered
- architecture-paradigm-microservices
- architecture-paradigm-event-driven
- ... (10 more)

**Proposed State**: 1 interactive selector skill
- Single entry point: `architecture-paradigms` (already exists!)
- Conditional loading of specific paradigm content
- Module-based organization

**Savings**: ~1,500 description characters (82% reduction in archetypes budget)

**Implementation**:
1. Enhance existing `architecture-paradigms` skill with interactive selector
2. Move individual paradigm content to modules
3. Deprecate individual paradigm skills
4. Update documentation

**Assignee**: TBD
**Estimate**: 1 day
**Risk**: Low (paradigm selector already exists)

### 7. Review sanctum Command Structure

**Status**: ⏳ TODO

**Analysis**: 30 components using 3,407 chars (23% of total budget)

**Potential Consolidations**:
- `pr`, `pr-review`, `fix-pr` → Single `pr-workflow` with modes?
- `update-docs`, `update-readme`, `update-tutorial` → `update-documentation` with targets?
- Consider skill vs command trade-offs

**Approach**:
1. Analyze usage patterns (which commands used together?)
2. Identify natural groupings
3. Prototype consolidated versions
4. Gather user feedback

**Assignee**: TBD
**Estimate**: 2 days
**Risk**: Medium (high usage area, backward compatibility concerns)

---

## Priority 4: Long-Term Infrastructure (Quarter 1)

### 8. Build Budget Monitoring Tools

**Status**: ⏳ TODO

Create `abstract/commands/check-budget.md`:
- Scan all plugins for description lengths
- Calculate total budget usage
- Identify components approaching limits
- Suggest optimizations

Enhance `abstract/skills-eval` with:
- Budget analysis module
- Per-plugin budget tracking
- Automated optimization suggestions

**Assignee**: TBD
**Estimate**: 3 days

### 9. Add Pre-Commit Budget Validation

**Status**: ⏳ TODO

Create `.git/hooks/pre-commit` (or GitHub Action):
- Check description field lengths
- Validate total budget usage
- Block commits that exceed limits
- Provide optimization suggestions

**Assignee**: TBD
**Estimate**: 1 day

### 10. Implement CI/CD Validation

**Status**: ⏳ TODO

Add GitHub Action workflow:
- Run on all PRs
- Validate plugin structure
- Check budget compliance
- Generate budget impact reports
- Block merges if budget exceeded

**Assignee**: TBD
**Estimate**: 2 days

---

## Priority 5: Strategic Optimization (Quarter 2)

### 11. Modularize Large Monolithic Skills

**Candidates**:
- `memory-palace/knowledge-intake` (498 lines)
- `scry/media-composition` (271 lines)

**Approach**: Convert to hub-and-spoke pattern with progressive loading

**Assignee**: TBD
**Estimate**: 1 week

### 12. Develop Skill Composition Patterns

**Goal**: Enable complex workflows without large descriptions

**Approach**:
- Skill chaining mechanisms
- Workflow DSL for common patterns
- Macro/alias system for compound commands

**Assignee**: TBD
**Estimate**: 2 weeks

---

## Success Metrics

### Phase 1 (Week 1)
- [ ] Budget warning in README
- [ ] Top 5 descriptions optimized
- [ ] Total usage < 15,000 chars (within budget)
- [ ] User-facing documentation updated

### Phase 2 (Month 1)
- [ ] Architecture paradigm consolidation complete
- [ ] Budget monitoring tools available
- [ ] Description writing standards documented
- [ ] Total usage < 13,500 chars (10% buffer)

### Phase 3 (Quarter 1)
- [ ] Pre-commit validation active
- [ ] CI/CD pipeline validates budget
- [ ] All plugins follow description standards
- [ ] Zero budget-related skill activation issues reported

---

## Rollback Plan

If optimization causes issues:

1. **Immediate**: Users can set `SLASH_COMMAND_TOOL_CHAR_BUDGET=30000`
2. **Short-term**: Revert specific optimizations via git
3. **Long-term**: Request Claude Code to increase default budget

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes to descriptions | Medium | High | Careful testing, gradual rollout |
| User confusion during transition | High | Medium | Clear communication, migration guide |
| Consolidation reduces discoverability | Low | Medium | Enhance selector UX, maintain cross-references |
| Budget limits future growth | Medium | High | Establish 10% buffer, monitor proactively |

---

## Communications Plan

### Week 1
- GitHub Issue: Budget crisis discovered, plan in progress
- README updated with immediate workaround
- Discord/Slack: Announce findings and user action

### Week 2
- Blog post: Technical deep-dive on budget limits
- Tutorial: How to optimize skill descriptions
- Video: Quick setup guide for new users

### Month 1
- Release notes: v1.1.2 with budget optimizations
- Migration guide: For plugin authors
- Best practices: Maintaining budget efficiency

---

## Next Steps

1. **Review this plan** with core team
2. **Assign priorities 1-2** to specific contributors
3. **Set up project tracking** (GitHub Projects?)
4. **Schedule check-ins** (weekly for first month)
5. **Begin communication rollout** (start with README update ✅)

---

**Created**: 2025-12-31
**Last Updated**: 2025-12-31
**Owner**: Plugin Development Team
**Status**: Active Development
