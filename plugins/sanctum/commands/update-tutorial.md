---
description: Generate or update tutorial documentation with accompanying GIFs using VHS terminal recording and Playwright browser recording.
---

# Update Tutorial

To generate or update tutorials with accompanying GIFs, invoke the tutorial-updates skill:

1. Run `Skill(sanctum:tutorial-updates)` with the appropriate arguments.

## Usage

```bash
/update-tutorial <name>              # Single tutorial
/update-tutorial <name1> <name2>     # Multiple tutorials
/update-tutorial --all               # All tutorials in manifest
/update-tutorial --list              # Show available tutorials
/update-tutorial --scaffold          # Create directory structure without recording
/update-tutorial --validate-only     # Validate tape without generating GIF
/update-tutorial --skip-validation   # Skip validation for rapid regeneration
```

## Validation Flags

### `--validate-only`

Run tape validation without generating GIF. Useful for CI checks or pre-commit hooks.

**Example**:
```bash
/update-tutorial quickstart --validate-only
```

**Exit codes**:
- 0: Validation passed
- 1: Validation failed (errors found)

**Use when**: You want to verify tape commands are correct before committing or before running expensive GIF generation.

### `--skip-validation`

Bypass pre-flight tape validation. Use when commands are known-good and you need rapid GIF regeneration.

**Example**:
```bash
/update-tutorial quickstart --skip-validation
```

**Warning**: Skipping validation may result in VHS failures that could have been caught earlier.

**Use when**: You've already validated the tape and are iterating on timing/styling only.

## Rebuild Flags

### `--skip-rebuild`

Skip binary freshness check and rebuild step. Use when binary is known to be current.

**Example**:
```bash
/update-tutorial quickstart --skip-rebuild
```

**Use when**: You've just rebuilt the binary manually and want to avoid redundant rebuilds.

### `--force-rebuild`

Force binary rebuild even if freshness check passes. Ensures absolute latest code.

**Example**:
```bash
/update-tutorial quickstart --force-rebuild
```

**Use when**: You want to guarantee the binary matches source, regardless of timestamps (useful after git operations that don't change timestamps).

## Workflow

The skill orchestrates scry media generation capabilities:

1. **Discovery**: Parse tutorial manifests to identify tape files and browser specs.
2. **Validation**: Test tape commands locally BEFORE recording to catch errors early.
3. **Rebuild**: Check binary freshness and rebuild if stale so demos reflect latest code.
4. **Recording**: Invoke `Skill(scry:vhs-recording)` for terminal demos and `Skill(scry:browser-recording)` for web UI demos.
5. **Processing**: Use `Skill(scry:gif-generation)` for format conversion and optimization.
6. **Composition**: Apply `Skill(scry:media-composition)` for multi-source tutorials.
7. **Documentation**: Generate dual-tone markdown (project docs and technical book).
8. **Integration**: Update README demo sections and book chapters.

## Examples

### Update Single Tutorial
```bash
/update-tutorial quickstart
```

### Update Multiple Tutorials
```bash
/update-tutorial quickstart sync mcp
```

### Regenerate All Tutorials
```bash
/update-tutorial --all
```

### Preview Available Tutorials
```bash
/update-tutorial --list
```

### Create Scaffold Only
```bash
/update-tutorial --scaffold
```
Creates the directory structure (`assets/tapes/`, `assets/gifs/`, `docs/tutorials/`) without executing recordings.

## Requirements

### Required
- **VHS** (Charmbracelet) - Terminal recording to GIF
  - Install: `brew install vhs` or `go install github.com/charmbracelet/vhs@latest`
  - Dependencies: `ttyd`, `ffmpeg` (VHS installs ttyd automatically)

### Optional (for browser tutorials)
- **Playwright** - Browser automation and video recording
  - Install: `npm install -D @playwright/test`
- **ffmpeg** - Video-to-GIF conversion (usually pre-installed)

### WSL2 Notes
- VHS works on WSL2 but may require building `ttyd` from source
- Test early; fallback to asciinema + agg if issues arise

## Manifest Format

Tutorials are defined via YAML manifests:

```yaml
# assets/tapes/mcp.manifest.yaml
name: mcp
title: "MCP Server Integration"
components:
  - type: tape
    source: mcp.tape
    output: assets/gifs/mcp-terminal.gif
  - type: playwright
    source: browser/mcp-browser.spec.ts
    output: assets/gifs/mcp-browser.gif
    requires:
      - "skrills serve"
combine:
  output: assets/gifs/mcp-combined.gif
  layout: vertical
```

## Manual Execution

If skills cannot be loaded, follow these steps:

1. **Run VHS directly**
   ```bash
   vhs assets/tapes/quickstart.tape
   ```

2. **Run Playwright recording**
   ```bash
   npx playwright test assets/browser/mcp-browser.spec.ts
   ffmpeg -i mcp-browser.webm -vf "fps=10,scale=800:-1" mcp-browser.gif
   ```

3. **Update markdown manually**
   - Edit `docs/tutorials/<name>.md` with project-doc tone
   - Edit `book/src/tutorials/<name>.md` with technical-book tone
   - Update README demo section with GIF links

## See Also

- `Skill(scry:vhs-recording)` - VHS tape execution and terminal recording
- `Skill(scry:browser-recording)` - Playwright browser automation and video capture
- `Skill(scry:gif-generation)` - Video-to-GIF conversion and optimization
- `Skill(scry:media-composition)` - Multi-source GIF stitching
