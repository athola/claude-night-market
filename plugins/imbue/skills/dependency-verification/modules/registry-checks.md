# Registry Checks

Per-ecosystem endpoints for confirming a package exists, and the
rules the guard hook applies.

## Endpoints

| Ecosystem | URL | Exists | Absent |
|-----------|-----|--------|--------|
| PyPI | `https://pypi.org/pypi/{name}/json` | HTTP 200 | HTTP 404 |
| npm | `https://registry.npmjs.org/{name}` | HTTP 200 | HTTP 404 |
| crates.io | `https://crates.io/api/v1/crates/{name}` | HTTP 200 | HTTP 404 |

A manual check from the shell:

```bash
# PyPI: prints the status code; 200 exists, 404 does not.
curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/requests/json
```

## Decision Rules

The hook classifies each install target into one of three states:

- **exists** (registry returns 200): pass.
- **nonexistent** (registry returns 404): likely hallucination.
  Block when `VOW_SHADOW_MODE=0`, warn otherwise.
- **unverified** (timeout, rate limit, offline, non-404 error):
  warn only, never block. The guard does not fail closed on a
  network problem.

Known-popular packages short-circuit before any network call, so a
common install such as `pip install requests` never makes a request
to the registry. Only names absent from the bundled popular set are
looked up.

## Timeout and Offline Behavior

The network lookup uses a 1.5 second per-package timeout. Set
`IMBUE_PKG_REGISTRY_CHECK=0` to skip network lookups entirely and
rely on the offline typosquat signal (edit distance against the
known-popular set). This is the right setting in sandboxed or
air-gapped environments where the registry is unreachable.

## Typosquat Distance

A name not in the known-popular set but within Levenshtein distance
1 or 2 of a popular package is flagged as a typosquat suspect. The
distance threshold balances catching real typos (`reqeusts`,
`numpi`) against false positives on legitimately short names. The
known-popular set is the most-impersonated packages per ecosystem
and is meant to be extended as new impersonation targets emerge.
