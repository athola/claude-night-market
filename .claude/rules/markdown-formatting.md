**Format markdown prose for readable diffs!**

When writing or editing markdown documentation, follow these
formatting rules to keep git diffs clean and reviewable:

**Line wrapping (prose text blocks only):**
- Wrap at 80 characters per line
- Prefer breaking at sentence boundaries (after . ! ?)
- Then at clause boundaries (after , ; :)
- Then before conjunctions (and, but, or)
- Then at word boundaries as a fallback
- Never break inside inline code, links, or URLs

**Do NOT wrap:**
- Tables, code blocks, headings, frontmatter, HTML, link
  definitions, image references

**Structural rules:**
- Blank line before AND after every heading
- ATX headings only (`# Heading`, never setext underlines)
- Blank line before every list (ordered or unordered)
- Reference-style links when inline links push past 80 chars

**Full reference:** `Skill(leyline:markdown-formatting)` and
its `wrapping-rules` module contain the complete algorithm
with examples.
