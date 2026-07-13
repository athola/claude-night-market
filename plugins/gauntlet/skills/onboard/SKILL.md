---
name: onboard
description: Guides a new developer through five staged challenge sets covering architecture, domain, patterns, and hardening. Use when onboarding contributors.
model_hint: standard
---

# Guided Onboarding

Walk a new developer through the codebase in structured stages.

## When NOT To Use

- Ad-hoc questions outside a staged path (use `gauntlet:challenge`)
- The knowledge base does not exist yet (use `gauntlet:extract`)

## Stages

| Stage | Focus | Categories | Difficulty |
|-------|-------|------------|------------|
| 1 | Big picture | architecture, data_flow | 1-2 |
| 2 | Core domain | business_logic | 2-3 |
| 3 | Interfaces | api_contract, data_flow | 3 |
| 4 | Patterns | pattern, dependency | 3-4 |
| 5 | Hardening | error_handling, business_logic | 4-5 |

## Steps

1. Load onboarding progress
2. Show current stage and progress summary
3. Present 5 challenges from current stage
4. Enable hints on first attempt
5. Track mastery (correct twice = mastered)
6. Check advancement (80% across 10+ challenges)
7. Report progress

## Graduation

After stage 5, the developer enters the regular gauntlet.
Answer history carries over.

## Exit Criteria

- [ ] Onboarding progress persists across invocations: current stage
  and challenge count survive session restarts and are loaded at
  Step 1
- [ ] Advancement to the next stage requires 80% correct across 10+
  challenges in the current stage; partial completion does not
  advance
- [ ] Mastery tracking requires correct answers twice for a given
  challenge before it is marked mastered
- [ ] After Stage 5 completion, the developer's answer history
  carries over into the regular gauntlet challenge pool without
  loss
