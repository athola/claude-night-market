# VHS Tapes Directory

VHS tape files for generating tutorial GIFs.

## Available Tapes

| Tape | Output | Description | Duration |
|------|--------|-------------|----------|
| [skills-showcase.tape](skills-showcase.tape) | [skills-showcase.gif](../gifs/skills-showcase.gif) | Skill discovery and workflow demonstration | ~90s |

## Recording Instructions

### Prerequisites

- **VHS** (Charmbracelet): `brew install vhs` or `go install github.com/charmbracelet/vhs@latest`
- **ffmpeg**: Usually pre-installed with VHS

### Generate GIF

```bash
# Single tape
vhs assets/tapes/skills-showcase.tape

# Verify output
ls -lh assets/gifs/skills-showcase.gif
```

### Using the Tutorial-Updates Skill

For automated generation with validation:

```
/update-tutorial skills-showcase
```

This will:
1. Validate tape commands locally
2. Generate the GIF via VHS
3. Update documentation (docs/ and book/)
4. Integrate into README and SUMMARY

## Tape Format

VHS tapes use a simple command syntax:

```tape
# Metadata annotations
# @step Step Title
# @docs-brief Concise documentation text
# @book-detail Extended educational text

Output path/to/output.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Catppuccin Mocha"

Type "command here"
Enter
Sleep 2s
```

### Annotations

- `@step` - Step heading in generated markdown
- `@docs-brief` - Text for project docs (concise, action-oriented)
- `@book-detail` - Text for technical book (detailed, educational)

These annotations are parsed by the `tutorial-updates` skill to generate dual-tone documentation.

## Best Practices

1. **Keep it focused**: 60-90 seconds max
2. **Use sleeps liberally**: Allow viewers to read output
3. **Clear between sections**: Use `clear` to reset the screen
4. **Show real value**: Demonstrate actual project workflows
5. **Annotate thoroughly**: `@docs-brief` and `@book-detail` enable automation

## See Also

- [Tutorial Updates Skill](../../plugins/sanctum/skills/tutorial-updates/SKILL.md)
- [VHS Documentation](https://github.com/charmbracelet/vhs)
- [Scry Plugin](../../plugins/scry/) - Media generation capabilities
