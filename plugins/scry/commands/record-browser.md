---
name: record-browser
description: Record browser sessions using Playwright
---

# /record-browser

Record browser sessions using Playwright specs for web UI tutorials.

## Usage

```bash
/record-browser <spec-file>            # Record from Playwright spec
/record-browser --init <name>          # Create new spec template
/record-browser --config               # Show Playwright config
```

## Workflow

1. **Invoke skill**: `Skill(scry:browser-recording)`
2. Follow the skill's workflow to:
   - Validate Playwright installation
   - Check spec file exists
   - Execute recording with video
   - Convert to GIF using gif-generation

## Examples

```bash
# Record from existing spec
/record-browser specs/dashboard-demo.spec.ts

# Create new spec template
/record-browser --init login-flow

# Check Playwright config
/record-browser --config
```

## Requirements

- Node.js and npm
- Playwright: `npm install -D @playwright/test`
- Browsers: `npx playwright install chromium`

## See Also

- `Skill(scry:browser-recording)` - Core recording skill
- `Skill(scry:gif-generation)` - Video to GIF conversion
- Playwright docs: https://playwright.dev/
