---
module: research-flow
category: data-gathering
dependencies: []
estimated_tokens: 600
---

# Architecture Research Flow

Steps 1-2 of the architecture-aware-init workflow: gather project
context, then research current best practices online.

## Step 1: Gather Project Context

Ask the user for the following information before any research:

**Project Type**

- Web API, CLI tool, data pipeline, desktop app, library, mobile,
  embedded, etc.

**Domain Complexity**

- Simple (CRUD only)
- Moderate (some business logic)
- Complex (many rules, workflows)
- Highly Complex (domain-specific language needed)

**Team Context**

- Team size: < 5 | 5-15 | 15-50 | 50+
- Experience: Junior | Mixed | Senior | Expert
- Distribution: Co-located | Remote | Distributed

**Non-Functional Requirements**

- Scalability needs (users, requests/sec, data volume)
- Performance requirements
- Security and compliance needs
- Integration points (external systems, databases, APIs)

**Timeline and Constraints**

- Time to market: Rapid | Normal | Not urgent
- Budget constraints
- Technology constraints (must-use or must-avoid)

Mark `arch-init:research-completed` only after the answers are
captured. Skipping context-gathering is the most common cause of a
mismatched paradigm choice in Step 3.

## Step 2: Research Best Practices

Run three search tiers using `WebSearch`:

```bash
# Tier 1: project-type level
WebSearch("[project type] architecture best practices 2026")

# Tier 2: language-specific
WebSearch("[language] [project type] architecture patterns 2026")

# Tier 3: framework-specific
WebSearch("[framework] architecture patterns [project type]")
```

Focus the synthesis on five questions:

1. What are practitioners actually recommending right now?
2. Are any new patterns gaining traction in this space?
3. Which practices are being actively discouraged (anti-patterns)?
4. Which patterns work best with the chosen stack?
5. Are there real-world case studies of similar projects?

## Synthesis Output

Produce a short brief with:

- Recommended architecture(s) for this project type
- Key trade-offs to consider
- Red flags or anti-patterns to avoid
- Technology-specific considerations

Hand the brief into Step 3 (paradigm selection). The decision
matrix in `modules/paradigm-selection.md` consumes this brief
directly.
