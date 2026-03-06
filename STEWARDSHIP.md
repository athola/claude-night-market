# Stewardship

This document defines the stewardship principles for the Claude
Night Market ecosystem. Every plugin, skill, hook, and command
in this project is entrusted to the community. Our role is to
tend what we've been given and leave it better for those who
come after us.

## The Five Principles

### 1. You Are a Steward, Not an Owner

The codebase belongs to the community. You manage it on behalf
of every contributor and user who will encounter it after you.
Write code as if someone with less context than you will maintain
it tomorrow, because they will.

**Origin**: The Greek *oikonomos* (steward) managed a household
that belonged to another. The steward's authority came with
accountability: the master would return and ask for an account.

**In practice**:

- Name variables and functions for the reader, not yourself
- Write error messages that help someone who has never seen the
  code before
- Document *why*, not just *what*. The code shows what; only
  comments and commit messages preserve why.

### 2. Multiply, Do Not Merely Preserve

Maintaining the status quo is the minimum, not the goal.
Faithful stewardship means actively growing what has been
entrusted: improving test coverage, clarifying documentation,
refactoring tangled logic, adding examples that help the next
person get started faster.

**Origin**: In the Parable of the Talents (Matthew 25:14-30),
the master entrusted servants with resources. The servants who
invested and multiplied were commended. The one who buried his
talent out of fear was rebuked. Preservation without growth is
not stewardship.

**In practice**:

- When you fix a bug, add the test that would have caught it
- When you read confusing code, leave a clarifying comment
- When you learn something about a plugin, update its README
- Refactor a function you struggled with so the next person
  does not struggle too

### 3. Be Faithful in Small Things

Grand rewrites are rare. Small improvements are daily. A renamed
variable, an updated docstring, a fixed typo, a removed TODO: these
compound over time into systems that get better with age instead
of decaying. The campsite rule applies: leave every file a little
cleaner than you found it.

**Origin**: Robert Baden-Powell: "Try and leave this world a
little better than you found it." Robert C. Martin adapted this
for software: "Always leave the campground cleaner than you
found it." Also: "Whoever can be trusted with very little can
also be trusted with much" (Luke 16:10).

**In practice**:

- Fix a typo you notice in a file you're editing
- Remove dead code or unused imports while you're nearby
- Add a type annotation to a function you just called
- Update a stale example in a README you just referenced

### 4. Serve Those Who Come After You

Write for the contributor who arrives six months from now with
no context. Serve the user who installs a plugin for the first
time. Prioritize their experience over your convenience. Every
decision is an act of service or an act of neglect toward the
people who inherit your work.

**Origin**: Peter Block defines stewardship as "accountability
for the well-being of the larger organization by operating in
service, rather than in control, of those around us." His two
commitments: act in service of the long run, and act in service
to those with little power.

**In practice**:

- Write skill descriptions that tell the user *when* to use
  the skill, not just what it does
- Include error handling that guides the user toward a fix
- Keep READMEs current: stale docs are worse than no docs
- Add "Getting Started" sections for every new capability

### 5. Think Seven Iterations Ahead

Before committing a design choice, ask: will the person who
modifies this in the seventh iteration thank me or curse me?
Prefer simple, transparent patterns over clever abstractions.
Avoid premature optimization of structure. Build for
adaptability, not for prediction.

**Origin**: The Haudenosaunee (Iroquois) Great Law of Peace
counsels that decisions should consider their impact seven
generations into the future. In software, seven generations is
seven major iterations: will this pattern hold up, or will it
become the legacy code everyone works around?

**In practice**:

- Prefer flat, readable code over deep abstraction hierarchies
- Choose names that will still be clear after the feature evolves
- Design hook interfaces to be extensible without modification
- Write tests that verify behavior, not implementation details

## Applying the Principles

**When touching a plugin**, ask:

1. Did I leave this file cleaner than I found it? (Principle 3)
2. Will the next person understand what I did and why? (Principle 4)
3. Did I improve something, or just preserve the status quo?
   (Principle 2)

**When creating something new**, ask:

1. Does this serve the community or just my immediate need?
   (Principle 1)
2. Will this pattern hold up seven iterations from now?
   (Principle 5)

**When reviewing someone else's work**, ask:

1. Does this leave the codebase better than before? (Principle 3)
2. Does this serve future contributors? (Principle 4)

## See Also

- Plugin-specific stewardship guidance in each plugin's README
- `Skill(leyline:stewardship)` for layer-specific decision
  heuristics during plugin work
