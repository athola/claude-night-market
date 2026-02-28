# Phase 4: Knowledge Queue Promotion Check

Check the memory-palace research queue for items needing evaluation.

## Step 1: Scan Queue for Pending Items

```bash
ls -lt plugins/memory-palace/docs/knowledge-corpus/queue/*.md 2>/dev/null | head -20
```

Check for `webfetch-*.md`, `websearch-*.md`, and files with `status: pending_review`.

## Step 2: Report Queue Status

Display pending items with age, topic, and priority in a table format.

## Step 3: Prompt for Evaluation

For each pending item older than 3 days, display summary and request decision: Promote, Archive, Defer, or Skip.

## Step 4: Execute Promotions

Move promoted items from queue to corpus, update frontmatter status, and rename to permanent filenames.

## Step 5: Track Decisions

Create TodoWrite items for each promotion decision. Use `--skip-queue` to skip.
