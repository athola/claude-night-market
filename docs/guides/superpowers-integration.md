# Superpowers Integration Guide for Night-Market Plugins

This guide documents the integration of superpowers marketplace skills with the night-market plugin ecosystem.

**Last Updated:** 2026-01-23
**Superpowers Version:** v4.1.0
**Spec-Kit Version:** v0.0.90

## Overview

The superpowers marketplace provides specialized skills that implement rigorous methodologies like RED-GREEN-REFACTOR, systematic debugging, and evidence-based operations. This integration enhances existing plugin capabilities without replacing them, creating a cohesive development workflow with better quality gates.

## Recent Updates (v4.0.0 - v4.1.0)

### Skill Consolidations (v4.0.0)

Several standalone skills were bundled into comprehensive skills. **Update your references:**

- ❌ `superpowers:root-cause-tracing` → ✅ `superpowers:systematic-debugging`
- ❌ `superpowers:defense-in-depth` → ✅ `superpowers:systematic-debugging`
- ❌ `superpowers:condition-based-waiting` → ✅ `superpowers:systematic-debugging`
- ❌ `superpowers:testing-skills-with-subagents` → ✅ `superpowers:writing-skills`
- ❌ `superpowers:testing-anti-patterns` → ✅ `superpowers:test-driven-development`
- ❌ `superpowers:sharing-skills` → Removed (obsolete)

### New Features (v4.0.x)

1. **Two-Stage Code Review** - Subagent workflows now use:
   - Stage 1: Spec compliance review (skeptical verification)
   - Stage 2: Code quality review (only after spec compliance passes)

2. **DOT Flowcharts** - Key skills now use executable DOT/GraphViz diagrams

3. **Strengthened Skill Invocation** (v4.0.3)
   - "Invoke relevant or requested skills" instead of "Check for skills"
   - "BEFORE any response or action"
   - New red flag: "I know what that means"

4. **Test Infrastructure** - New testing patterns:
   - Skill-triggering tests
   - Claude Code integration tests
   - End-to-end workflow tests

### Breaking Changes (v4.1.0)

1. **OpenCode Native Skills** - Switched to native `skill` tool (migration required)
2. **Windows Compatibility** - Fixed hook execution for Claude Code 2.1.x

**For full details:** [Superpowers Release Notes](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md)

## Integration Philosophy

### Core Principles
1. **Enhance, Don't Replace** - Superpowers skills elevate existing capabilities
2. **Evidence-Based Operations** - Every claim backed by verification
3. **Methodology Over Features** - Focus on how work is done, not just what is done
4. **Incremental Quality** - Small improvements with verification at each step

### Integration Patterns
1. **Direct Call** - Replace duplicate logic with superpowers skill calls
2. **Complementary Enhancement** - Add quality gates to existing workflows
3. **Workflow Integration** - Insert methodology steps into existing processes

## Plugin Integrations

### Abstract Plugin (Meta-Skills Infrastructure)

#### Components Enhanced
- `/create-skill` command - Already properly references `superpowers:brainstorming`
- `/create-command` command - Uses brainstorming for concept refinement
- `/create-hook` command - Uses brainstorming for security-first design

#### Superpowers Skills Added
- **superpowers:brainstorming** - Socratic questioning for idea refinement
- **superpowers:writing-skills** - TDD for skill documentation (future)

### Spec-Kit Plugin (Spec Driven Development)

#### Components Enhanced
- `speckit-orchestrator` skill - Already has full superpowers dependencies
- `command-skill-matrix` - Already maps commands to superpowers skills
- `task-planning` skill - Uses writing-plans and executing-plans

#### Superpowers Skills Already Integrated
- **superpowers:brainstorming** - For specification refinement
- **superpowers:writing-plans** - For detailed implementation planning
- **superpowers:executing-plans** - For task execution with checkpoints
- **superpowers:systematic-debugging** - For implementation error handling
- **superpowers:verification-before-completion** - For artifact analysis

### Pensive Plugin (Code Review)

#### Components Enhanced
- `/full-review` command - Added systematic debugging and verification

#### Superpowers Skills Added
- **superpowers:systematic-debugging** - Four-phase framework for complex issues
- **superpowers:verification-before-completion** - Evidence-based review standards
- **superpowers:receiving-code-review** - Technical rigor for feedback processing

### Sanctum Plugin (Git & Workspace Operations)

#### Components Enhanced
- `/fix-pr` command - Added code review processing methodology

#### Superpowers Skills Added
- **superpowers:receiving-code-review** - Evaluate suggestions with technical rigor
- **superpowers:systematic-debugging** - For complex issue investigation
- **elements-of-style:writing-clearly-and-concisely** - For commit message clarity

### Parseltongue Plugin (Python Development)

#### Components Enhanced
- `python-testing` skill - Added TDD methodology and anti-pattern prevention

