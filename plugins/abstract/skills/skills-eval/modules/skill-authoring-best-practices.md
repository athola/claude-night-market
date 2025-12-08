# Skill Authoring Best Practices

Official guidance for writing effective Skills that Claude can discover and use successfully.
Based on Claude Developer Platform documentation.

## Core Principles

### Conciseness is Key

The context window is a public good. Your Skill shares it with:
- System prompt
- Conversation history
- Other Skills' metadata
- User's actual request

**Not every token has immediate cost**: At startup, only metadata (name/description) is pre-loaded. Claude reads SKILL.md only when triggered, and additional files only as needed. However, being concise in SKILL.md still matters: once loaded, every token competes with conversation history.

**Default assumption: Claude is already very smart.**

Only add context Claude doesn't already have. Challenge each piece:
- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

**Good (≈50 tokens):**
```markdown
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

**Bad (≈150 tokens):**
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library...
```

The concise version assumes Claude knows what PDFs are and how libraries work.

### Set Appropriate Degrees of Freedom

Match specificity to task fragility and variability.

| Freedom Level | Use When | Example |
|--------------|----------|---------|
| **High** (text instructions) | Multiple valid approaches, context-dependent | Code review process |
| **Medium** (pseudocode/params) | Preferred pattern exists, some variation ok | Report templates |
| **Low** (specific scripts) | Operations fragile, consistency critical | Database migrations |

**Analogy - Claude as robot exploring a path:**
- **Narrow bridge with cliffs**: One safe way forward → specific guardrails (low freedom)
- **Open field, no hazards**: Many paths succeed → general direction (high freedom)

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

Use gerund form (verb + -ing) for clarity:
- ✓ `processing-pdfs`, `analyzing-spreadsheets`, `testing-code`
- ✓ Alternative: `pdf-processing`, `process-pdfs`
- ✗ Avoid: `helper`, `utils`, `tools`, `documents`

Consistent naming makes it easier to:
- Reference Skills in documentation and conversations
- Understand what a Skill does at a glance
- Organize and search through multiple Skills
- Maintain a professional, cohesive skill library

### Writing Effective Descriptions

**Always write in third person** (injected into system prompt):
- ✓ "Processes Excel files and generates reports"
- ✗ "I can help you process Excel files"
- ✗ "You can use this to process Excel files"

**Be specific with key terms** - Claude uses description to select from 100+ Skills:

```yaml
# Good - specific triggers
description: Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Bad - too vague
description: Helps with documents
```

Each Skill has exactly one description field. The description is critical for skill selection: Claude uses it to choose the right Skill from potentially 100+ available Skills.

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

### Pattern 2: Domain-Specific Organization

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing)
    ├── sales.md (pipeline, accounts)
    └── product.md (API usage, features)
```

When user asks about sales, Claude reads only `reference/sales.md`. This keeps token usage low and context focused.

### Pattern 3: Conditional Details

```markdown
## Creating documents
Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
For simple edits, modify XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

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

Claude can then read the complete file or jump to specific sections as needed.

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

### Implement Feedback Loops

**Pattern: Run validator → fix errors → repeat**

This pattern greatly improves output quality.

```markdown
## Document editing process

1. Make edits to `word/document.xml`
2. **Validate immediately**: `python scripts/validate.py dir/`
3. If validation fails:
   - Review error message
   - Fix issues in XML
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild document
```

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

| ✓ Consistent | ✗ Inconsistent |
|--------------|----------------|
| Always "API endpoint" | Mix "URL", "route", "path" |
| Always "field" | Mix "box", "element", "control" |
| Always "extract" | Mix "pull", "get", "retrieve" |

Consistency helps Claude understand and follow instructions.

## Common Patterns

### Template Pattern

For strict requirements:
```markdown
## Report structure

ALWAYS use this exact template:

```markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview]

## Key findings
- Finding 1 with data
- Finding 2 with data
```
```

For flexible guidance:
```markdown
## Report structure

Sensible default format (adapt as needed):
...
```

### Examples Pattern

Provide input/output pairs:

```markdown
## Commit message format

**Example 1:**
Input: Added user auth with JWT
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed date bug in reports
Output:
```
fix(reports): correct date formatting in timezone conversion
```
```

Examples help Claude understand desired style and detail more clearly than descriptions alone.

### Conditional Workflow Pattern

```markdown
## Document modification workflow

1. Determine modification type:
   **Creating new content?** → Follow "Creation workflow"
   **Editing existing?** → Follow "Editing workflow"

2. Creation workflow:
   - Use docx-js library
   - Build from scratch
   ...

3. Editing workflow:
   - Unpack existing document
   - Modify XML directly
   ...
```

If workflows become large, push them into separate files.

