---
title: Franklin Protocol - Learning Algorithms
source: https://spf13.com/p/how-benjamin-franklin-invented-machine-learning-in-1720/
author: spf13
date_captured: 2025-12-04
palace: Learning Techniques
district: Historical Methods
maturity: evergreen
tags: [learning, machine-learning, deliberate-practice, feedback-loops, skill-acquisition]
---

# Franklin Protocol: The Original Learning Algorithm

## Core Thesis

Benjamin Franklin reverse-engineered the principles of machine learning 250 years before we had the mathematics to describe it. His writing improvement method embodies gradient descent: compare output to exemplar, calculate error, adjust parameters, iterate.

## The Learning Algorithm (Memory Palace Layout)

```
Franklin's Workshop (Palace)
├── Data Collection Room (The Spectator)
│   └── Curated high-quality training data
├── Compression Chamber (Feature Extraction)
│   └── "Short hints of the sentiment in each sentence"
├── Reconstruction Forge (Forward Pass)
│   └── Generate from compressed understanding after deliberate delay
├── Comparison Hall (Loss Function)
│   └── "Discovered some of my faults" - side-by-side review
└── Update Anvil (Parameter Adjustment)
    └── Lean into discrepancies, rewrite, internalize patterns
```

## Key Concepts

### 1. Feature Extraction
**Location**: Compression Chamber
**Sensory Encoding**: Tight, focused distillation - like squeezing essence from raw material
**Concept**: Convert exemplary works into compact notes, forcing yourself to distill structure, tone, and argument

### 2. Deliberate Delay (Regularization)
**Location**: Waiting Antechamber
**Sensory Encoding**: Cool, patient stillness before reconstruction
**Concept**: Built-in delay prevents overfitting by forcing generalization over memorization

### 3. Reconstruction from Memory
**Location**: Reconstruction Forge
**Sensory Encoding**: Heat of creative generation, building from hints
**Concept**: The forward pass - prediction generated from compressed representation

### 4. Error Calculation
**Location**: Comparison Hall
**Sensory Encoding**: Bright, clinical light revealing every discrepancy
**Concept**: Side-by-side comparison supplies loss signal for concrete gaps

### 5. Parameter Update
**Location**: Update Anvil
**Sensory Encoding**: Hammering, reshaping, refining
**Concept**: Lean into errors to update internal model for next iteration

## ML Training Loop Parallel

| Franklin's Method | Machine Learning Equivalent |
|-------------------|----------------------------|
| Select high-quality articles | Curated training dataset |
| Compress to "short hints" | Feature extraction / embedding |
| Reconstruct from memory | Forward pass / prediction |
| Compare to original | Loss function calculation |
| Correct faults meticulously | Backpropagation & gradient descent |

## Connections to Plugin Development

### skills-eval Parallel
The Franklin Protocol mirrors how skills-eval works:
- **Find exemplar** → Reference established skill patterns
- **Compare output** → Validate against quality metrics
- **Identify gaps** → Generate improvement suggestions
- **Iterate** → Apply corrections, re-evaluate

### modular-skills Application
The "short hints" compression technique aligns with progressive disclosure:
- Extract essential structure first (SKILL.md hub)
- Detailed workflows in modules (spokes)
- User reconstructs understanding from hints

### Deliberate Practice for Skill Authors
When writing skills:
1. **Find Your Spectator**: Study exemplary skills (modular-skills examples)
2. **Run the Loop**: Draft skill, compare to exemplar, note 3 differences
3. **Internalize Patterns**: Ask "What pattern did I miss?"

## Practical Application: The Franklin Challenge

```yaml
challenge:
  pick_micro_skill: "Choose one specific skill to improve"
  find_spectator: "Find one high-quality example done perfectly"
  run_one_loop:
    - "Spend 30 minutes replicating from memory"
    - "Compare to original"
    - "Record 3 precise differences"
  outcome: "Started practicing like Franklin, learning like a neural network"
```

## Cross-References

- **Internal Skills**:
  - `memory-palace-architect` - Uses similar structured decomposition
  - `digital-garden-cultivator` - Iterative improvement through tending
  - `skills-eval` (abstract plugin) - Comparison and improvement workflow

- **Related Concepts**:
  - Anders Ericsson's "Deliberate Practice" (Peak, 2016)
  - Gradient descent in neural networks
  - Regularization and overfitting prevention

## Meta-Insight

> "Mastery is not about memorization, but about building an internal generative model of a domain."

Franklin's greatest insight: expertise can be engineered systematically. This is "learning how to learn" - the ultimate meta-skill that applies equally to human learning and AI training.

## Source Attribution

- **Original Article**: [How Benjamin Franklin Invented Machine Learning in 1720](https://spf13.com/p/how-benjamin-franklin-invented-machine-learning-in-1720/) by spf13
- **Referenced Works**:
  - Benjamin Franklin, *The Autobiography of Benjamin Franklin* (1791)
  - Anders Ericsson, *Peak: Secrets from the New Science of Expertise* (2016)