#### Superpowers Skills Added
- **superpowers:test-driven-development** - RED-GREEN-REFACTOR cycle
- **superpowers:testing-anti-patterns** - Prevent common testing mistakes
- **superpowers:systematic-debugging** - For test failure investigation
- **superpowers:verification-before-completion** - For test quality validation

### Minister Plugin (Project Management)

#### Components Enhanced
- `issue-management` skill - Added systematic debugging for bug reports

#### Superpowers Skills Added
- **superpowers:systematic-debugging** - Methodical bug investigation
- **superpowers:verification-before-completion** - Before issue resolution
- **superpowers:root-cause-tracing** - For recurring systemic issues

### Conservation Plugin (Resource Optimization)

#### Components Enhanced
- `/optimize-context` command - Added condition-based waiting and verification

#### Superpowers Skills Added
- **superpowers:condition-based-waiting** - Replace arbitrary timeouts
- **superpowers:verification-before-completion** - Before optimization claims
- **superpowers:systematic-debugging** - For context optimization issues

## Cross-Cutting Enhancements

### Quality Gates
All plugins now integrate:
- **superpowers:verification-before-completion** - Evidence before assertions
- **superpowers:systematic-debugging** - Standardized debugging approach

### Workflow Standards
Common patterns across plugins:
- TDD methodology for new development
- Evidence-based decision making
- Systematic problem investigation
- No rationalization or assumptions without proof

## Usage Examples

### Example 1: Creating a New Skill
```bash
# Abstract's create-skill command now:
/create-skill "async error handling"

# Automatically invokes:
I'll use superpowers:brainstorming to refine this skill idea...
```

### Example 2: Reviewing Code
```bash
# Pensive's full-review command now:
/full-review

# Automatically includes:
I'll use superpowers:verification-before-completion to validate all findings are evidence-based...
```

### Example 3: Fixing PR Comments
```bash
# Sanctum's fix-pr command now:
/fix-pr 123

# Automatically includes:
I'll use superpowers:receiving-code-review to evaluate suggestions with technical rigor...
```

### Example 4: Writing Tests
```bash
# Parseltongue's python-testing skill now:
I'll use superpowers:test-driven-development to follow RED-GREEN-REFACTOR...
```

## Implementation Checklist

### Phase 1: Quick Wins [DONE]
- [x] Abstract plugin brainstorming integration
- [x] Spec-kit dependency completion
- [x] Pensive review quality gates
- [x] Sanctum PR feedback processing
- [x] Parseltongue TDD methodology
- [x] Minister issue debugging
- [x] Conservation condition-based waiting

### Phase 2: Workflow Enhancements (Future)
- [ ] Add systematic debugging to all error handling
- [ ] Integrate defense-in-depth patterns across security-sensitive plugins
- [ ] Add parallel agent dispatch for multi-plugin operations
- [ ] Create unified completion workflows

### Phase 3: Advanced Features (Future)
- [ ] Centralized skill discovery and management
- [ ] Cross-plugin workflow orchestration
- [ ] Advanced analytics and optimization

## Benefits Realized

### Immediate Benefits
1. **Consistent Methodology** - All plugins follow evidence-based practices
2. **Higher Quality** - Systematic debugging and verification prevent issues
3. **Better Documentation** - Writing clarity enforced across plugins
4. **Reduced Duplication** - Common patterns centralized in superpowers

### Long-term Benefits
1. **Ecosystem Cohesion** - Shared methodology across all plugins
2. **Easier Maintenance** - Centralized best practices
3. **Better Testing** - TDD methodology prevents regressions
4. **User Confidence** - Evidence-based operations build trust

## Migration Guide

### For Plugin Developers
1. Identify where your plugin implements common patterns (brainstorming, debugging, verification)
2. Add superpowers integration sections to your skill/command documentation
3. Include superpowers calls in your workflows where appropriate
4. Test integrations to verify they enhance rather than complicate workflows

### For Users
1. No changes required - integrations are automatic
2. You may see more methodical approaches to problem-solving
3. Reviews will include evidence-based findings
4. Debugging will follow systematic investigation patterns

## Future Roadmap

### Planned Enhancements
1. **Dispatching Parallel Agents** - Coordinate multiple agents for complex tasks
2. **Using Git Worktrees** - Isolated workspace management for all plugins
3. **Defense in Depth** - Multi-layer validation across security-sensitive operations
4. **Skill Discovery** - Centralized management of skill dependencies

### Community Contributions
Contributions welcome for:
- Additional integration patterns
- New workflow orchestrations
- Cross-plugin synergies
- Documentation improvements

## Conclusion

Superpowers skills integrate with night-market plugins to add quality gates and consistent methodology. The focus on evidence over assumptions improves reliability across the plugin system.

The phased approach delivers immediate value while building toward deeper integration.
