# ADR 0005: Attune Plugin Discoverability Enhancement

## Status

Accepted - 2026-02-05

## Context

Skills, commands, and agents in the attune plugin were not consistently discovered by Claude when users made relevant prompts or requests. Research of the obra/superpowers plugin revealed proven discoverability patterns that significantly improve automatic component matching.

### Research Findings

Official Claude Code specification analysis revealed:
- **Only the `description` field** is used for skill/command/agent matching
- All other frontmatter fields (`category`, `tags`, `complexity`, etc.) are custom metadata for our ecosystem only
- Token budget: 15,000 chars total for all skill descriptions combined across the entire plugin ecosystem
- Attune target: < 3,000 chars (20% of ecosystem budget) for proportional allocation

### Problem Statement

Users would:
- Type "I want to start a new project" but attune:brainstorm wouldn't trigger
- Ask "how do I compare approaches?" without project-brainstorming being suggested
- Request "design the architecture" without project-architect agent being invoked
- Experience workflow confusion due to unclear skill boundaries

## Decision

Implement a **hybrid approach** combining:

1. **Template Development**: Create reusable templates for skills, commands, and agents
2. **Incremental Rollout**: Pilot → High-Priority → Remaining (4 phases)
3. **Description Formula**: WHAT + WHEN + WHEN NOT pattern
4. **Token Management**: Target 100-200 chars per description with monitoring

### Description Pattern

Universal formula for all component types:
```
[WHAT it does]. Use when: [keyword1, keyword2, scenario]. Do not use when: [boundary].
```

**Example** (project-brainstorming skill):
```yaml
description: "Guide project ideation through Socratic questioning and constraint analysis to create actionable project briefs. Use when: starting projects, exploring problem spaces, comparing approaches, validating feasibility. Do not use when: requirements already clear and specification exists."
```

### Content Structure

Every enhanced component includes:

**Skills**:
- "When To Use" section (5-7 specific scenarios)
- "When NOT To Use" section (3-4 boundaries with alternatives)
- Custom metadata clearly separated with comment

**Commands**:
- Similar structure but more concise (50-150 char descriptions)
- Action-oriented language (imperative verbs)
- Clear workflow positioning

**Agents**:
- Capability-focused descriptions (75-175 char target)
- "When To Invoke" section (5 delegation scenarios)
- Tool permissions and model specifications

## Implementation

### Phase Breakdown

| Phase | Components | Duration | Chars | Status |
|-------|-----------|----------|-------|--------|
| Phase 0: Foundation | Templates + Guide | 3 hours | N/A | ✅ Complete |
| Phase 1: Pilot | 3 (skill, cmd, agent) | 4 hours | 691 | ✅ Complete |
| Phase 2: High-Pri Skills | 4 skills | 4 hours | 1,196 | ✅ Complete |
| Phase 3: High-Pri Commands | 4 commands | 4 hours | 431 | ✅ Complete |
| Phase 4: Remaining | 9 mixed | 6 hours | 1,602 | ✅ Complete |
| Phase 5: Documentation | README, CHANGELOG, ADR | 5 hours | N/A | ✅ Complete |
| **Total** | **20 components** | **26 hours** | **3,920** | **✅ Complete** |

### Coverage

- ✅ 9/9 skills enhanced (100%)
- ✅ 9/9 commands enhanced (100%)
- ✅ 2/2 agents enhanced (100%)
- **Total: 20/20 components (100% plugin coverage)**

### Critical Discovery: YAML Quoting

Descriptions containing colons (e.g., "Use when: starting projects") **must be quoted** to prevent YAML parse errors:

```yaml
# ✗ WRONG - breaks YAML
description: Use when: starting projects

# ✓ CORRECT
description: "Use when: starting projects"
```

## Consequences

### Positive

- ✅ **Improved Auto-Discovery**: Users' natural language requests now trigger appropriate attune components
- ✅ **Reduced False Positives**: "When NOT To Use" boundaries prevent skill misuse
- ✅ **Consistent Patterns**: All components follow same discoverability structure
- ✅ **Reusable Templates**: Future additions can use validated templates
- ✅ **Clear Workflow**: Explicit cross-references guide users through brainstorm → specify → plan → execute
- ✅ **Documentation**: Contributor templates in `plugins/attune/templates/`

### Negative

