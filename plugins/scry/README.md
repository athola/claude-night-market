# Scry - Media Generation Plugin

Media generation capabilities for terminal recordings (VHS), browser recordings (Playwright), GIF processing, and media composition.

## Installation

Add to your Claude Code plugins:
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
| **vhs-recording** | Terminal recordings using VHS (Charmbracelet) with tape scripts |
| **browser-recording** | Browser automation recordings using Playwright |
| **gif-generation** | GIF processing and optimization workflows |
| **media-composition** | Combine multiple media assets into tutorials and demos |

### Commands

| Command | Description |
|---------|-------------|
| `/record-terminal` | Create terminal recordings with VHS tape scripts |
| `/record-browser` | Record browser sessions using Playwright |

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

# Or use the skill directly
Skill(scry:vhs-recording)
```

### Browser Recording
```bash
# Record a browser session
/record-browser

# Or use the skill directly
Skill(scry:browser-recording)
```

### GIF Generation
```bash
# Process recordings into optimized GIFs
Skill(scry:gif-generation)
```

### Media Composition
```bash
# Combine multiple assets into a tutorial
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

## Plugin Structure

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

**Tutorial Creation**: Use `vhs-recording` to capture terminal demos, `browser-recording` for web UI walkthroughs, then `media-composition` to combine into a cohesive tutorial.

**Demo Recording**: Quick terminal demo with `/record-terminal`, optimize output with `gif-generation`.

**Documentation Assets**: Generate GIFs for README files and documentation using the full skill chain.

## License

MIT
