---
name: warn-slop-in-markdown
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.(md|markdown|mdx)$
  - field: new_text
    operator: regex_match
    pattern: '—|\s--\s|\w\s\+\s\w|;\s+(?:it|they|this|that|these|those|we|you|there)\s|(?:It''s|It is|This is|That''s|That is|These are|Those are)\s+[\w\s]+?,\s+not\b|\w,\s+not\s+(?:just\s+|a\s+|an\s+|the\s+)?\w+[.!?]|[“”‘’]|,\s+not\s+just\s+\w|(?i:cannot\s+be\s+over(?:stated|emphasi[sz]ed|estimated)|not\s+to\s+be\s+(?:underestimated|overlooked|understated)|it\s+goes\s+without\s+saying|needless\s+to\s+say|no\s+small\s+(?:feat|task|thing|matter))|(?i:not\s+un(?:common|like|usual|important|reasonable|clear)|never\s+fails?\s+to\b)'
---

**AI slop pattern in markdown you are writing.**

One of these matched the text being written:

| Pattern | Rewrite as |
|---------|-----------|
| Em dash `—` | A colon, a period, or parentheses |
| Spaced double dash ` -- ` | Same. `--` is a shell end-of-options marker, not punctuation |
| `+` joining words in prose | "and", or rewrite the sentence |
| `;` splicing two clauses | Two sentences, or "and" / "but" / "so" |
| "X, not Y" and ", not just Y" | State X. Delete the negated half |
| Smart quotes `“ ” ‘ ’` | Straight quotes `"` `'` |
| "cannot be overstated", "needless to say", "no small feat" | Delete. State the consequence if there is one |
| "not uncommon", "never fails to" | The positive word: "common", "always" |

The last two rows are the negative-tense tells the scorer calls
high confidence. A negation that carries a fact ("the hook cannot reach
the registry") is deliberately unmatched.

The semicolon is the one to restructure rather than swap. A splice is
usually an em dash the author already talked themselves out of, and the
sentence reads better split. Keep the semicolon only in a list whose
items carry internal commas.

**Locate every finding, including the categories this rule does not
carry:**

```bash
uv run --with pyyaml python scripts/slop_score.py --audit <files>
```

That reports negative-tense reliance, over-explained fixes, spatial
copula, participial tails and the rest, each with a file and a line.
This rule holds only the cheap half, because hooks run on the system
Python without pyyaml and cannot load the pattern data.

Rewrite guidance for every category: `.claude/rules/slop-scan-for-docs.md`.

**Why this rule exists:**

The catalog's `require-slop-scan-for-docs` fires on a prompt that
sounds like documentation work. Slop arriving through an edit made for
some other reason was invisible until CI or a manual sweep, which is
late: by then it is in a diff someone is reviewing.

This warns and never blocks. Several of these are judgment calls, and
the house rule is that a person decides those.
