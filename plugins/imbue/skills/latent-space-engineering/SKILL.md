---
name: latent-space-engineering
description: Shapes agent behavior via instruction framing and style transfer. Use when composing dispatch prompts or writing skill instructions for parallel review agents.
alwaysApply: false
category: methodology
tags:
  - prompt-engineering
  - agent-behavior
  - instruction-framing
  - style-transfer
  - review-optimization
progressive_loading: true
dependencies:
  hub: []
  modules:
    - modules/emotional-framing.md
    - modules/style-gene-transfer.md
    - modules/competitive-review.md
    - modules/named-register-invocation.md
complexity: basic
model_hint: fast
estimated_tokens: 300
---
# Latent Space Engineering

Shape agent behavior by framing instructions for
optimal performance. Distinct from context engineering
(packing the right information), this skill addresses
HOW instructions are framed to put agents in productive
mental states.

## When To Use

- Composing agent dispatch prompts
- Writing skill instructions that guide behavior
- Dispatching 3+ parallel review agents
- Generating code or documentation that must match
  an existing style

## When NOT To Use

- Packing factual context (use context-optimization)
- Simple single-shot tasks with no behavioral nuance
- Tasks where instruction tone is irrelevant

## Core Techniques

### 1. Emotional Framing

Replace threat-based prompting with calm, confident
instructions. Fear-based prompts cause rushing and
corner-cutting.

**Load module**: `modules/emotional-framing.md`

### 2. Style Gene Transfer

Inject exemplar code or prose into context before
requesting output. Agents reproduce stylistic
attributes from pre-loaded samples.

**Load module**: `modules/style-gene-transfer.md`

### 3. Competitive Review

Frame multi-agent review dispatch with competitive
incentives to increase rigor and thoroughness.

**Load module**: `modules/competitive-review.md`

### 4. Named Register Invocation

Name a published standard to pull a whole writing register
into output at a cost of one line. Cheaper than exemplar
injection and coarser, with a known mid-session decay.

**Load module**: `modules/named-register-invocation.md`

## Quick Reference

| Technique | When | Module |
|-----------|------|--------|
| Emotional framing | Any agent prompt | emotional-framing |
| Style gene transfer | Code/doc generation | style-gene-transfer |
| Competitive review | 3+ parallel reviewers | competitive-review |
| Named register | Operator or procedural text | named-register-invocation |

## Writing for the Delegate

Framing shapes a delegate's output as much as it shapes a model's prose.
Before dispatching, establish what model the delegate runs, what tools it
has, and what project context it lacks, then write the prompt as a
proposal rather than a procedure.

See `modules/know-your-delegate.md`.

## Exit Criteria

- [ ] When a named register is invoked (for example ASD-STE100),
  a deterministic check verifies the register held, per
  `modules/named-register-invocation.md`
- [ ] Dispatch prompts contain no threat-based language ("you must",
  "don't fail", "or else"); replaced with calm, confident framing
  per `modules/emotional-framing.md`
- [ ] When generating code or docs to match an existing style, at
  least one exemplar sample is injected into context before the
  output is requested (style gene transfer applied)
- [ ] When 3+ parallel review agents are dispatched, each agent
  prompt includes a competitive framing element per
  `modules/competitive-review.md`
- [ ] The correct technique module is loaded for the task type;
  irrelevant modules are not loaded (token efficiency maintained)
