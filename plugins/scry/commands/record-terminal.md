---
name: record-terminal
description: Create terminal recordings with VHS tape scripts
---

# /record-terminal

Record terminal sessions using VHS tape files for tutorials and documentation.

## Usage

```bash
/record-terminal <tape-file>           # Record from tape file
/record-terminal --init <name>         # Create new tape template
/record-terminal --validate <tape>     # Validate tape syntax
```

## Workflow

1. **Invoke skill**: `Skill(scry:vhs-recording)`
2. Follow the skill's workflow to:
   - Validate tape file exists
   - Check VHS installation
   - Execute recording
   - Verify GIF output

## Examples

```bash
# Record from existing tape
/record-terminal assets/tapes/quickstart.tape

# Create new tape template
/record-terminal --init demo

# Validate before recording
/record-terminal --validate assets/tapes/demo.tape
```

## See Also

- `Skill(scry:vhs-recording)` - Core recording skill
- `Skill(scry:gif-generation)` - Post-processing options
- VHS documentation: https://github.com/charmbracelet/vhs
