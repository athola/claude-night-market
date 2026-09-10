---
name: require-slop-scan-for-docs
enabled: true
event: prompt
action: warn
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (writ|creat|updat|generat|rewrite|overhaul|rewrit|draft).*(tutorial|documentation|readme|docs|guide|changelog|book)
---

**Run AI slop detection on documentation changes!**

Before you call documentation work complete, locate every finding in
each modified markdown file with one command:

```bash
uv run --with pyyaml python scripts/slop_score.py --audit <files>
```

It reports every category with a file and a line, the opt-in and
low-confidence ones included, and the per-document negation-density
reading. Rewrite guidance for each category is in
`.claude/rules/slop-scan-for-docs.md`. `Skill(scribe:slop-detector)`
carries the full method.

**The checklist the audit covers:**

| Tell | Rewrite as |
|------|-----------|
| Em dash, or a spaced `--` used as one | A colon, a period, or parentheses. Target zero in new prose |
| Plus-sign for "and" in prose: "hooks + skills" | "hooks and skills" |
| Semicolon splicing two clauses | Two sentences, or "and" / "but" / "so". Restructure rather than swap in a dash |
| Contrastive negation: "It's not X, it's Y", "X, not Y", ", not just Y" | State the affirmed half. Delete the negated one |
| Over-explained fixes: "in order to", "this ensures that", "the reason for this is" | State the defect and the change, then stop |
| Negative framing: "not uncommon", "cannot be overstated", "does not support X" | The positive form. A negation that carries a fact stays |
| Negation density over 35% of sentences | Reread for places where saying what the thing does is shorter |
| Tier 1 words: "structured", "actionable", "comprehensive", "seamless" | Delete, or the specific word |
| Participial tail: "..., enabling researchers to analyze data" | A new sentence with the consequence |
| Spatial copula: "lives in", "sits at", "serves as", "rooted in" | "is", "has", "uses" |
| Throat-clearing openers, three-fragment bursts, significance clusters | Delete. Start at the substantive content |
| Smart quotes outside code | Straight quotes |

**Required workflow:**

1. Write or edit the documentation.
2. Run the audit command on each modified markdown file.
3. Fix every high-confidence finding. Judge each `(low)` or `(medium)`
   one by hand.
4. Run the audit again and confirm the high-confidence count is zero.

The `warn-slop-in-markdown` rule fires on the write itself for the
cheap half of this table. A pre-commit ratchet and the PR slop check
fail a file that scores worse than its committed version.

**Why this rule exists:**

- AI-generated documentation erodes reader trust.
- Em dashes, "structured", and "actionable" are the most common tells.
- The operator used to type this whole checklist as a prompt every
  time. The audit command and this table replace that prompt.
