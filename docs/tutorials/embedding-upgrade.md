# Optional Embedding Upgrade & Toggle

The cache interceptor can layer semantic vectors on top of the keyword/query indexes. This tutorial walks through building multiple provider slices, toggling them at runtime, and validating recall with the new benchmark helpers.

## Build provider slices

```bash
cd plugins/memory-palace
# Deterministic 16-dim hashed vectors (no external deps)
uv run python scripts/build_embeddings.py --provider hash

# Higher-recall local vectors (requires sentence-transformers)
uv run python scripts/build_embeddings.py --provider local

# Run benchmarks without rebuilding
uv run python scripts/build_embeddings.py \
  --provider local \
  --benchmark fixtures/semantic_queries.json \
  --benchmark-top-k 3 \
  --benchmark-only
```

Each invocation writes under `data/indexes/embeddings.yaml` in its own provider block so switching providers never wipes the fallback hashes.

## Runtime toggle

Set the environment variable that operators or CI can flip:

```bash
export MEMORY_PALACE_EMBEDDINGS_PROVIDER=hash  # or local
```

Then use the env-aware constructor (hooks already pass this through):

```python
lookup = CacheLookup(
    corpus_dir="plugins/memory-palace/docs/knowledge-corpus",
    index_dir="plugins/memory-palace/data/indexes",
    embedding_provider="env",
)
results = lookup.search("gradient descent", mode="embeddings")
```

`CacheLookup` resolves the env var once, so you can override per process or per test run without editing YAML config.

## Inspecting `embeddings.yaml`

The file stores provider metadata so you can confirm what was built:

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

Feel free to add additional providers (e.g., remote APIs) — the builder will preserve everything in-place.

## Fallback strategy

If `sentence-transformers` is missing, the system automatically hashes to deterministic 16-d vectors, so CI and constrained environments always have a provider they can flip on. Use `MEMORY_PALACE_EMBEDDINGS_PROVIDER=hash` to guarantee that behavior.
