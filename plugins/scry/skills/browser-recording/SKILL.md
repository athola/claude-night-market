---
name: browser-recording
description: |
  Record browser sessions using Playwright for web UI tutorials.
  Captures video of browser interactions that can be converted to GIF.

  Triggers: browser recording, playwright, web demo, ui recording

  Use when: creating browser-based tutorials showing web UI interactions
category: media-generation
tags: [playwright, browser, recording, video, web, tutorial]
tools: [Read, Write, Bash]
complexity: medium
estimated_tokens: 500
progressive_loading: true
modules:
  - spec-execution
  - video-capture
dependencies:
  - scry:gif-generation
---

# Browser Recording Skill

Record browser sessions using Playwright to create video captures of web UI interactions for tutorials and documentation.

## Overview

This skill uses Playwright's built-in video recording to capture browser interactions. The workflow:

1. Validate Playwright installation
2. Execute a Playwright spec with video recording enabled
3. Retrieve the recorded video (WebM format)
4. Convert to GIF using the gif-generation skill

> **💡 Note**: Claude Code 2.0.72+ includes native Chrome integration for interactive browser control. This skill (Playwright) is designed for **automated recording workflows, CI/CD, and cross-browser support**. For interactive debugging and live testing, consider using native Chrome integration. Both approaches complement each other - develop interactively with Chrome, then automate with Playwright specs.

## Required TodoWrite Items

When invoking this skill, create todos for:

```
- [ ] Validate Playwright is installed and configured
- [ ] Check spec file exists at specified path
- [ ] Execute Playwright spec with video recording
- [ ] Locate and verify video output
- [ ] Convert video to GIF using gif-generation skill
```

## Process

### Step 1: Validate Playwright Installation

Check that Playwright is available:

```bash
npx playwright --version
```

If not installed, the user should run:
```bash
npm install -D @playwright/test
npx playwright install chromium
```

### Step 2: Check Spec File

Verify the Playwright spec file exists. Spec files should:
- Be located in a `specs/` or `tests/` directory
- Have `.spec.ts` or `.spec.js` extension
- Include video configuration (see spec-execution module)

### Step 3: Execute Recording

Run the spec with video enabled:

```bash
npx playwright test <spec-file> --config=playwright.config.ts
```

The config must enable video recording. See the spec-execution module for configuration details.

### Step 4: Convert to GIF

After recording completes, use the gif-generation skill to convert the WebM video to an optimized GIF:

```
Invoke scry:gif-generation with:
- input: <path-to-webm>
- output: <desired-gif-path>
- fps: 10 (recommended for tutorials)
- width: 800 (adjust based on content)
```

## Example Playwright Spec

```typescript
import { test, expect } from '@playwright/test';

test('demo workflow', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:3000');

  // Wait for page to be ready
  await page.waitForLoadState('networkidle');

  // Perform demo actions
  await page.click('button[data-testid="start"]');
  await page.waitForTimeout(500); // Allow animation to complete

  await page.fill('input[name="query"]', 'example search');
  await page.waitForTimeout(300);

  await page.click('button[type="submit"]');
  await page.waitForSelector('.results');

  // Final pause to show results
  await page.waitForTimeout(1000);
});
```

## Playwright Configuration

Create or update `playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    video: {
      mode: 'on',
      size: { width: 1280, height: 720 }
    },
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      slowMo: 100 // Slow down actions for visibility
    }
  },
  outputDir: './test-results',
});
```

## Exit Criteria

- Playwright spec executed successfully (exit code 0)
- Video file exists in output directory
- Video has non-zero file size
- GIF conversion completed (if requested)

## Error Handling

| Error | Resolution |
|-------|------------|
| Playwright not installed | Run `npm install -D @playwright/test` |
| Browser not installed | Run `npx playwright install chromium` |
| Spec file not found | Verify path and file extension |
| Video not created | Check Playwright config has video enabled |
| Empty video file | validate spec actions complete before test ends |

## Output Locations

Default output paths:
- Videos: `./test-results/<test-name>/video.webm`
- Screenshots: `./test-results/<test-name>/screenshot.png`

## See Also

- spec-execution module: Detailed Playwright execution options
- video-capture module: Video format and quality settings
- scry:gif-generation: Convert video to optimized GIF
