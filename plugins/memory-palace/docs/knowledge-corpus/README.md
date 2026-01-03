# Knowledge Corpus

External resources stored in memory palace format to inform plugin development and skill design.

## Purpose

This corpus captures valuable insights from articles, blog posts, research papers, and other external sources. By storing them in memory palace format, we:

1. **Preserve context** - Maintain structured notes on important concepts
2. **Enable cross-reference** - Link external insights to internal skills
3. **Build patterns** - Identify recurring themes across sources
4. **Inform development** - Apply learned patterns to plugin improvements

## Structure

Each entry follows the memory palace schema:
- **Palace**: Thematic grouping (e.g., "Learning Techniques", "AI Patterns")
- **Location**: Specific source or concept cluster
- **Concept**: Key insight with sensory encoding
- **Associations**: Links to related concepts and skills

## Adding New Entries

When adding external resources:
1. Extract key concepts using the "Franklin Protocol"
2. Create structured notes with explicit associations
3. Link to relevant internal skills and patterns
4. Tag with maturity level (seedling → evergreen)

## Cache Interception Catalog

The cache interceptor requires a large curated base so governance hooks can answer requests without hitting the network. We maintain a YAML catalog (`cache_intercept_catalog.yaml`) with **55** vetted scenarios that cover cache governance patterns, rollback readiness, and curator prompts.

- **Location**: `plugins/memory-palace/docs/knowledge-corpus/cache_intercept_catalog.yaml`
- **Metadata**: Each entry includes slug, title, tags, keywords, summary, and canonical file path.
- **Quality bar**: Keep the `metadata.cache_intercept.curated_count` at **≥50** by adding scenarios in batches of five or more with reviewer sign-off.
- **Refresh workflow**:
  1. Update the YAML catalog with the new entries.
  2. Run `uv run python plugins/memory-palace/scripts/seed_corpus.py` to merge curated entries via `seed_cache_catalog`.
  3. Verify `plugins/memory-palace/data/indexes/keyword-index.yaml` reflects the new `cache_intercept` metadata and entry slugs.

## Index

### Learning & Meta-Skills
- [Franklin Protocol - Learning Algorithms](./franklin-protocol-learning.md)

### Code Quality & Maintenance
- [Codebase Bloat Detection - Tools and Techniques](./codebase-bloat-detection.md)
