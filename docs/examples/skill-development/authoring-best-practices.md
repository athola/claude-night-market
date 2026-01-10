# Skill Authoring Best Practices

Official guidance for writing effective Skills that Claude can discover and use successfully.
Based on Claude Developer Platform documentation.

## Core Principles

### Conciseness is Key

Context window is shared with system prompt, conversation history, and other Skills. Only metadata loads at startup; SKILL.md loads when triggered.

**Default assumption: Claude is already smart.** Only add context Claude doesn't have.

**Good (≈50 tokens):**
```python
# Extract PDF text
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

**Bad (≈150 tokens):** Explaining what PDFs are, how libraries work, etc.

### Set Appropriate Degrees of Freedom

Match specificity to task fragility and variability.

| Freedom Level | Use When | Example |
|--------------|----------|---------|
| **High** (text instructions) | Multiple valid approaches, context-dependent | Code review process |
| **Medium** (pseudocode/params) | Preferred pattern exists, some variation ok | Report templates |
| **Low** (specific scripts) | Operations fragile, consistency critical | Database migrations |


### Test with All Target Models

Skills effectiveness depends on underlying model:
- **Haiku**: Does the Skill provide enough guidance?
- **Sonnet**: Is the Skill clear and efficient?
- **Opus**: Does the Skill avoid over-explaining?

What works for Opus might need more detail for Haiku. If using across multiple models, aim for instructions that work well with all of them.

## Skill Structure Requirements

### YAML Frontmatter

**name** field:
- Maximum 64 characters
- Lowercase letters, numbers, hyphens only
- No XML tags
- No reserved words: "anthropic", "claude"

**description** field:
- Non-empty, maximum 1024 characters
- No XML tags
- Include WHAT it does AND WHEN to use it

### Naming Conventions

Use gerund form (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`, `testing-code`

Avoid generic names: `helper`, `utils`, `tools`, `documents`

### Writing Effective Descriptions

**Always write in third person** (injected into system prompt):
- OK "Processes Excel files and generates reports"
- FAIL "I can help you process Excel files"
- FAIL "You can use this to process Excel files"

**Be specific with key terms** - Claude uses description to select from 100+ Skills:

```yaml
# Good - specific triggers
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Bad - too vague
description: Helps with documents
```


## Progressive Disclosure Patterns

SKILL.md serves as overview pointing to detailed materials (like table of contents).

**Keep SKILL.md body under 500 lines** for optimal performance. Split content into separate files when approaching this limit.

### Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick start
[Essential content here]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
```

Claude loads FORMS.md only when needed.


### Avoid Deeply Nested References

Claude may only preview nested files (using `head -100`), resulting in incomplete information.

**Bad - too deep:**
```
SKILL.md → advanced.md → details.md → actual info
```

**Good - one level deep:**
```
SKILL.md → advanced.md
         → reference.md
         → examples.md
```

### Structure Long Reference Files

For files >100 lines, include table of contents at top:

```markdown
# API Reference

## Contents
- Authentication and setup
- Core methods (create, read, update, delete)
- Advanced features
- Error handling
- Code examples

## Authentication and setup
...
```

## Workflows and Feedback Loops

### Use Workflows for Complex Tasks

Break complex operations into clear, sequential steps. Provide checklists Claude can track:

**Example 1: Research synthesis (without code):**
```markdown
## Research synthesis workflow

Copy this checklist and track your progress:

```
Research Progress:
- [ ] Step 1: Read all source documents
- [ ] Step 2: Identify key themes
- [ ] Step 3: Cross-reference claims
- [ ] Step 4: Create structured summary
- [ ] Step 5: Verify citations
```

**Step 1: Read all source documents**
Review each document in the `sources/` directory...
```

**Example 2: PDF form filling (with code):**
```markdown
## PDF form filling workflow

Copy this checklist and check off items:

```
Task Progress:
- [ ] Step 1: Analyze form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill form (run fill_form.py)
- [ ] Step 5: Verify output (run verify_output.py)
```

