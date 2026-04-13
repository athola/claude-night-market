---
module: sample-intake
category: voice-extraction
dependencies: [Bash, Read, Write]
estimated_tokens: 600
---

# Sample Intake Module

Collect and organize writing samples for voice extraction.

## Directory Mode

When user provides a path to a directory of writing samples:

```bash
PROFILE_NAME="$1"
SAMPLE_DIR="$2"
PROFILE_DIR="$HOME/.claude/voice-profiles/$PROFILE_NAME"

mkdir -p "$PROFILE_DIR/samples"
mkdir -p "$PROFILE_DIR/registers"
mkdir -p "$PROFILE_DIR/learning/snapshots"

# Copy and anonymize samples
counter=1
for f in "$SAMPLE_DIR"/*.{md,txt} 2>/dev/null; do
  [ -f "$f" ] || continue
  padded=$(printf "%02d" $counter)
  cp "$f" "$PROFILE_DIR/samples/sample-${padded}.md"
  counter=$((counter + 1))
done
```

## Interactive Mode

Prompt user to paste samples one at a time:

1. Present: "Paste writing sample (min 100 words). Type END on a new line when done."
2. Save to `samples/sample-{nn}.md`
3. Report word count
4. Ask: "Add another sample? (yes/done)"
5. Repeat until "done" or 20 samples reached

## Validation Rules

| Check | Threshold | Action |
|-------|-----------|--------|
| Sample count | >= 3 | Error if below |
| Total words | >= 500 | Error if below |
| Per-sample words | >= 100 | Warn, allow |
| Topic variety | 3+ distinct topics | Warn if all same |

## Manifest Creation

After intake, write `manifest.json`:

```json
{
  "profile_name": "NAME",
  "created": "YYYY-MM-DD",
  "samples": [
    {
      "id": "sample-01",
      "word_count": 450,
      "date_added": "YYYY-MM-DD",
      "original_filename": "anonymized"
    }
  ],
  "extraction": {
    "model": null,
    "date": null,
    "passes_completed": 0
  },
  "registers": ["default"],
  "learning": {
    "snapshot_count": 0,
    "accumulator_entries": 0,
    "last_learning_pass": null
  }
}
```

## Anonymization

Strip all context from samples before extraction:

- Remove filenames from headers
- Remove dates, URLs, proper nouns that identify source
- Label only as "Sample 01", "Sample 02", etc.
- Never tell the extractor what platform or context a sample is from

This forces the extraction to focus on structural and stylistic
patterns rather than anchoring on content or context.
