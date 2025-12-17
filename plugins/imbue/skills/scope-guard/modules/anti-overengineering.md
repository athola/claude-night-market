# Anti-Overengineering Rules

Patterns and rules to prevent overengineering during development.

## Core Rules

### 1. Questions Before Solutions

**Always ask clarifying questions BEFORE proposing solutions:**
- What problem are you solving?
- Where does the application run?
- Who reads the output?
- What's the current pain point?
- What's the stated requirement?

**Anti-pattern:** Offering 3-5 approaches before understanding the need.

### 2. No Abstraction Until Third Use Case

**Rule:** Do NOT create abstractions until you have at least 3 concrete use cases.

**Examples:**
- Two config formats? → Two simple functions
- Three config formats? → NOW consider abstraction
- "We might need..." → NOT a use case

**Explicitly refuse:**
- Base classes for 1-2 implementations
- Strategy patterns before third strategy
- Plugin systems for hypothetical future needs

### 3. Defer "Nice to Have" Features

**Rule:** Features without clear business value go to backlog.

**Test:** If you can't answer "Why now?", defer it.

**Common rationalizations to block:**
- "Users might want this"
- "We'll need this eventually"
- "It's a good practice"
- "Modern applications have this"

### 4. Stay Within Branch Budget

**Default budget: 3 major features per branch**

When at budget, adding new feature requires:
- Dropping an existing feature, OR
- Splitting to new branch, OR
- Explicit override with documented justification

**Budget Check Template:**
```
Branch: [branch-name]
Budget: 3 features

Current allocation:
1. [Primary feature]
2. [Secondary feature]
3. [OPEN SLOT or Third feature]

Proposed: [New feature]
Decision: [Fits/Requires split/Requires drop]
```

## Anti-Rationalization Checklist

**If you find yourself thinking:**

| Thought | Reality Check |
|---------|---------------|
| "This is a small addition" | Did you score it? Small additions compound. |
| "We'll need this eventually" | Score Time Criticality honestly. "Eventually" = 1. |
| "It's already half done" | Sunk cost fallacy. Re-score from current state. |
| "Users might want this" | "Might" = Business Value of 1-2 max. |
| "This is the right way to do it" | Is it the simplest way that works? |
| "It's just refactoring" | Refactoring still has Complexity cost. Score it. |

## Red Flags

**Red flags that indicate overengineering:**
- Enjoying the solution more than solving the problem
- Adding "flexibility" for unspecified future needs
- Creating abstractions before the third use case
- Discussing patterns before discussing requirements
- Branch metrics climbing without proportional value delivery

## "While We're Here" Pattern

**Anti-pattern:** Scope expansion because you're "already working in this area"

**Examples to block:**
- "While we're here, let's also refactor..."
- "For consistency, we should update..."
- "Since we're touching this file, we could..."

**Response:** Evaluate the additional work with Worthiness formula. If < 1.0, defer to backlog.
