# Markdown Formatting Enhancement - Project Brief

**Date**: 2026-03-04
**Status**: Approved

## Problem Statement

**Who**: Developers and AI agents reviewing documentation PRs
**What**: Long single-line paragraphs in markdown produce unreadable
git diffs. A single word change in a 300-character paragraph
highlights the entire line, making review painful on desktop and
nearly impossible on mobile.
**Where**: All markdown across the claude-night-market plugin
ecosystem (docs/, book/, wiki/, plugin READMEs, skill files)
**When**: Every PR that touches documentation content
**Why**: Reviewers cannot identify what actually changed.
Mobile GitHub requires horizontal scrolling for long lines.
**Current State**: No line length rules exist for markdown.
The scribe and sanctum plugins generate documentation without
wrapping. Paragraphs regularly exceed 200+ characters per line.

## Goals

1. All doc-generation skills produce text blocks wrapped at 80
   characters using hybrid wrapping (prefer sentence/clause
   boundaries)
2. Enforce consistent markdown formatting conventions across
   all documentation plugins
3. Make documentation diffs reviewable on mobile devices
4. Establish a shared "markdown style module" that all plugins
   reference for formatting rules

## Constraints

### Technical
- Must not alter rendered markdown output (newlines in paragraphs
  render as spaces)
- Must exempt non-prose content: tables, code blocks, headings,
  URLs/links, frontmatter, HTML blocks, YAML blocks
- System Python is 3.9.6 (hooks must remain compatible)
- No external tool dependencies (skills generate markdown directly)

### Integration
- Affects 4+ plugins: scribe, sanctum, attune, spec-kit
- Must integrate with existing Write/Edit tool usage
- Must not conflict with directory-style-rules (paragraph sentence
  limits, section length limits)

### Success Criteria
- [ ] All doc-generation skills include formatting instructions
- [ ] Prose text blocks wrap at 80 chars with semantic awareness
- [ ] Tables, code blocks, headings, links remain unwrapped
- [ ] Blank lines enforced around headings and before lists
- [ ] ATX headings enforced (no setext)
- [ ] Reference-style links recommended for long URLs
- [ ] No rendered output changes after reformatting
- [ ] Diffs for documentation changes show only changed lines

## Approach Comparison

| Criterion | Pure Hard Wrap | Semantic Breaks | Hybrid (selected) |
|-----------|---------------|-----------------|---------------------|
| Diff Quality | Good | Excellent | Very Good |
| Familiarity | High | Low | High |
| Implementation | Simple | Complex | Medium |
| Rewrap Cascade | Frequent | None | Rare |
| Consistency | Deterministic | Variable | Mostly Deterministic |

## Selected Approach: Hybrid Hard Wrap

Wrap prose text at 80 characters but prefer breaking at sentence
boundaries (after `.`, `!`, `?`), clause boundaries (after `,`,
`;`, `:`) and before conjunctions. When a sentence fits within
80 characters, keep it on one line. When a sentence exceeds 80
characters, break at the nearest clause boundary before the limit.

### Additional Formatting Rules

1. **Blank lines around headings**: Require a blank line before
   and after every heading (markdownlint MD022)
2. **ATX headings only**: Enforce `#` style, no setext underlines
   (markdownlint MD003)
3. **Blank line before lists**: Require a blank line before
   starting any list (markdownlint MD032)
4. **Reference-style links for long URLs**: When inline link
   syntax would push a line beyond 80 characters, move the URL
   to a reference definition at the bottom of the section

### Trade-offs Accepted

- **Slightly more complex wrapping logic**: Mitigated by clear
  specification and examples in a shared module
- **Not perfect diff isolation** (semantic breaks would be
  better): Mitigated by sentence-boundary preference reducing
  cascades to rare occurrences

### Research Sources

- [Semantic Line Breaks Specification](https://sembr.org)
- [Robert Lin: Semantic Line Breaks](https://bobheadxi.dev/semantic-line-breaks/)
- [4+1 Wrapping Styles Comparison](https://mtsknn.fi/blog/4-1-wrapping-styles-for-markdown-prose-and-code-comments/)
- [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)
- [markdownlint MD013](https://github.com/DavidAnson/markdownlint/blob/main/doc/md013.md)
- [Flowmark](https://github.com/jlevy/flowmark) (2025, semantic auto-formatter)
- [md-fixup](https://brettterpstra.com/2026/01/07/markdown-fixup-an-opinionated-markdown-linter/) (2026, normalization tool)
- [Fern Docs Linting Guide 2026](https://beta.buildwithfern.com/post/docs-linting-guide)

## Next Steps

1. `/attune:specify` - Create specification with wrapping rules,
   exemption list, and per-plugin integration points
2. `/attune:blueprint` - Plan implementation across all plugins
3. Execute changes to skills, modules, and rules