## Evaluation and Iteration

### Build Evaluations First

Create evaluations BEFORE extensive documentation. This ensures your Skill solves real problems rather than documenting imagined ones.

**Evaluation-driven development:**
1. **Identify gaps**: Run Claude on tasks without a Skill. Document specific failures
2. **Create evaluations**: Build 3 scenarios testing those gaps
3. **Establish baseline**: Measure performance without Skill
4. **Write minimal instructions**: Just enough to address gaps and pass evaluations
5. **Iterate**: Execute, compare against baseline, refine

This approach ensures you're solving actual problems rather than anticipating requirements that may never materialize.

**Evaluation structure:**
```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF and save to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Successfully reads PDF using appropriate library",
    "Extracts text from all pages without missing any",
    "Saves to output.txt in readable format"
  ]
}
```

Evaluations are your source of truth for measuring Skill effectiveness.

### Develop Skills Iteratively with Claude

Work with one Claude instance ("Claude A") to create a Skill for other instances ("Claude B"). Claude A helps design and refine instructions; Claude B tests them in real tasks.

**Creating a new Skill:**

1. **Complete a task without a Skill**: Work through a problem with Claude A using normal prompting. Note what context you provide, what explanations you give, what preferences you share.

2. **Identify the reusable pattern**: What context would help similar future tasks?
   - Example: BigQuery analysis → table names, field definitions, filtering rules like "always exclude test accounts"

3. **Ask Claude A to create a Skill**: "Create a Skill that captures this BigQuery analysis pattern we just used."
   - Claude understands the Skill format natively—no special prompts needed

4. **Review for conciseness**: Check that Claude A hasn't added unnecessary explanations
   - "Remove the explanation about what win rate means - Claude already knows that"

5. **Improve information architecture**: Ask Claude A to organize content effectively
   - "Organize this so the table schema is in a separate reference file"

6. **Test on similar tasks**: Use the Skill with Claude B (fresh instance) on related use cases

7. **Iterate based on observation**: If Claude B struggles, return to Claude A with specifics
   - "When Claude used this Skill, it forgot to filter by date for Q4. Should we add a section about date filtering patterns?"

### Iterating on Existing Skills

The hierarchical pattern continues for improvements. Alternate between:
- Working with Claude A (the expert who refines the Skill)
- Testing with Claude B (the agent using the Skill for real work)
- Observing Claude B's behavior and bringing insights back to Claude A

**Process:**
1. Use the Skill in real workflows with Claude B
2. Observe behavior: struggles, successes, unexpected choices
3. Return to Claude A: Share SKILL.md and describe observations
4. Review Claude A's suggestions
5. Apply changes and test again with Claude B
6. Repeat based on usage

**Why this works**: Claude A understands agent needs, you provide domain expertise, Claude B reveals gaps through real usage, and iterative refinement improves Skills based on observed behavior rather than assumptions.

### Gathering Team Feedback

Share Skills with teammates and observe their usage:
- Does the Skill activate when expected?
- Are instructions clear?
- What's missing?

Incorporate feedback to address blind spots in your own usage patterns.

### Observe Navigation Patterns

Watch for:
- **Unexpected exploration paths**: Structure may not be intuitive
- **Missed connections**: Links may need to be more explicit
- **Overreliance on sections**: Content might belong in SKILL.md
- **Ignored content**: File might be unnecessary or poorly signaled

The 'name' and 'description' in your Skill's metadata are particularly critical. Claude uses these when deciding whether to trigger the Skill.

## Anti-Patterns to Avoid

### Windows-Style Paths
- ✓ `scripts/helper.py`, `reference/guide.md`
- ✗ `scripts\helper.py`, `reference\guide.md`

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

Handle errors rather than failing:

```python
# Good - handle explicitly
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''
    except PermissionError:
        print(f"Cannot access {path}, using default")
        return ''

# Bad - punt to Claude
def process_file(path):
    return open(path).read()  # Just fails
```

### Document Configuration Constants

```python
# Good - self-documenting
REQUEST_TIMEOUT = 30  # HTTP requests typically complete within 30s
MAX_RETRIES = 3       # Most intermittent failures resolve by second retry

# Bad - magic numbers
TIMEOUT = 47  # Why 47?
```

Configuration parameters should be justified and documented to avoid "voodoo constants" (Ousterhout's law).

### Provide Utility Scripts

Benefits over Claude-generated code:
- More reliable than generated code
- Save tokens (no code in context)
- Save time (no generation required)
- Ensure consistency across uses

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
- ✓ `BigQuery:bigquery_schema`
- ✓ `GitHub:create_issue`
- ✗ `bigquery_schema` (may fail with multiple servers)

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
- Bundle comprehensive resources freely
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
