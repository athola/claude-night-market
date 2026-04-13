---
module: register-selection
category: voice-generation
dependencies: [Read, Bash]
estimated_tokens: 300
---

# Register Selection Module

Choose the appropriate voice register for generation.

## Selection Priority

1. **Explicit request**: User says "use casual register"
2. **Context match**: Register metadata matches the task
3. **Default**: Fall back to `registers/default.md`

## Context Matching

Each register file has a `## Context` section describing
when to use it. Match against the user's stated purpose:

```
User: "Write a blog post about..."     -> default or narrative
User: "Draft a technical doc for..."   -> technical
User: "Reply to this Reddit thread..." -> casual
User: "Write an email to my team..."   -> professional
```

## Register Loading

```bash
PROFILE_DIR="$HOME/.claude/voice-profiles/$PROFILE_NAME"
REGISTER_FILE="$PROFILE_DIR/registers/${REGISTER_NAME}.md"

if [ ! -f "$REGISTER_FILE" ]; then
  echo "Register '$REGISTER_NAME' not found. Available:"
  ls "$PROFILE_DIR/registers/"
  echo "Using default register."
  REGISTER_FILE="$PROFILE_DIR/registers/default.md"
fi
```

## Inheritance

Non-default registers inherit from default unless they
explicitly override a section. When loading a non-default
register:

1. Read `default.md` as base
2. Read `{name}.md` for overrides and additions
3. Merge: override sections replace, additions append

## Listing Available Registers

When user asks what registers exist:

```bash
echo "Available voice registers for $PROFILE_NAME:"
for f in "$PROFILE_DIR/registers/"*.md; do
  name=$(basename "$f" .md)
  context=$(grep -A1 "^## Context" "$f" | tail -1)
  echo "  $name: $context"
done
```
