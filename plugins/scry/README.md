# Scry

Media generation for terminal recordings (VHS), browser recordings (Playwright), GIF processing, and media composition.

## Installation

```bash
claude plugins install scry
```

Or reference directly from the marketplace:
```json
{
  "plugins": ["scry@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **vhs-recording** | Terminal recordings using VHS (Charmbracelet) with tape scripts. |
| **browser-recording** | Browser automation recordings using Playwright. |
| **gif-generation** | GIF processing and optimization. |
| **media-composition** | Combine media assets into tutorials and demos. |

### Commands

| Command | Description |
|---------|-------------|
| `/record-terminal` | Create terminal recordings with VHS tape scripts. |
| `/record-browser` | Record browser sessions using Playwright. |

## Dependencies

### VHS (Terminal Recording)

VHS is a terminal recording tool from Charmbracelet.

**macOS:**
```bash
brew install charmbracelet/tap/vhs
brew install ttyd ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
# Install VHS
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
sudo apt update && sudo apt install vhs

# Dependencies
sudo apt install ffmpeg
```

**Windows (WSL):**
Follow Linux instructions within WSL2.

### Playwright (Browser Recording)

```bash
npm install -g playwright
npx playwright install
```

### FFmpeg (Media Processing)

FFmpeg is required for GIF generation and media composition.

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

## Quick Start

### Terminal Recording
```bash
# Create a VHS tape script and record
/record-terminal

# Or use the skill
Skill(scry:vhs-recording)
```

### Browser Recording
```bash
# Record a browser session
/record-browser

# Or use the skill
Skill(scry:browser-recording)
```

**Note**: Claude Code 2.0.72+ includes native Chrome integration. Use Playwright for automated recording, CI/CD, and cross-browser support.

### GIF Generation
```bash
# Process recordings into GIFs
Skill(scry:gif-generation)
```

### Media Composition
```bash
# Combine assets into a tutorial
Skill(scry:media-composition)
```

## VHS Tape Script Example

```tape
# example.tape
Output demo.gif

Set FontSize 16
Set Width 1200
Set Height 600

Type "echo 'Hello, World!'"
Sleep 500ms
Enter
Sleep 2s
```

Run with:
```bash
vhs example.tape
```

## Structure

```
scry/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/
│   ├── record-terminal.md   # Terminal recording command
│   └── record-browser.md    # Browser recording command
├── skills/
│   ├── vhs-recording/       # VHS terminal recording skill
│   ├── browser-recording/   # Playwright browser recording skill
│   ├── gif-generation/      # GIF processing skill
│   └── media-composition/   # Media composition skill
├── Makefile
└── README.md
```

## Workflow Patterns

- **Tutorial Creation**: Use `vhs-recording` for terminal demos, `browser-recording` for web UI walkthroughs, and `media-composition` to combine them.
- **Demo Recording**: Record terminal demos with `/record-terminal` and optimize with `gif-generation`.
- **Documentation Assets**: Generate GIFs for documentation using the skill chain.

## Claude Code Compatibility

### Browser Recording Options

- **Playwright (this plugin)**: Best for automated recording, headless execution, CI/CD, cross-browser testing, and programmatic control.
- **Native Chrome (Claude Code 2.0.72+)**: Best for interactive debugging, live testing, exploring network requests, and quick interactions.

### Recommended Approach

1. **Development**: Use native Chrome integration for interactive testing.
2. **Automation**: Use Playwright specs for reliable recording.
3. **Documentation**: Use Playwright for consistent, reproducible demos.

### Image Viewing (Claude Code 2.0.73+)

Claude Code 2.0.73+ supports clickable `[Image #N]` links that open images in the default viewer.

**Benefits for Scry Workflows**:
- **Quick preview**: View generated GIFs and screenshots without leaving the terminal.
- **Verification**: Check recording output quality immediately.
- **Comparison**: Open multiple images side-by-side.
- **Iteration**: Fast preview and adjustment cycle.

**Example**:
```bash
# Generate terminal recording
/record-terminal demo.tape

# Claude shows: "Generated demo.gif [Image #1]"
# Click [Image #1] to preview.
```

See `plugins/abstract/docs/claude-code-compatibility.md` for version details.

## License

MIT
