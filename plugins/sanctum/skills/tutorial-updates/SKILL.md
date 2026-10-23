---
name: tutorial-updates
description: Generates or updates tutorials from VHS tapes and Playwright specs with dual-tone markdown and GIF recording. Use when tutorial assets need refreshing.
alwaysApply: false
category: artifact-generation
tags:
- tutorial
- gif
- vhs
- playwright
- documentation
- demo
tools: []
complexity: high
model_hint: deep
estimated_tokens: 1100
progressive_loading: true
modules:
- modules/manifest-parsing.md
- modules/markdown-generation.md
- modules/tape-validation.md
- modules/binary-rebuild.md
dependencies:
- sanctum:git-workspace-review
- scry:vhs-recording
- scry:browser-recording
- scry:gif-generation
- scry:media-composition
---

# Tutorial Updates Skill

Orchestrate tutorial generation with GIF recordings from VHS tape files and Playwright browser specs.


## When To Use

- Generating or updating user-facing tutorials
- Creating VHS and Playwright tutorial recordings

## When NOT To Use

- Internal documentation without user-facing tutorials
- API reference docs - use scribe:doc-generator instead

## Overview

This skill coordinates the complete tutorial generation pipeline:

1. Discover tape files and manifests in the project
2. Validate tape commands and check binary freshness
3. Rebuild binaries if stale so demos reflect latest code
4. Record terminal sessions using VHS (scry:vhs-recording)
5. Record browser sessions using Playwright (scry:browser-recording)
6. Generate optimized GIFs (scry:gif-generation)
7. Compose multi-component tutorials (scry:media-composition)
8. Generate dual-tone markdown for docs/ and book/

## Command Options

```bash
/update-tutorial quickstart        # Single tutorial by name
/update-tutorial sync mcp          # Multiple tutorials
/update-tutorial --all             # All tutorials with manifests
/update-tutorial --list            # Show available tutorials
/update-tutorial --scaffold        # Create structure without recording
```
**Verification:** Run the command with `--help` flag to verify availability.

## Required Progress Items

Create todos with these prefixes for progress tracking:

```
**Verification:** Run the command with `--help` flag to verify availability.
- tutorial-updates:discovery
- tutorial-updates:validation
- tutorial-updates:rebuild
- tutorial-updates:recording
- tutorial-updates:generation
- tutorial-updates:integration
```
**Verification:** Run the command with `--help` flag to verify availability.

## Phase 1: Discovery (`tutorial-updates:discovery`)

### Step 1.1: Locate Tutorial Assets

Find tape files and manifests in the project:

```bash
# Find manifest files
find . -name "*.manifest.yaml" -type f \
  -not -path "*/.venv/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  2>/dev/null | head -20

# Find tape files
find . -name "*.tape" -type f \
  -not -path "*/.venv/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  2>/dev/null | head -20

# Find browser specs
find . -name "*.spec.ts" -path "*/browser/*" -type f \
  -not -path "*/.venv/*" -not -path "*/__pycache__/*" \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  2>/dev/null | head -20
```
**Verification:** Run the command with `--help` flag to verify availability.

### Step 1.2: Parse Manifests

For each manifest file, extract:
- Tutorial name and title
- Component list (tape files, playwright specs)
- Output paths for GIFs
- Composition rules (layout, combine options)

See `modules/manifest-parsing.md` for manifest schema details.

### Step 1.3: Handle Options

| Option | Behavior |
|--------|----------|
| `--list` | Display discovered tutorials and exit |
| `--all` | Process all discovered manifests |
| `--scaffold` | Create directory structure and empty files without recording |
| `<names>` | Process only specified tutorials |

When `--list` is specified:
```
**Verification:** Run the command with `--help` flag to verify availability.
Available tutorials:
  quickstart     assets/tapes/quickstart.tape
  sync           assets/tapes/sync.tape (manifest)
  mcp            assets/tapes/mcp.manifest.yaml (terminal + browser)
  skill-debug    assets/tapes/skill-debug.tape
```
**Verification:** Run the command with `--help` flag to verify availability.

## Phase 1.5: Validation (`tutorial-updates:validation`)

**CRITICAL**: Validate tape commands BEFORE running VHS to avoid expensive regeneration cycles.

Four checks run per tape: VHS syntax (an `Output` directive and
balanced quotes), CLI flags in each `Type` command checked against
`--help`, demo data present and populated, and each command run locally
under a timeout to catch failures, empty output and hangs. The scripts
and the validation exit criteria are in `modules/tape-validation.md`.

### Validation Flags

| Flag | Behavior |
|------|----------|
| `--validate-only` | Run validation without generating GIF |
| `--skip-validation` | Bypass validation for rapid regeneration |

**If validation fails**: Stop immediately, report errors, and do NOT proceed to VHS recording.

## Phase 1.6: Binary Rebuild (`tutorial-updates:rebuild`)

**CRITICAL**: Ensure the binary being tested in tapes matches the latest source code. Stale binaries produce misleading demos.

Detect the build system (Cargo or Make), compare the binary's mtime with
Git HEAD, rebuild when stale, then confirm the binary is on `PATH` and
runs `--version`. The scripts, flags and rebuild exit criteria are in
`modules/binary-rebuild.md`.

**If rebuild fails**: Stop immediately, report build errors, and do NOT proceed to tape validation or VHS recording.

## Phase 2: Recording (`tutorial-updates:recording`)

