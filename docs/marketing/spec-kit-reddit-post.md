# How you can write specifications that prevent 80% of implementation rework

Resource

If you have ever implemented a feature only to realize during code review that you misunderstood the requirements, you know the pain. Two weeks of work. A PR with 500 lines changed. The reviewer asks "Did you consider X?" and "What happens when Y?" and "This does not match the original request."

You thought you understood. You read the requirements. You discussed it in the meeting. You nodded at all the right places. But when you started coding, assumptions crept in. Edge cases emerged. The requirements that seemed clear turned out to have interpretations you did not anticipate.

So you rewrite. You add the missing feature. You handle the edge case. You refactor to match the actual requirements. Another week passes. Another round of reviews. More feedback.

The cost is not just the rework. It is the motivation. You were excited about this feature. Now it is a chore you just want to finish. The team is frustrated because the deadline slips. The stakeholders are annoyed because the timeline keeps extending.

The problem is not that you are a bad developer. The problem is that natural language is ambiguous. Requirements stated clearly in conversation turn into contradictions when you try to implement them. Assumptions that everyone agrees with in the meeting turn out to be assumptions only you made.

spec-kit changes that math completely.

spec-kit is a specification-driven development workflow. You describe a feature in natural language. It clarifies the requirements with targeted questions. It generates a testable specification. It breaks the work into tasks with dependencies. It produces an implementation plan. Only then does it start coding.

The difference from jumping straight to implementation is clarity. Before you write a single line of code, you have a specification that defines what success looks like. You have acceptance criteria that are unambiguous. You have identified edge cases and decided how to handle them. You have agreement from stakeholders that this specification captures their intent.

How you can use it in 10 minutes.

Claude Night Market has a workflow called spec-kit. You invoke `/speckit-specify`, describe the feature in natural language, and it guides you through a clarification process. It asks about edge cases. It probes ambiguities. It extracts acceptance criteria. It produces a markdown specification that anyone can review.

I used it last week to implement a multi-step approval workflow. I described the feature in one paragraph: "Users need approval from their manager before publishing content, and managers need approval from finance if the content exceeds budget."

spec-kit asked questions I had not considered. What happens if the manager is on vacation? Can approvals be delegated? What if the budget changes between approval and publication? Is there a rejection workflow? What happens to the content if approval is rejected?

Ten minutes of clarification and we had a specification that covered every edge case. The implementation took two days and passed review on the first attempt because the requirements were unambiguous and the edge cases were already handled.

The specification became a living document. When questions came up during implementation, we checked the spec. If the spec did not cover it, we updated the spec first, then implemented. No oral tradition. No assumptions. No "I thought we agreed to X."

And the workflow continues. After the specification, `/speckit-plan` generates an implementation plan. `/speckit-tasks` breaks the plan into dependency-ordered tasks. `/speckit-implement` executes the tasks with TDD. `/speckit-checklist` generates a quality checklist. The entire process is progressive, with each step building on the previous one.

Tips if you want to try spec-kit

A few things I learned using spec-kit for feature development:

Embrace the clarification. The questions feel tedious at first. You want to get to coding. But those five minutes of clarification save two weeks of rework. Every question represents an edge case you would have missed or an ambiguity you would have interpreted wrong.

Make the specification visible. The spec is a markdown file. Put it in the repo. Link it from the issue. Reference it in the PR description. When the QA team tests the feature, they should use the spec as the source of truth for what "done" looks like.

Update the spec when reality changes. Requirements evolve. That is fine. Update the specification first, then update the implementation. The spec should always match reality. If they diverge, you have a problem.

Use the checklist. The workflow generates a quality checklist based on your specification. Run it before you submit the PR. It catches missing requirements, incomplete features, and edge cases you forgot to implement.

Start small. You do not need to use the full workflow for every change. For a one-line fix, skip the specification. For a feature that affects multiple files and has unclear requirements, run the full workflow. The tool is smart about scope—use it accordingly.

If you use Claude Code, try spec-kit. Think of a feature you are about to implement. Instead of diving straight into the code, run `/speckit-specify`. Answer the questions. Produce a specification. Then implement. See how much smoother the process is when you know exactly what you are building before you start building it.

Claude Night Market is free and open source: github.com/athola/claude-night-market

Stop implementing features based on assumptions. Write specifications first. Clarify the ambiguities. Prevent the rework.
