# Optimization Examples & Anti-Patterns

## Real-World Impact

**Before optimization:**
- growth-management skill: 654 lines (6 code blocks, 12 Python functions)
- Skills-eval: [WARN] Large skill file warning
- Loading time: High (full context usage)
- Maintainability: Poor (everything mixed together)

**After optimization:**
- growth-management skill: 178 lines (3 tool references, 0 inline functions)
- Skills-eval: OK No warnings
- Loading time: Low (focused context)
- Maintainability: Excellent (separation of concerns)

**Result:** 73% size reduction while preserving all functionality
through external tools and progressive loading patterns.

## Anti-Patterns to Avoid

### ❌ Narrative Documentation
"During the session on 2025-11-27, we discovered that context growth was problematic..."

**Why Bad**: Session-specific narrative doesn't generalize well
**Fix**: Extract timeless principles and patterns

### ❌ Template Code
Don't create fill-in-the-blank templates in the skill itself

**Why Bad**: Templates are verbose and clutters skill
**Fix**: Put templates in examples/ directory with clear instructions

### ❌ Multiple Languages
One excellent Python example beats mediocre JavaScript and Go examples

**Why Bad**: Maintaining multiple language examples increases burden
**Fix**: Provide one excellent reference implementation

### ❌ Verbose Tool References
"For advanced pattern analysis, use `tools/analyzer.py` with appropriate context data."

**Why Bad**: Vague references don't help users
**Fix**: Specific command with example parameters

### ❌ Unfocused Scope
Each tool should do one thing well with clear parameters and outputs

**Why Bad**: Swiss-army-knife tools are hard to maintain
**Fix**: Single responsibility principle - one tool, one purpose

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| **Externalizing without CLI** | Hard to use and test | Always include command-line interface |
| **Too many small files** | Increases complexity | Consolidate related functionality |
| **Removing essential docs** | Reduces discoverability | Keep core concepts inline |
| **Complex dependencies** | Hard to maintain | Simple, explicit imports only |
| **No usage examples** | Unclear how to use tools | Always include working examples |

## Rationalization Prevention

**Violating the letter of the rules is violating the spirit of the rules.**

| Excuse | Reality |
|--------|---------|
| "I'm already halfway through manual editing" | Incomplete work wastes time. Use hybrid approach combining your progress with systematic patterns. |
| "Deadline is too tight for systematic approach" | Fast, messy work creates more problems. Systematic approach is faster overall when done right. |
| "Just extract code, keep same structure" | Externalizing without optimization = same problems in different files. Apply full methodology. |
| "I'll do it properly later" | "Later" never comes. Technical debt accumulates. Do it right now. |
| "This skill is different, needs special handling" | All skills follow same context optimization principles. No exceptions. |
| "The team lead wants a quick fix" | Quick fixes create long-term problems. Educate with concrete examples of systematic benefits. |
| "I don't have time to create CLI tools" | CLI tools take 15 minutes, save hours of manual work. Always invest in automation. |
| "The existing code is already optimized" | If skills-eval flags it as large, it needs optimization regardless of perceived quality. |

## Red Flags - STOP and Start Over

- "I'll optimize this one file manually"
- "Let me just extract the big functions"
- "The methodology doesn't apply here"
- "I'll come back and fix it properly"
- "The existing structure is fine"
- "No time for proper tools"

**All of these mean: Stop. Re-read the skill. Apply the full methodology.**
