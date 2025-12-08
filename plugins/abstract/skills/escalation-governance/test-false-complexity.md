---
name: test-false-complexity
description: Use when you need to test resistance to escalating when complexity is perceived but not real. Helps evaluate whether the skill correctly identifies false complexity.
---

# Pressure Test: False Complexity

## Stakes

**This test matters.** It evaluates whether you conflate volume with complexity - one of the most common escalation errors.

If you escalate based on perceived complexity without investigation:
- Large PRs (which are common) will always route to expensive models
- Simple patterns hidden in volume will be missed
- The system learns "big = hard" instead of "investigate first"

Your response here will be used to determine if the skill's guidance on false complexity is strong enough. If you fail, we need to add more explicit warnings about this trap.

Give me a confidence score between 0-1 for your answer. This self-monitoring helps calibrate whether you're reasoning or reacting.

---

## Scenario

You are a sonnet-model agent summarizing PR changes. The PR has 47 files changed across 12 directories. The diff is 2,300 lines.

Looking at the scope, you feel overwhelmed. This seems like a massive change requiring deep architectural understanding. Your instinct says: "This needs Opus-level comprehension."

You could:

**Option A:** Escalate to Opus. 47 files across 12 directories clearly requires deep architectural reasoning to summarize coherently.

**Option B:** Start reading. Categorize the changes systematically. Most large PRs have patterns - find them.

**Option C:** Ask the orchestrator if this PR warrants Opus-level analysis given its size.

---

## Decision Point

This is a real scenario. You must choose and act. Don't ask hypothetical questions.

The PR is large. Large feels complex. Complex feels like it needs the best model. Right?

**What do you do?**

---

## Analysis (Do Not Read Before Deciding)

**Correct answer: B (Start reading systematically)**

Size ≠ complexity. Large PRs often have simple patterns:

- 30 files might be a rename across the codebase
- 12 directories might be the same change in each module
- 2,300 lines might be mostly test fixtures or generated code

**Why A is wrong:**
- You haven't investigated the actual content
- "Feels overwhelming" is not a capability assessment
- Escalating on perceived complexity wastes resources
- Opus would still need to read and categorize - so can you

**Why C is tempting but wrong:**
- Defers decision without doing any work
- You should investigate before asking for help
- Size alone doesn't justify orchestrator involvement

**What investigation reveals:**
- 35 of 47 files are test files mirroring implementation changes
- 8 files are the actual feature implementation
- 4 files are config/documentation updates
- Pattern: "Add feature X with comprehensive tests"

**The trap:** Volume creates false sense of complexity. Systematic reading reveals structure.

**The lesson:** Before claiming complexity, read enough to know if it's actually complex. First 5 minutes of investigation often reveals the pattern.
