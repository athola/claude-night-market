---
module: hallucination-detection
category: detection
dependencies: [Grep, Read, Bash]
estimated_tokens: 700
---

# Hallucination Detection

**Hallucination is not slop: it is wrongness with confident
phrasing. Always P0.**

This module covers the class of AI defects where the
generated text *refers to something that does not exist*:
a function never defined, a library never published, a
config key never read, a cited URL that 404s. Slop
detectors that only score word density miss these
entirely, because each individual word is fine.

The 2025-26 cross-evaluation work (§12.1) is unambiguous:
GPT-5.x family fabricates more (invented identifiers,
made-up library APIs); Claude 4.x family omits more
(skipped match arms, missed error paths). Both produce
plausible-but-fake doc references. Calibrate the audit
weighting to the model that produced the artifact, but
always run the full check.

## Class 1: Phantom code references

Comments and docs that reference code that does not exist
in the repository.

### Patterns to scan

```
"see also `module_name::function`"
"as defined in `path/to/file.rs`"
"this calls into `helper_fn()`"
"the `FooConfig` struct"
"flag this with `--enable-bar`"
```

### Detection rule

For each backtick-quoted identifier or path in prose,
verify it actually exists:

```bash
# Identifiers
rg -c "\bfunction_name\b" --type-add 'src:*.{py,rs,ts,js,go}' --type src

# File paths
[ -f "path/to/file.rs" ] && echo "exists" || echo "MISSING"

# Module paths (language-dependent)
rg "^(pub )?(mod|fn|struct|enum) function_name" --type src
```

Findings format:
- `confidence: high` if the identifier appears in prose
  but `rg` finds zero matches in source.
- `confidence: medium` if the identifier exists but in a
  surprising location (suggests rename without doc update).

### Common phantom-reference patterns

- "deprecated in favor of `new_api`": verify `new_api`
  exists and is not itself deprecated.
- "see `tests/test_foo.py`": verify file exists.
- "the `--strict` flag": verify the CLI parses that flag.
- "the `MAX_RETRIES` constant": verify the constant is
  defined and exported.

## Class 2: Phantom external dependencies

Library imports and config keys that AI invented because
they sounded plausible.

### Patterns to scan

For Rust/Python/JS, every import or `use` statement should
resolve to a real published crate/package.

```bash
# Python: every import in source
rg "^(?:from|import)\s+\w+" --type py | sort -u

# Rust: every use statement
rg "^use\s+[a-z][a-z0-9_]+::" --type rust | sort -u

# Cross-reference with declared dependencies
diff <(extract-imports) <(extract-deps)
```

### "Slopsquatting": the security flank

Trend Micro's 2024-25 research documented adversaries
registering hallucinated package names that AI agents
suggested. A doc that recommends installing a non-existent
package is a vector for supply-chain attack the next time
that name *does* get registered.

Detection:
- Cross-reference every `pip install`, `cargo install`,
  `npm install`, `gem install` recommendation in docs
  against the relevant registry.
- Flag any package that does not currently resolve.
- Especially flag packages with names suspiciously close
  to popular ones (e.g. `requesst` for `requests`).

### Made-up identifiers (model-specific weighting)

Per 2025-26 research:

- **GPT-family-generated text**: weight toward verifying
  every method name, attribute name, lint name, config
  key actually exists.
- **Claude-family-generated text**: weight toward verifying
  every match arm and error variant is reachable, every
  edge case is handled.

A simple cross-reference grep catches most of these.

## Class 3: Dead URLs and broken citations

AI confidently cites docs URLs that 404 or arXiv papers
that do not exist.

### Detection

```bash
# Extract all URLs from docs
rg -o 'https?://[^\s\)]+' docs/ *.md

# Verify each (rate-limited, batch)
while read url; do
  status=$(curl -sI -o /dev/null -w '%{http_code}' "$url" --max-time 5)
  [ "$status" != "200" ] && echo "DEAD: $status $url"
done < urls.txt
```

### Special cases

- **arXiv citations**: verify the arXiv ID exists.
  `https://arxiv.org/abs/{ID}` should return 200.
- **GitHub references**: `github.com/user/repo` should
  resolve. `github.com/user/repo/blob/main/path` should
  also resolve at the named branch.
- **Internal docs**: relative links should point to files
  that exist at that path in the repo.

## Class 4: Phantom test/file references

Comments that reference test files, fixtures, or modules
that do not exist.

```python
# SLOP: references file that doesn't exist
# See tests/integration/test_full_flow.py for end-to-end coverage
```

If `tests/integration/test_full_flow.py` does not exist,
the comment is hallucinated. Either:
1. The test was removed and the comment was not updated.
2. The test was never written and the comment is invention.

Either way, the comment is a defect: it tells future
maintainers that coverage exists where it does not.

### Detection

```bash
# Pull every file path from comments
rg -o '(?:tests?/|src/|docs?/)[\w/.-]+\.\w+' --no-filename .

# Verify each path exists
while read path; do
  [ ! -e "$path" ] && echo "MISSING: $path"
done < referenced-paths.txt
```

## Class 5: Made-up configuration

Config keys, environment variables, or feature flags that
appear in docs but are never read by the code.

### Detection

For every config key mentioned in docs, verify the code
actually reads it:

```bash
# Pull config keys from docs (tune the regex per config format)
rg -o '`[A-Z][A-Z0-9_]+`' --no-filename docs/ *.md | sort -u > docs-keys.txt

# Pull keys actually read in code
rg -o 'env::var\("([A-Z_]+)"' src/ | sort -u > code-keys.txt
rg -o 'os.environ\["([A-Z_]+)"\]' src/ | sort -u >> code-keys.txt

# Diff
comm -23 docs-keys.txt code-keys.txt
# Lines in docs but not in code = phantom config keys
```

## Output format

Hallucination findings should follow the structured-finding
format with `severity: critical` (since the documentation
is actively wrong, not just bloated):

```
[FINDING N]
file:        docs/api.md
line:        47
category:    hallucination/phantom-identifier
severity:    critical
confidence:  high
evidence:    >    Use `Client.connect_with_timeout(...)` to ...
rationale:   `Client.connect_with_timeout` does not exist
             anywhere in the codebase. `Client.connect`
             accepts a timeout via the `Options` struct:
fix:         Replace with `Client.connect(opts)` and update
             the surrounding example accordingly.
```

## Integration

Hallucination detection runs *before* the cleanup workflow
(see `cleanup-workflow.md` Pass 2). Cleaning up text that
references phantoms means polishing prose that is wrong
about the world: fix the wrongness first, then polish.

A document with any critical-severity hallucination
finding must not pass review until the finding is resolved
or explicitly waived with rationale.
