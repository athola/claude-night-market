# Tradeoff Acknowledgment: When Not to Apply These

The four principles bias toward caution. That bias
costs speed. For a substantial portion of coding work
the cost is worth paying. For a non-trivial minority,
the cost is wrong. This module names the boundary
honestly.

The upstream framing puts it as: "These guidelines
bias toward caution over speed. For trivial tasks,
use judgment." That sentence does the same work as
this module, just compressed.

## When the Principles Do Not Apply

### Trivial One-Line Fixes

Asking three clarifying questions before fixing a
typo in a comment is a parody of caution. For diffs
under five lines with obvious intent, ship and move
on. Principle 1 (Think Before Coding) is for
ambiguous requests, not unambiguous ones.

### Exploratory Spikes and Throwaway Scripts

A 50-line script that runs once, produces a CSV, and
gets deleted does not need the senior-engineer test.
It does not need TDD. It does not need careful
abstraction analysis. The artifact's lifetime caps
the time worth investing in its quality.

Test: if the script will run again next week, treat
it like real code. If you will throw it away in an
hour, do not over-invest.

### Documentation-Only Changes

Style drift in docs is often the point. Rewriting a
paragraph for clarity touches every line by design.
Principle 3 (Surgical Changes) was written for code
diffs, where adjacent edits hide intent. Prose is
different.

### Time-Boxed Prototypes

A "by Friday or we move on" prototype is a different
artifact from a feature. Verifiable success criteria
for a prototype look like "the demo runs end to
end," not "the test suite is green." Calibrate
ambition to the deadline.

### Production Fires

When the database is on fire, "let's write a failing
test first" is the wrong move. Stop the fire, then
write the test that prevents the next fire. The Iron
Law assumes a normal-operations context.

## Contrarian Voices Worth Engaging

Three voices push back on rigorous-by-default LLM
coding rules. Their critiques sharpen the boundary.

**Simon Willison** ("Not all AI-assisted programming
is vibe coding," March 2025) defends throwaway
prototyping as legitimate. His golden rule: do not
commit code you cannot explain. That rule is
compatible with everything in this skill, but it
makes the throwaway-prototype boundary explicit.

**Mastering Product HQ** ("What Karpathy's CLAUDE.md
misses") argues code simplicity does not equal scope
simplicity. A 50-line solution to the wrong problem
is still waste. The principles help with how to
build; they do not help with what to build. For
"what," see `Skill(imbue:scope-guard)` and
`Skill(imbue:feature-review)`.

**NMN.gl** ("Vibe Coding Considered Harmful," March
2025) warns that vibed black boxes compound. This is
adjacent support for the principles, not pushback,
but it names the real cost of skipping them at scale:
each black box you accept becomes a future debugging
expense.

## The Honest Bottom Line

These principles solve a specific class of problem:
LLM agents shipping wrong-shape code on tasks they
could have shipped right with five minutes of
upfront thought. That class is large. It is not
universal.

If you find yourself about to invoke these
principles on a task that fits in a sticky note,
stop. The principles are the heavier path. Use the
heavier path when the cost of getting it wrong is
larger than the cost of slowing down. Otherwise, ship
and move on.

## Cross-References

- `Skill(imbue:scope-guard)` for "should we build
  this at all" (the scope question this module
  punts on).
- `Skill(imbue:feature-review)` for prioritization
  using RICE / WSJF / Kano scoring.
- `Skill(conserve:decisive-action)` for guidance on
  when to skip clarification and proceed.
