# scry

Media generation for terminal recordings, browser recordings, GIF processing, and media composition.

## Overview

Scry creates documentation assets through terminal recordings (VHS), browser automation recordings (Playwright), GIF processing, and multi-source media composition. Use it to build tutorials, demos, and README assets.

## Installation

```bash
/plugin install scry@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `vhs-recording` | Terminal recordings using VHS tape scripts | CLI demos, tool tutorials |
| `browser-recording` | Browser recordings using Playwright | Web UI walkthroughs |
| `gif-generation` | GIF processing and optimization | README assets, docs |
| `media-composition` | Combine multiple media sources | Full tutorials |

## Commands

| Command | Description |
|---------|-------------|
| `/record-terminal` | Create terminal recording with VHS |
| `/record-browser` | Record browser session with Playwright |

## Usage Examples

### Terminal Recording

```bash
/record-terminal

# Or use the skill directly
Skill(scry:vhs-recording)
```

Creates a VHS tape script and records terminal output to GIF or video.

### Browser Recording

```bash
/record-browser

# Or use the skill directly
Skill(scry:browser-recording)
```

Records browser sessions with Playwright for web UI documentation.

### GIF Generation

```bash
Skill(scry:gif-generation)

# Optimizes recordings for documentation:
# - Resize for README display
# - Compress file size
# - Adjust frame rate
```

### Media Composition

```bash
Skill(scry:media-composition)

# Combines assets:
# - Terminal + browser recordings
# - Multiple clips into tutorials
# - Add transitions and captions
```

## VHS Tape Script Example

VHS uses tape scripts to define recordings:

```tape
# demo.tape
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
vhs demo.tape
```

## Dependencies

### VHS (Terminal Recording)

**macOS:**
```bash
brew install charmbracelet/tap/vhs
brew install ttyd ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
sudo apt update && sudo apt install vhs
sudo apt install ffmpeg
```

### Playwright (Browser Recording)

```bash
npm install -g playwright
npx playwright install
```

### FFmpeg (Media Processing)

Required for GIF generation and media composition.

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

## Workflow Patterns

### Tutorial Creation

1. Record terminal demo with `vhs-recording`
2. Record web UI walkthrough with `browser-recording`
3. Combine with `media-composition`
4. Optimize output with `gif-generation`

### Quick Demo

```bash
/record-terminal
# Creates demo.gif ready for README
```

### Documentation Assets

```bash
# Generate multiple GIFs for docs
Skill(scry:vhs-recording)
Skill(scry:gif-generation)
# Move outputs to docs/images/
```

## Integration with sanctum

Scry integrates with sanctum for PR and documentation workflows:

```bash
# Generate demo for PR description
/record-terminal

# Include in PR body
/sanctum:pr
```

## Related Plugins

- **sanctum**: PR preparation uses scry for demo assets
- **memory-palace**: Store and organize media assets
