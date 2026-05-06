# Creating a New Shared Pattern

How to extract a reusable pattern from a recurring need, decide
whether the abstraction earns its keep, and add it to this skill
without breaking existing callers.

## Extraction Methodology

Wait for the third occurrence before extracting. The first time
you write a chunk of code, you do not know what is essential vs
incidental. The second time, you guess. The third time, you have
enough variation across callers to see the true shape.

### Three-Strike Rule

| Occurrence | Action |
|------------|--------|
| First | Inline. Note the code in your head. |
| Second | Inline. Add a comment: "duplicate of X". |
| Third | Extract into a shared pattern module. |

Do not skip ahead. Premature extraction freezes the wrong
abstraction and forces later callers to fight the shape.

### Extraction Steps

1. List the 3+ call sites side by side.
2. Identify the parts that are identical across all sites.
3. Identify the parts that vary; these become parameters.
4. Identify the parts that are accidentally similar; leave those
   inline.
5. Write the extracted function with the smallest signature that
   covers all current callers.
6. Replace each call site with a call to the new function.
7. Run each caller's test suite.

## When to Abstract

Extract a shared pattern when all of these hold:

- Three or more skills do the same thing
- The thing has a name you can defend in one sentence
- The contract (inputs, outputs, errors) is stable enough that
  callers will not need it to change every release
- The cost of the extra import is less than the cost of keeping
  copies in sync

Look at `validation-patterns.md` for an example: every skill that
parses frontmatter needs `validate_required_fields()`. The shape
is small (a dict and a list of keys), the output is a list of
missing keys, and the contract has not changed.

## When to Inline

Keep the code inline when any of these hold:

- Only one or two callers exist
- The "same" code in two places is doing different things at the
  domain level (similar shape, different intent)
- Extracting would force the function to take many flag
  parameters to handle each caller's quirks
- The shared version would be longer than the sum of the
  inlined versions

A shared pattern with five boolean flags is usually two
patterns wearing the same name. Split or keep inline.

## Adding the Module

1. Create `modules/<pattern-name>.md` next to the existing
   modules in `plugins/abstract/skills/shared-patterns/modules/`.
2. Match the structure of a sibling: opening paragraph, code
   block with the pattern, table of variants, anti-patterns.
3. Add the module to the `modules:` list in `SKILL.md`
   frontmatter.
4. Add a section in the parent `SKILL.md` body that points to
   the new module under `Pattern Categories`.
5. Update each caller to reference the new module by relative
   path: `../shared-patterns/modules/<pattern-name>.md`.

## Anti-Patterns

- **Speculative extraction**: Building a shared pattern for code
  that has only one caller. There is no signal yet about what
  varies and what is fixed.
- **God module**: A single `helpers.md` that grows to hold every
  shared snippet. Prefer one focused module per pattern.
- **Renaming during extraction**: Calling the new function
  something different from what each caller called it. Forces
  reviewers to rebuild the mental map.
- **Hidden coupling**: The shared pattern reads global state
  (env vars, module-level singletons) so callers cannot tell
  from the signature what it depends on.

## Cross-Reference

See `editing.md` for changing a pattern after its first release,
and `advanced.md` for composing several patterns in one skill.