- ⚠️ **Time Investment**: 26 hours total implementation time
- ⚠️ **Budget Variance**: 3,920 chars (130.7% of 3,000 target) due to 43% more components than planned
  - *Mitigated*: When adjusted for actual component count, usage is 91.4% of proportional budget
- ⚠️ **Maintenance**: Ongoing need to maintain pattern consistency for new components

### Neutral

- ℹ️ **Custom Metadata**: Fields like `category`, `tags`, `complexity` documented as non-functional for matching
- ℹ️ **Token Budgets**: Require monitoring with conserve tools (`/conserve:estimate-tokens`)
- ℹ️ **Template Evolution**: Phase 1 pilot refined templates based on learnings

## Validation

### Manual Discovery Testing

| Test Prompt | Expected Match | Result |
|-------------|----------------|--------|
| "I want to start a new web app project" | `/attune:brainstorm` | ✅ Pass |
| "How do I compare technical approaches?" | `Skill(attune:project-brainstorming)` | ✅ Pass |
| "Create a specification from requirements" | `/attune:specify` | ✅ Pass |
| "Design the system architecture" | `Agent(attune:project-architect)` | ✅ Pass |
| "Should I convene a war room?" | `Skill(attune:war-room)` | ✅ Pass |
| "Execute my implementation plan" | `/attune:execute` | ✅ Pass |

### Technical Validation

- ✅ 100% YAML frontmatter valid (all descriptions quoted)
- ✅ All components have "When To Use" sections
- ✅ All components have "When NOT To Use" sections (except agents which use "When To Invoke")
- ✅ Token budget: 3,920 chars across 20 components (avg 196 chars/component)
- ✅ No breaking changes to existing references

## Alternatives Considered

### Alternative 1: Keyword Tags Only

**Approach**: Use frontmatter tags for discoverability
```yaml
tags: [brainstorming, ideation, planning]
```

**Rejected Because**:
- Research confirmed tags are not used by Claude for matching
- Only `description` field affects discovery
- Would waste implementation time on non-functional approach

### Alternative 2: Verbose Descriptions

**Approach**: Very long descriptions (400-500 chars) with all possible triggers

**Rejected Because**:
- Exceeds token budget quickly (15k chars for entire ecosystem)
- Diminishing returns beyond 200 chars
- Harder to maintain and read
- Phase 1 pilot showed 150-200 chars sufficient for complex skills

### Alternative 3: Big Bang Rollout

**Approach**: Enhance all 20 components at once without pilot

**Rejected Because**:
- No validation of pattern effectiveness before full rollout
- High risk of template errors affecting all components
- No opportunity to refine templates based on learnings
- Incremental approach allowed template evolution (e.g., YAML quoting discovery)

## References

- Brainstorm session: `.claude/brainstorm-attune-discoverability.md`
- Pattern catalog: `.claude/discoverability-patterns-summary.md`
- Official spec findings: `.claude/frontmatter-spec-findings.md`
- Implementation plan: `docs/implementation-plan-attune-discoverability-v1.4.0.md`
- Templates: `plugins/attune/templates/`
- Superpowers plugin: `~/.claude-code/plugins/superpowers/` (reference implementation)

## Lessons Learned

1. **YAML Syntax Critical**: Colons in descriptions require quoting - caught in Phase 1 pilot
2. **Budget Flexibility**: Initial 3,000 char target was for ~14 components; actual 20 components required proportional adjustment
3. **Pattern Success**: WHAT/WHEN/WHEN NOT formula effective across all component types (skills, commands, agents)
4. **Template Value**: Pilot phase template refinement prevented issues in later phases
5. **Cross-References**: "When NOT To Use" sections valuable for workflow guidance (e.g., "use `/attune:plan` instead")

## Future Work

1. **Extend to Other Plugins**: Apply pattern to sanctum, conserve, imbue, etc.
2. **Automated Validation**: Create pre-commit hook validating new skills against template
3. **Discovery Metrics**: Track which prompts trigger which components to refine keywords
4. **Pattern Evolution**: Monitor effectiveness and evolve formula based on usage data
5. **Token Budget Monitoring**: Periodic review with `/conserve:estimate-tokens` as ecosystem grows

---

**Date**: 2026-02-05
**Author**: Claude Sonnet 4.5
**Reviewers**: Attune Plugin Maintainers
**Status**: Implemented and Validated
