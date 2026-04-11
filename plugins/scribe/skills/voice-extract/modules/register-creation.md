---
module: register-creation
category: voice-extraction
dependencies: [Write]
estimated_tokens: 400
---

# Register Creation Module

Create voice registers from extraction output.

## Default Register

After extraction completes, create the default register at
`~/.claude/voice-profiles/{name}/registers/default.md`:

```markdown
# Register: default

## Context

Default writing voice for {profile_name}. Use when no
specific register is requested.

## Vocabulary

{extraction vocabulary section - actionable directives}

## Sentence Structure

{extraction sentence structure section}

## Rhetorical Techniques

{extraction rhetorical techniques section}

## Voice Qualities

{extraction voice qualities section}
```

## Additional Registers

Users may want registers for different contexts (casual,
technical, narrative, advocacy). To create an additional
register:

1. Select samples that represent that specific context
2. Re-run extraction on the subset
3. Identify what differs from the default register
4. Create a register file with only the differences

**Register file for non-default**:

```markdown
# Register: {name}

## Context

{When to use this register}

## Inherits

default (all features from default apply unless overridden)

## Overrides

{Features that differ from default register}

## Additions

{Features unique to this register not in default}
```

## Register Detection

When the voice-generate skill activates, select register by:

1. Explicit user request ("use casual register")
2. Context matching (if register has context triggers)
3. Default fallback

## Per-Project Overrides

If `.voice/override.md` exists in the project root, merge
its contents with the active register. Project overrides
take precedence over profile-level features.

```markdown
# Project Voice Override

## Context

{Why this project needs different voice settings}

## Overrides

{Features to change for this project}

## Additional Banned Phrases

{Project-specific phrases to avoid}
```
