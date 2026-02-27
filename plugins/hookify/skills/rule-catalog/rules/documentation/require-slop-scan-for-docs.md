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

When creating, updating, or rewriting documentation, run `Skill(scribe:slop-detector)` on all modified markdown files before considering the work complete.

**Common AI tells to watch for:**
- Em dash overuse (>2 per 1000 words is elevated, >6 is a strong AI signal)
- "structured", "actionable", "comprehensive", "seamless" and other tier 1 slop words
- Participial phrase tail-loading ("...enabling researchers to analyze data")
- Uniform sentence lengths (human writing varies, AI stays at 15-25 words)
- Hedging patterns ("It's important to note", "From a broader perspective")

**Required workflow:**
1. Write/edit the documentation
2. Run `Skill(scribe:slop-detector)` on each modified .md file
3. Fix any issues with score > 2.0
4. Verify em dash count is within human range (0-2 per 1000 words)

**Quick checks:**
```bash
# Count em dashes in a file
grep -o '—' file.md | wc -l

# Count words
wc -w < file.md
```

**Why this rule exists:**
- AI-generated documentation erodes reader trust
- Em dashes, "structured", and "actionable" are the most common tells
- The slop detector exists but is only invoked manually today
- This rule closes the gap between writing docs and quality-checking them
