# Embedding Upgrade Guide

Add semantic search capabilities to Memory Palace for improved knowledge retrieval.

## Prerequisites

- Memory Palace plugin installed
- Python environment with uv
- (Optional) `sentence-transformers` for high-quality embeddings

## Objectives

By the end of this tutorial, you'll:

- Build embedding indexes for your corpus
- Toggle between embedding providers
- Benchmark retrieval quality
- Configure production settings

## Step 1: Choose an Embedding Provider

Memory Palace supports multiple providers:

| Provider | Quality | Dependencies | Use Case |
|----------|---------|--------------|----------|
| `hash` | Basic | None | CI, constrained environments |
| `local` | High | sentence-transformers | Production, quality focus |

## Step 2: Build Provider Slices

Navigate to the plugin directory:

```bash
cd plugins/memory-palace
```

### Build Hash Embeddings (No Dependencies)

```bash
uv run python scripts/build_embeddings.py --provider hash
```

This creates deterministic 16-dimensional vectors using hashing.

### Build Local Embeddings (High Quality)

First, install sentence-transformers:

```bash
uv pip install sentence-transformers
```

Then build:

```bash
uv run python scripts/build_embeddings.py --provider local
```

This creates 384-dimensional vectors using a local transformer model.

## Step 3: Verify the Build

Check the generated index:

```bash
cat data/indexes/embeddings.yaml
```

Expected structure:

```yaml
providers:
  hash:
    embeddings: {...}
    vector_dimension: 16
  local:
    embeddings: {...}
    vector_dimension: 384
metadata:
  default_provider: hash
```

Both providers are stored, so you can switch without rebuilding.

## Step 4: Toggle at Runtime

Set the provider via environment variable:

```bash
# Use hash embeddings
export MEMORY_PALACE_EMBEDDINGS_PROVIDER=hash

# Use local embeddings
export MEMORY_PALACE_EMBEDDINGS_PROVIDER=local
```

The hooks automatically use the environment variable.

## Step 5: Benchmark Quality

Run retrieval benchmarks:

```bash
uv run python scripts/build_embeddings.py \
  --provider local \
  --benchmark fixtures/semantic_queries.json \
  --benchmark-top-k 3 \
  --benchmark-only
```

The benchmark file should contain test queries:

```json
{
  "queries": [
    {
      "query": "async context managers in Python",
      "expected": ["async-patterns.md", "context-managers.md"]
    }
  ]
}
```

## Step 6: Using in Code

The `CacheLookup` class handles provider selection:

```python
from memory_palace.cache_lookup import CacheLookup

lookup = CacheLookup(
    corpus_dir="plugins/memory-palace/docs/knowledge-corpus",
    index_dir="plugins/memory-palace/data/indexes",
    embedding_provider="env",  # Reads from environment
)

# Semantic search
results = lookup.search("gradient descent", mode="embeddings")
```

## Fallback Strategy

If `sentence-transformers` is missing:

1. System automatically falls back to hash provider
2. CI environments always have a working provider
3. Set `MEMORY_PALACE_EMBEDDINGS_PROVIDER=hash` to guarantee fallback

## Adding Custom Providers

Extend with additional providers:

```python
# In your custom builder
def build_custom_embeddings(corpus):
    # Call external API
    embeddings = external_api.embed(corpus)
    return embeddings

# Builder preserves existing providers
uv run python scripts/build_embeddings.py \
  --provider custom \
  --custom-builder my_builder.py
```

## Performance Considerations

| Provider | Memory | Latency | Accuracy |
|----------|--------|---------|----------|
| hash | ~1MB | <10ms | ~60% |
| local | ~500MB | ~100ms | ~90% |

For production:
- Use `local` for quality-critical retrieval
- Use `hash` for quick lookups and CI

## Troubleshooting

### sentence-transformers installation fails

```bash
# Try with specific version
uv pip install sentence-transformers==2.2.2
```

### Embeddings not updating

```bash
# Force rebuild
rm data/indexes/embeddings.yaml
uv run python scripts/build_embeddings.py --provider local
```

### Provider not found

validate environment variable is set correctly:
```bash
echo $MEMORY_PALACE_EMBEDDINGS_PROVIDER
```

## Verification

Confirm semantic search works:

```bash
# In Python
from memory_palace.cache_lookup import CacheLookup

lookup = CacheLookup(
    corpus_dir="docs/knowledge-corpus",
    index_dir="data/indexes",
    embedding_provider="local"
)

results = lookup.search("your test query", mode="embeddings")
print(results)
```

## Next Steps

- [Memory Palace Curation](memory-palace-curation.md) for intake workflow
- [Cache Modes](cache-modes.md) for retrieval configuration

<div class="achievement-unlock" data-achievement="embedding-upgrade-complete">
Achievement Unlocked: Semantic Scholar
</div>
