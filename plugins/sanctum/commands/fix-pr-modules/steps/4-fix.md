# Step 4: Fix (Apply Changes)

> **Navigation**: [← Step 3: Plan](3-plan.md) | [Main Workflow](../workflow-steps.md) | [Step 5: Validate →](5-validate.md)

**Purpose**: Apply code changes systematically.

**Skip when**: Just need validation (already made changes manually).

## 4.1 Apply Fixes Systematically

```bash
# For each approved fix:
1. Read code context (±20 lines)
2. Apply fix with Edit tool
3. Verify no new issues introduced
4. Mark as completed
```

## 4.2 Commit Changes

- **Single**: "Address PR review feedback"
- **Separate**: One commit per fix category
- **Manual**: Stage changes, user commits

### Commit message hygiene (MANDATORY)

Load `../../shared/output-hygiene.md` before writing the message.
Inline fallback if that module is absent:

- **Contract A (characters)**: no `"+"` used as a conjunction (use
  `and`; keep `+` in versions and code), no em-dash `—`, no prose
  `--`, no arrows `->` / `→` as connectors, no smart quotes
  `“ ” ‘ ’`. Replace with plain punctuation.
- **Contract B (subject matter)**: if a fix removed AI slop, describe
  the change by its reader-facing effect. Name neither the AI origin
  nor the specific marker removed. Do NOT write `remove AI slop`,
  `de-slop`, `AI-generated content`, `AI phrasing`, `replace
  em-dashes`, or `remove smart quotes`. For example `docs: clarify
  wording`, not `style: replace em-dashes with colons`.

**Step 4 Output**: Applied fixes, commits created

---

> **Next**: [Step 5: Validate (Test & Verify) →](5-validate.md)
