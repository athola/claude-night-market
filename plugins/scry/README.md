# Scry

Media generation for terminal recordings, browser automation, GIF processing, and tutorial composition.

## Overview

Scry manages terminal and browser recordings to create technical demos and tutorials. It uses VHS (Charmbracelet) for terminal tape scripts and Playwright for browser automation, allowing for both interactive and programmatic recording workflows. The plugin also handles GIF optimization and media composition to combine disparate assets into cohesive documentation.

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

## Quick Start and Workflow Patterns

To create a tutorial, use `vhs-recording` for terminal demonstrations and `browser-recording` for web interface walkthroughs. These assets can then be merged using the `media-composition` skill. For standalone demos, record terminal sessions directly with `/record-terminal` and optimize the final output through `gif-generation`.

Playwright is recommended for automated recording and CI/CD environments, while Claude Code's native Chrome integration is often better for interactive debugging. When generating media, Claude Code 2.0.73+ supports clickable image links that allow for immediate verification of recording quality within the default viewer.