### Step 2.1: Process Tape Components

For each tape file component:

1. Parse tape file for metadata annotations (@step, @docs-brief, @book-detail)
2. Validate Output directive exists
3. Invoke `Skill(scry:vhs-recording)` with tape file path
4. Verify GIF output was created

### Step 2.2: Process Browser Components

For each playwright spec component:

1. Check `requires` field for prerequisite commands (e.g., start server)
2. Launch any required background processes
3. Invoke `Skill(scry:browser-recording)` with spec path
4. Stop background processes
5. Invoke `Skill(scry:gif-generation)` to convert WebM to GIF

### Step 2.3: Handle Multi-Component Tutorials

For manifests with `combine` section:

1. Verify all component GIFs exist
2. Invoke `Skill(scry:media-composition)` with manifest
3. Verify combined output was created

## Phase 3: Generation (`tutorial-updates:generation`)

### Step 3.1: Parse Tape Annotations

Extract documentation content from tape files:

```tape
# @step Install skrills
# @docs-brief Install via cargo
# @book-detail The recommended installation method uses cargo...
Type "cargo install skrills"
```
**Verification:** Run the command with `--help` flag to verify availability.

Annotations:
- `@step` - Step title/heading
- `@docs-brief` - Concise text for project docs (docs/ directory)
- `@book-detail` - Extended text for technical book (book/ directory)

### Step 3.2: Generate Dual-Tone Markdown

Generate two versions of each tutorial:

1. **Project docs** (`docs/tutorials/<name>.md`)
   - Brief, action-oriented
   - Uses @docs-brief content
   - Focuses on commands and quick results

2. **Technical book** (`book/src/tutorials/<name>.md`)
   - Detailed, educational
   - Uses @book-detail content
   - Explains concepts and rationale

See `modules/markdown-generation.md` for formatting details.

### Step 3.3: Generate README Demo Section

Create or update demo section in README.md:

```markdown
## Demos

### Quickstart
![Quickstart demo](assets/gifs/quickstart.gif)
*Install, validate, analyze, and serve in under a minute. [Full tutorial](docs/tutorials/quickstart.md)*
```
**Verification:** Run the command with `--help` flag to verify availability.

## Phase 4: Integration (`tutorial-updates:integration`)

### Step 4.1: Verify All Outputs

Confirm all expected files exist:

```bash
# Check GIF files
for gif in assets/gifs/*.gif; do
  if [[ -f "$gif" ]]; then
    echo "OK: $gif ($(du -h "$gif" | cut -f1))"
  else
    echo "MISSING: $gif"
  fi
done

# Check markdown files
ls -la docs/tutorials/*.md 2>/dev/null
ls -la book/src/tutorials/*.md 2>/dev/null
```
**Verification:** Run the command with `--help` flag to verify availability.

### Step 4.2: Update SUMMARY.md (Book)

If the project has an mdBook structure, update `book/src/SUMMARY.md`:

```markdown
- [Tutorials](./tutorials/README.md)
  - [Quickstart](./tutorials/quickstart.md)
  - [Sync Workflow](./tutorials/sync.md)
  - [MCP Integration](./tutorials/mcp.md)
  - [Skill Debugging](./tutorials/skill-debug.md)
```
**Verification:** Run the command with `--help` flag to verify availability.

### Step 4.3: Report Results

Summarize the update:

```
**Verification:** Run the command with `--help` flag to verify availability.
Tutorial Update Complete
========================
Tutorials processed: 4
GIFs generated: 5
  - quickstart.gif (1.2MB)
  - sync.gif (980KB)
  - mcp-terminal.gif (1.5MB)
  - mcp-browser.gif (2.1MB)
  - skill-debug.gif (890KB)

Markdown generated:
  - docs/tutorials/ (4 files)
  - book/src/tutorials/ (4 files)

README demo section updated
```
**Verification:** Run the command with `--help` flag to verify availability.

## Exit Criteria

- [ ] All specified tutorials processed (or all if --all)
- [ ] GIF files created at manifest-specified paths
- [ ] Dual-tone markdown generated for each tutorial
- [ ] README demo section updated with GIF embeds
- [ ] Book SUMMARY.md updated (if applicable)
- [ ] All progress items completed

## Error Handling

| Error | Resolution |
|-------|------------|
| VHS not installed | `go install github.com/charmbracelet/vhs@latest` |
| Playwright not installed | `npm install -D @playwright/test && npx playwright install chromium` |
| Tape file missing Output | Add `Output assets/gifs/<name>.gif` directive |
| Browser spec requires server | Start server before running spec |
| GIF too large | Adjust fps/scale in gif-generation |

## Scaffold Mode

When `--scaffold` is specified, create structure without recording:

1. Create `assets/tapes/` directory
2. Create `assets/gifs/` directory
3. Create `assets/browser/` directory (if browser tutorials planned)
4. Create template tape file with metadata annotations
5. Create template manifest file
6. Create empty markdown files in docs/tutorials/ and book/src/tutorials/

Template tape file:
```tape
# @title: Tutorial Name
# @description: Brief description of the tutorial

Output assets/gifs/tutorial-name.gif
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# @step Step 1 Title
# @docs-brief Brief docs text
# @book-detail Extended book text with more context and explanation
Type "command here"
Enter
Sleep 2s
```
**Verification:** Run the command with `--help` flag to verify availability.