**Step 1: Analyze the form**
Run: `python scripts/analyze_form.py input.pdf`
...
```

Clear steps prevent Claude from skipping critical validation.

## Content Guidelines

### Avoid Time-Sensitive Information

**Bad:**
```markdown
If you're doing this before August 2025, use old API.
After August 2025, use new API.
```

**Good (use collapsible "old patterns"):**
```markdown
## Current method
Use the v2 API endpoint: `api.example.com/v2/messages`

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>
The v1 API used: `api.example.com/v1/messages`
</details>
```

### Use Consistent Terminology

Choose one term and use throughout:

| OK Consistent | FAIL Inconsistent |
|--------------|----------------|
| Always "API endpoint" | Mix "URL", "route", "path" |
| Always "field" | Mix "box", "element", "control" |
| Always "extract" | Mix "pull", "get", "retrieve" |

Consistency helps Claude understand and follow instructions.

## Common Patterns

### Template Pattern

Provide exact templates for strict requirements. For flexible cases, offer "sensible defaults (adapt as needed)".

### Examples Pattern

Use input/output pairs to show desired style and detail.

### Conditional Workflow Pattern

Break workflows into conditional paths based on context. Use separate files for large workflows.

## Evaluation and Iteration

### Build Evaluations First

Create evaluations BEFORE extensive documentation to validate real problem-solving.

**Evaluation-driven approach**: Identify gaps → Create eval scenarios → Establish baseline → Write minimal instructions → Iterate.

### Develop Skills Iteratively with Claude

Work with one Claude instance ("Claude A") to create a Skill for other instances ("Claude B"). Claude A helps design and refine instructions; Claude B tests them in real tasks.

**Creating a new Skill:**

1. Complete task without Skill (note context provided)
2. Identify reusable pattern
3. Ask Claude to create Skill
4. Review for conciseness
5. Improve information architecture
6. Test with fresh instance
7. Iterate based on observation

### Iterating on Existing Skills

The hierarchical pattern continues for improvements. Alternate between:
- Working with Claude A (the expert who refines the Skill)
- Testing with Claude B (the agent using the Skill for real work)
- Observing Claude B's behavior and bringing insights back to Claude A

**Iterative process**: Use Skill → Observe → Refine → Test → Repeat

### Gathering Team Feedback

Share Skills with teammates and observe their usage:
- Does the Skill activate when expected?
- Are instructions clear?
- What's missing?

Incorporate feedback to address blind spots in your own usage patterns.


## Anti-Patterns to Avoid

### Windows-Style Paths
- OK `scripts/helper.py`, `reference/guide.md`
- FAIL `scripts\helper.py`, `reference\guide.md`

Unix-style paths work across all platforms.

### Offering Too Many Options

**Bad:**
```markdown
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...
```

**Good:**
```markdown
Use pdfplumber for text extraction:
```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image with pytesseract.
```

Don't present multiple approaches unless necessary. Provide a default with escape hatch.

## Advanced: Skills with Executable Code

### Solve, Don't Punt

Handle errors explicitly rather than failing silently.

### Document Configuration Constants

Justify magic numbers with comments explaining the reasoning.

### Provide Utility Scripts

Benefits over Claude-generated code:
- More reliable than generated code
- Save tokens (no code in context)
- Save time (no generation required)
- validate consistency across uses

Make clear whether Claude should **execute** or **read** scripts:
- "Run analyze_form.py to extract fields" (execute)
- "See analyze_form.py for extraction algorithm" (read as reference)

For most utility scripts, execution is preferred—more reliable and efficient.

### Create Verifiable Intermediate Outputs

**Plan-validate-execute pattern:**

1. Claude creates plan file (e.g., `changes.json`)
2. Script validates plan before execution
3. Only proceed if validation passes

Benefits:
- Catches errors early
- Machine-verifiable
- Reversible planning
- Clear debugging

When to use: Batch operations, destructive changes, complex validation rules, high-stakes operations.

**Implementation tip**: Make validation scripts verbose with specific error messages like "Field 'signature_date' not found. Available fields: customer_name, order_total, signature_date_signed" to help Claude fix issues.

### Use Visual Analysis

When inputs can be rendered as images, have Claude analyze them:

```markdown
## Form layout analysis

1. Convert PDF to images:
   ```bash
   python scripts/pdf_to_images.py form.pdf
   ```

2. Analyze each page image to identify form fields
3. Claude can see field locations and types visually
```

Claude's vision capabilities help understand layouts and structures.

### Package Dependencies

Skills run in code execution environment with platform-specific limitations:
- **claude.ai**: Can install from npm/PyPI, pull from GitHub
- **Anthropic API**: No network access, no runtime package installation

List required packages in SKILL.md and verify availability.

### MCP Tool References

Always use fully qualified names:
- OK `BigQuery:bigquery_schema`
- OK `GitHub:create_issue`
- FAIL `bigquery_schema` (may fail with multiple servers)

Format: `ServerName:tool_name`

### Avoid Assuming Tools are Installed

**Bad:**
```markdown
Use the pdf library to process the file.
```

**Good:**
```markdown
Install required package: `pip install pypdf`

Then use it:
```python
from pypdf import PdfReader
reader = PdfReader("file.pdf")
```
```

## Runtime Environment Notes

- **Metadata pre-loaded**: name/description in system prompt at startup
- **Files read on-demand**: Claude uses bash/Read tools when needed
- **Scripts executed efficiently**: Only output consumes tokens
- **No context penalty for large files**: Until actually read

**Implications:**
- File paths matter (use forward slashes)
- Name files descriptively (`form_validation.md` not `doc2.md`)
- Bundle detailed resources freely
- Prefer scripts for deterministic operations
- Test file access patterns—verify Claude can navigate your structure

## For Claude 4.x Models

Claude Opus 4.5 is more responsive to system prompts. If prompts were designed to reduce undertriggering, they may now overtrigger.

**Fix**: Dial back aggressive language
- Old: "CRITICAL: You MUST use this tool when..."
- New: "Use this tool when..."

## Technical Notes

### Token Budgets

Keep SKILL.md body under 500 lines for optimal performance. If content exceeds this, split into separate files using progressive disclosure patterns.

### Checklist Reference

See `authoring-checklist.md` for quick-reference validation checklist before sharing Skills.
