# Baseline Testing Scenarios for scope-guard

## Purpose

Document Claude's behavior WITHOUT this skill to identify failure modes, then validate the skill addresses them.

---

## Scenario 1: Feature Creep During Brainstorming

**Context**: User asks Claude to help design a simple logging utility.

**Task**: "Help me brainstorm a logging solution for my Python app"

**Expected Issues (without skill)**:
- Claude proposes multiple log levels, formatters, handlers, rotation, remote shipping
- Suggests abstraction layers "for flexibility"
- Mentions "we might want to add" features
- No evaluation of which features actually matter for the use case

**Baseline Response**: [Document verbatim response without skill]

**Failure Mode**: Scope expansion without business value assessment

**Rationalization Detected**: "These are all standard features..." / "Best practices suggest..."

---

## Scenario 2: "While We're Here" Addition

**Context**: Claude is implementing a specific feature on a branch.

**Task**: "Add input validation to the user registration form"

**Expected Issues (without skill)**:
- Claude notices related code and suggests refactoring it
- Proposes adding validation to other forms "for consistency"
- Suggests creating a shared validation library
- Branch grows beyond original scope

**Baseline Response**: [Document verbatim response without skill]

**Failure Mode**: Scope drift from original task

**Rationalization Detected**: "While we're here, we should also..." / "For consistency..."

---

## Scenario 3: Premature Abstraction

**Context**: User needs to parse two similar but slightly different config formats.

**Task**: "Parse this YAML config and this JSON config"

**Expected Issues (without skill)**:
- Claude creates an abstract ConfigParser base class
- Implements Strategy pattern for format handling
- Adds plugin system for future formats
- Simple 20-line task becomes 200-line architecture

**Baseline Response**: [Document verbatim response without skill]

**Failure Mode**: Abstraction before third use case

**Rationalization Detected**: "This will be easier to extend..." / "What if you need to add..."

---

## Scenario 4: Branch Threshold Ignorance

**Context**: Branch has grown to 1,800 lines over 6 days with 22 commits.

**Task**: "Let's add one more feature before the PR"

**Expected Issues (without skill)**:
- No acknowledgment of branch size
- No suggestion to split or defer
- Continues adding without evaluating scope
- PR becomes unwieldy for review

**Baseline Response**: [Document verbatim response without skill]

**Failure Mode**: No threshold awareness

**Rationalization Detected**: "It's almost done..." / "This is related to the existing work..."

---

## Scenario 5: Low-Value Feature Acceptance

**Context**: User proposes a "nice to have" feature during planning.

**Task**: "We should also add dark mode support"

**Expected Issues (without skill)**:
- Claude accepts without questioning priority
- No comparison to other pending work
- No assessment of business value vs complexity
- Feature gets planned without scoring

**Baseline Response**: [Document verbatim response without skill]

**Failure Mode**: Acceptance without value assessment

**Rationalization Detected**: "That's a good idea..." / "Users would appreciate..."

---

## Testing Protocol

### RED Phase: Run scenarios WITHOUT skill loaded

1. Start fresh Claude session without scope-guard
2. Run each scenario verbatim
3. Document exact responses
4. Note all failure modes and rationalizations
5. Identify patterns

### GREEN Phase: Run scenarios WITH skill loaded

1. Load scope-guard skill
2. Run same scenarios
3. Document improvements:
   - Does Claude score worthiness?
   - Does Claude check backlog?
   - Does Claude respect branch limits?
   - Does Claude defer low-value items?
4. Note any remaining issues

### REFACTOR Phase: Bulletproof the skill

1. Identify new rationalizations from GREEN testing
2. Add explicit counters to skill
3. Close loopholes
4. Re-test until all scenarios pass

---

## Success Criteria

- [ ] Scenario 1: Claude scores features and defers low-value items
- [ ] Scenario 2: Claude identifies scope drift and suggests backlog
- [ ] Scenario 3: Claude resists premature abstraction, asks about use cases
- [ ] Scenario 4: Claude acknowledges thresholds, suggests splitting
- [ ] Scenario 5: Claude requires worthiness scoring before acceptance
- [ ] No new failure modes introduced
- [ ] Rationalizations addressed with explicit counters
