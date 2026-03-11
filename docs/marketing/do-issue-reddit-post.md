# How you can implement GitHub issues in one command instead of two hours of context switching

Resource

If you have ever implemented GitHub issues, you know the ritual. Open the issue. Read the description. Open the linked PRs. Check the related issues. Search the codebase for relevant files. Try to remember the project conventions. Write some code. Realize you missed a dependency. Rewrite. Run tests. Fix failures. Update the issue. Draft a PR.

Two hours later, you have changed 50 lines of code.

The cost is not the coding. The cost is the context. Every issue requires you to rebuild mental models of the codebase, the conventions, the testing setup, the deployment process. You switch from "writing code" to "archaeology" to "detective work" to "diplomat" (resolving merge conflicts) and back.

So most developers develop habits. They skim issues. They skip the analysis. They dive into coding before they understand the problem. They miss edge cases. They create PRs that get rejected for missing requirements. The cycle repeats.

The problem is not that you are a bad developer. The problem is that the workflow is broken. Humans are not good at maintaining consistent process across dozens of steps, especially when those steps span different tools, different contexts, different mental models.

do-issue changes that math completely.

do-issue is a progressive workflow that implements GitHub issues automatically. It reads the issue. It analyzes the codebase. It clarifies acceptance criteria. It breaks the work into tasks. It implements the changes with TDD. It validates the results. It creates a PR with a proper description.

The difference from doing it manually is consistency. You do not skip the analysis because you are in a hurry. You do not forget to run tests because you are excited about the solution. You do not write a vague PR description because you are tired of the whole process. The workflow runs the same way every time.

How you can use it in 5 minutes.

Claude Night Market has a command called do-issue. You point it at an issue, and it runs the full progressive workflow: analyze, specify, plan, implement, validate, complete.

I used it yesterday to implement a feature request for our API. The issue had a vague description and no acceptance criteria. I ran `/do-issue 142`. It fetched the issue, analyzed the related code, asked clarifying questions about edge cases, generated a specification, broke it into 7 tasks with dependencies, implemented each task with tests first, validated everything worked, and created a PR with a detailed description referencing the original issue.

What used to take me 2 hours of context switching and backtracking took 15 minutes of actual work. The PR was approved on the first pass because all the requirements were addressed, the tests were thorough, and the description made it clear what changed and why.

The workflow is smart about scope. For a typo fix, it skips straight to implementation. For a complex feature with multiple files and unclear requirements, it runs the full analysis and specification phase. It detects the scope automatically, but you can override it.

And the quality is higher. Every implementation follows TDD—tests are written before the code. Every PR includes quality gates—linting, type checking, test coverage. Every step produces artifacts that become part of the project documentation. Specifications, task breakdowns, implementation plans—all stored, all searchable, all reusable.

Tips if you want to try do-issue

A few things I learned using do-issue for issue implementation:

Let it ask questions. The specification phase is where the workflow clarifies ambiguity. Do not skip it. The questions it asks about edge cases and acceptance criteria are exactly the questions you should be asking but probably forget when you dive straight into coding.

Trust the scope detection. The workflow is designed to skip unnecessary steps. A minor fix does not need a full specification. Let the workflow decide. You can always override with `--scope minor` if you know better, but most of the time auto-detection gets it right.

Review the artifacts. The workflow produces a specification, a task breakdown, and an implementation plan. Read them. They become part of your project documentation. Six months from now, when someone asks why this feature was implemented this way, you have the answer.

Use it for batches. You can pass multiple issues at once: `/do-issue 142 143 144`. The workflow analyzes dependencies and suggests an optimal execution order. What used to be three separate context switches becomes one coordinated effort.

Run quality gates. The validate step runs linting, type checking, and tests. Do not skip it. The gates catch issues before you create the PR, which means fewer review cycles and faster merges.

If you use Claude Code, try do-issue. Pick a GitHub issue that you have been putting off. Run the command. Let the workflow handle the archaeology, the analysis, the process. You focus on the parts that require your judgment—the decisions, the trade-offs, the creative work.

Claude Night Market is free and open source: github.com/athola/claude-night-market

Stop wasting time on issue implementation rituals. Automate the workflow. Focus on the code that matters.
