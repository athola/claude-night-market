# Scribe

Documentation review, cleanup, and generation with AI slop detection.

## Installation

```bash
claude plugins install scribe
```

Or reference from the marketplace:
```json
{
  "plugins": ["scribe@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **slop-detector** | Detect AI-generated content markers |
| **style-learner** | Extract writing style from exemplar text |
| **doc-generator** | Generate/remediate documentation |
| **tech-tutorial** | Plan, draft, and refine technical tutorials |
| **voice-extract** | SICO comparative extraction from writing samples |
| **voice-generate** | Generate text in a learned writing voice |
| **voice-review** | Dual-gate review (prose + craft) against voice profile |
| **voice-learn** | Learning loop from manual edits to improve profile |

### Commands

| Command | Description |
|---------|-------------|
| `/slop-scan` | Scan files for AI slop markers |
| `/style-learn` | Create style profile from examples |
| `/doc-polish` | Clean up AI-generated content |
| `/doc-generate` | Generate new documentation |
| `/voice-extract` | Extract your writing voice from samples |
| `/voice-generate` | Generate text in your trained voice |
| `/voice-review` | Review text against your voice profile |
| `/voice-learn` | Teach the system from your manual edits |
| `Agent(scribe:doc-verifier)` | Validate documentation claims with proof-of-work (agent-only) |

### Agents

| Agent | Description |
|-------|-------------|
| **doc-editor** | Interactive documentation editing. |
| **slop-hunter** | Detection of AI-generated markers and tropes. |
| **prose-reviewer** | AI pattern detection, banned phrases, voice drift. |
| **craft-reviewer** | Naming, aphoristic destinations, structural devices. |
| **doc-verifier** | QA validation using proof-of-work methodology. |

## Quick Start

### Detect AI Slop

```bash
# Scan current directory
/slop-scan

# Scan specific file with fix suggestions
/slop-scan README.md --fix
```

### Clean Up Content

```bash
# Interactive polish
/doc-polish docs/guide.md

# Polish all markdown files
/doc-polish **/*.md
```

### Learn a Style

```bash
# Create style profile from examples
/style-learn good-examples/*.md --name house-style

# Generate with learned style
/doc-generate readme --style house-style
```

### Voice Craft (SICO-based)

Train the agent to write in your voice using comparative
extraction from your own writing samples.

```bash
# Extract voice from a directory of writing samples
/voice-extract myvoice --samples-dir ~/my-writing/

# Generate text in your extracted voice
/voice-generate myvoice

# Review any text against your voice profile
/voice-review draft.md --profile myvoice

# After manual edits, teach the system what you changed
/voice-learn final.md --profile myvoice
```

The extraction uses SICO Phase 1 (comparative feature analysis)
to identify what makes YOUR writing distinctive compared to
Claude's default output. Profiles are stored per-user at
`~/.claude/voice-profiles/` with optional per-project overrides
in `.voice/`.

### Verify Documentation

Documentation verification is now agent-only via `Agent(scribe:doc-verifier)`:

```bash
# Verify README claims and commands
# Use the doc-verifier agent directly:
Agent(scribe:doc-verifier) "Verify README.md claims and commands"
```

## AI Slop Detection

Scribe detects patterns that reveal AI-generated content.

### Tier 1 Words (Highest Confidence)

Words that appear dramatically more often in AI text: delve, tapestry, realm,
embark, beacon, multifaceted, nuanced, pivotal, meticulous, showcasing,
leveraging, streamline, comprehensive.

### Phrase Patterns

Formulaic constructions like "In today's fast-paced world," "cannot be
overstated," "navigate the complexities," and "treasure trove of."

### Structural Markers

Overuse of em dashes, excessive bullet points, uniform sentence length,
perfect grammar without contractions.

### Fiction-Specific Tells

Physical cliches ("breath he didn't know he was holding"),
emotion washing ("relief washed over"),
vague depth markers ("something in his eyes").

## Writing Principles

Scribe enforces a grounded writing style by requiring specific claims over
adjectives and removing formulaic openers or closers.
It emphasizes authorial perspective by including reasoning and trade-offs,
varies sentence structure to avoid monotony,
and prioritizes active voice for direct, clear communication.

## Vocabulary Substitutions

| Instead of | Use |
|------------|-----|
| leverage | use |
| utilize | use |
| comprehensive | thorough |
| robust | solid |
| facilitate | help |
| optimize | improve |
| delve | explore |
| embark | start |

## Examples

These examples show slop remediation in practice.
Each pair includes a score reduction from the detector.

### Example 1: Vocabulary Slop

**Before** (score: 8/10):
> "This comprehensive solution leverages cutting-edge technology to delve into the multifaceted realm of documentation quality."

**After** (score: 1/10):
> "This solution uses modern tools to check documentation quality."

Removed: comprehensive, leverages, delve, multifaceted, realm.

### Example 2: Structural Patterns (Em Dash Overuse)

**Before** (score: 7/10):
> "The system—which processes requests—handles validation—ensuring data integrity—before returning results."

**After** (score: 1/10):
> "The system processes requests and handles validation to ensure data integrity before returning results."

Four em dashes collapsed into a single flowing sentence.

### Example 3: Phrase Patterns

**Before** (score: 9/10):
> "In today's fast-paced world, it's worth noting that this tool cannot be overstated as a testament to documentation quality."

**After** (score: 1/10):
> "This tool improves documentation quality by detecting and flagging AI-generated patterns."

Removed: "In today's fast-paced world," opener,
"it's worth noting that," and "cannot be overstated."

## Plugin Structure

```
scribe/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── doc-editor.md
│   ├── slop-hunter.md
│   └── doc-verifier.md
├── commands/
│   ├── slop-scan.md
│   ├── style-learn.md
│   ├── doc-polish.md
│   └── doc-generate.md
├── skills/
│   ├── shared/
│   ├── slop-detector/
│   │   └── modules/
│   ├── style-learner/
│   │   └── modules/
│   ├── doc-generator/
│   │   └── modules/
│   └── tech-tutorial/
│       └── modules/
└── README.md
```

## Integration

Scribe integrates with other claude-night-market plugins:

### Sanctum Documentation Workflows

| Sanctum Command | Scribe Integration |
|-----------------|-------------------|
| `/pr-review` | Runs `slop-detector` on changed `.md` files, uses `doc-generator` principles for PR descriptions |
| `/update-docs` | Runs `slop-detector` on edited docs, uses `doc-editor` for remediation |
| `/update-readme` | Runs `slop-detector` on README, applies `doc-generator` principles |
| `/prepare-pr` (`/pr`) | Verifies PR descriptions with `slop-detector` principles |

### Other Integrations

- **imbue:proof-of-work**:
  Evidence-based verification methodology (used by `doc-verifier`)
- **conserve:bloat-detector**: Token and content optimization
- **pensive:review skills**: Code review integration

## Stewardship

Ways to leave this plugin better than you found it:

- Slop detection patterns are an opportunity to add
  real before/after examples showing how each pattern
  was caught and rewritten
- Style learner templates could include sample style
  profiles for common writing contexts (technical docs,
  tutorials, API references)
- The doc-generator skill would benefit from documenting
  which input formats produce the best output quality
- Tutorial generation could include a troubleshooting
  section for common VHS/Playwright recording failures

See [STEWARDSHIP.md](../../STEWARDSHIP.md) for the full
stewardship principles guiding this project.

## License

MIT
