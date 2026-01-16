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

## Cargo Cult Overengineering

**Additional red flags from cargo cult programming:**

| Pattern | Symptom | Reality Check |
|---------|---------|---------------|
| **Enterprise Cosplay** | Microservices for a CRUD app | "Does my scale require this?" |
| **Technology Tourism** | Using Kubernetes "like Netflix" | "Do I have Netflix's problems?" |
| **Resume-Driven Development** | Adding tech to look impressive | "Does this solve user problems?" |
| **Complexity Signaling** | "Production-ready" without defining it | "What specific requirements?" |
| **Pattern Worship** | Using patterns because they exist | "What problem does this solve?" |

### The AI Amplification Problem

AI makes cargo cult overengineering worse because:

1. **Confident Explanations** - AI sounds authoritative even when wrong
2. **Complete Solutions** - AI provides full implementations for vague requirements
3. **Enterprise Defaults** - AI often suggests "scalable" solutions for simple problems
4. **No Pushback** - AI won't ask "Do you really need this?"

**Mitigation:** When AI suggests an approach, ask:
- "What simpler alternatives exist?"
- "What are the trade-offs?"
- "What's the minimum version that works?"

### Cargo Cult YAGNI

**YAGNI (You Aren't Gonna Need It)** applies especially to:

| "We might need..." | Reality |
|-------------------|---------|
| "...a plugin system" | Build it when you have 3 plugins |
| "...to scale globally" | Build for current users first |
| "...flexibility here" | Flexibility you don't use is debt |
| "...this configuration option" | Default is right 90% of time |
| "...enterprise features" | Define enterprise requirements first |

**Rule:** If justification uses "might", "could", or "eventually" - defer to backlog.

See [../../shared/modules/anti-cargo-cult.md](../../shared/modules/anti-cargo-cult.md) for understanding verification protocols.

## "While We're Here" Pattern

**Anti-pattern:** Scope expansion because you're "already working in this area"

**Examples to block:**
- "While we're here, let's also refactor..."
- "For consistency, we should update..."
- "Since we're touching this file, we could..."

**Response:** Evaluate the additional work with Worthiness formula. If < 1.0, defer to backlog.
