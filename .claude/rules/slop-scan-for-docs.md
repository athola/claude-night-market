**Run slop detection after writing documentation!**

When creating or updating markdown documentation files (tutorials, guides, READMEs, book content), you MUST run `Skill(scribe:slop-detector)` on each modified file before reporting completion.

**Automatic checks after writing .md files:**
1. Verify prose lines wrap at 80 chars (see
   `.claude/rules/markdown-formatting.md`)
2. Count em dashes: `grep -o '—' file.md | wc -l`
   (target: 0-2 per 1000 words)
3. Scan for tier 1 slop: "structured", "comprehensive",
   "actionable", "seamless", "robust"
4. Check for participial tail-loading: sentences ending
   with ", [verb]-ing ..."
5. Run full `Skill(scribe:slop-detector)` if file > 100 words

**Fix before committing:**
- Replace em dashes with colons, periods, commas, or parentheses
- Replace "structured" with nothing (usually filler) or a specific word
- Replace "actionable" with "specific" or "concrete"
- Replace "comprehensive" with "thorough" or "complete"
- Break up participial phrases into separate sentences
- Replace ASCII arrows (`->`, `→`) used as prose connectors
  with "to", "into", or "produces" (arrows are fine in code
  and type signatures)
- Replace `+` used as a prose conjunction with "and" or
  rewrite the sentence (fine in code, math, and labels)
