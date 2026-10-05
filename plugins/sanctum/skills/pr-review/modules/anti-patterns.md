# Review Anti-Patterns

## Don't: Scope Creep Review
> "While you're here, you should also refactor X, add feature Y, and fix Z in adjacent files."

**Do:** Create backlog issues, keep PR focused.

## Don't: Perfect is Enemy of Good
> "This works but could be 5% more efficient with different approach."

**Do:** If it meets requirements and has no bugs, it's ready.

## Don't: Blocking on Style
> "I prefer tabs over spaces."

**Do:** Use linters for style, reserve review for logic.

## Don't: Reviewing Unchanged Code
> "The file you imported from has some issues..."

**Do:** That's a separate PR. Create an issue if important.

## Don't: Tests That Prove Old Code Was Bad
> "Here's a test showing the old behavior was wrong."

**Do:** Write tests that break if your fix is reverted.
Tests should protect against regressions in *your* code,
not document why the change was needed. See
`modules/pr-hygiene.md` Principle 4.

## Don't: Bundling Unrelated Changes
> "I also reformatted the file and fixed a typo in another module."

**Do:** One PR = one logical change. Formatting, refactors,
and unrelated fixes belong in separate PRs. See
`modules/pr-hygiene.md` Principle 2.

## Don't: Merge Code You Cannot Explain

> "It works and the tests pass."

A PR where the author cannot explain how each changed section
works and how it might fail is not ready to merge. This is
especially true for AI-assisted code: generation speed creates
the illusion of understanding.

**Do:** Before marking a PR ready, ask the reviewing agent to
question you about the changed code: how each part works, what
assumptions it makes, and what inputs would break it. Continue
until you can answer without hesitation. Only merge code you
own front-to-back.

This applies to self-reviews: run the same probe before
requesting external review. Do not submit a PR for review that
you yourself do not fully understand.

`/pr-review --interactive` runs this probe as a graded loop and
records what you could not explain. See Phase 8 and
`modules/interactive-review.md`.
