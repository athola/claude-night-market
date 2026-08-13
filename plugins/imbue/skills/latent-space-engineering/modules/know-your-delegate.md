---
name: know-your-delegate
description: Write delegation prompts for the delegate that will run them.
  Establish model, tools, and missing context first, then frame the prompt
  as a proposal rather than a procedure.
parent_skill: imbue:latent-space-engineering
category: methodology
estimated_tokens: 550
---

# Know Your Delegate

A delegation prompt is written for a specific reader. Writing it without
knowing which reader wastes the prompt.

## The Failure

The same prompt lands two ways depending on who runs it. Spelling out a
step-by-step procedure for a frontier model burns prompt space on
process that model would have handled better on its own, and it caps the
result at whatever approach the author imagined. Handing a loose goal to
a small model produces unreliable output, because the judgment the goal
assumes is not there.

Both failures look identical from the outside: a disappointing result
that reads like the delegate ignored the prompt.

## Four Questions Before Writing

1. **What model is running?** A frontier model infers and adapts. A
   smaller one needs explicit structure, format specifications, and
   verification steps.
2. **What tools does it have?** Filesystem access, code execution, web
   search, the ability to spawn its own subagents, the ability to
   delete. Write for the tools the delegate has, not the tools the
   author has.
3. **What can it do that the author cannot?** Delegates often run
   scripts, process files at scale, or work in parallel. A good prompt
   uses that rather than dictating a serial procedure around it.
4. **What context is it missing?** The delegate usually has no project
   history, conventions, or strategic background. Supply the context it
   lacks rather than a procedure to follow.

## Prompts Are Proposals

Write for understanding, not for **compliance**. A capable delegate
given a well-contextualized prompt will often find a better approach
than the one the author had in mind, and a prompt written as a rigid
instruction sequence forecloses that.

Treat delegation prompts as **proposals**: state the goal, the
constraints, and the shape of a good result. Leave the method open
unless the method is itself the requirement.

## Have the Delegate Review the Prompt Before Running It

For anything non-trivial, hand the delegate the prompt and ask for
feedback first, **before running** the task.

The author has project context and strategic intent. The delegate has
operational knowledge the author lacks: its own tool behavior, edge
cases in the actual file state, better batching or parallelism, and the
ability to spot assumptions that do not hold. Neither writes the best
prompt alone.

This is the step most often skipped and the one that most reliably
changes the outcome, because a prompt written from the outside almost
always encodes at least one assumption about the environment that is
wrong.

## What Stays and What Goes

The delegate reads, processes, sorts, audits, and documents. The caller
judges, connects, and integrates.

Delegate work that is bounded, detail-intensive at scale, and
describable without full project context. Keep work that needs
strategic judgment, voice calibration, or decisions not yet made.

## Scope the Access

Give the delegate the access the task needs and no more. Broader access
invites drift outside the task boundary, and the cost of that shows up
as changes nobody asked for rather than as an error.
