# API Patterns

This module covers how to apply progressive-loading when a skill
analyzes, designs, or reviews a public API surface. The driving
question is which slices of API knowledge to load on demand:
versioning rules, error envelopes, pagination, authentication,
or surface inventory. Loading all of them at once wastes tokens
when only one slice applies to the current task.

## When This Module Applies

Load this module when the active task involves any of:

- Reviewing a REST, GraphQL, gRPC, or library API surface.
- Designing a new endpoint or public function signature.
- Auditing API consistency across an existing codebase.
- Generating client code, OpenAPI specs, or SDK bindings.

If the task is general code review with no API focus, prefer
`api-review.md` for the audit workflow itself. This module is
about how to chunk API content for progressive loading, not how
to perform the review.

## Slice the API Surface First

Before loading deep API knowledge, classify the surface in one
pass. The classification drives the next module load.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ApiSlice:
    style: str        # "rest", "graphql", "grpc", "library"
    transport: str    # "http", "tcp", "in-process"
    auth: str         # "none", "bearer", "oauth2", "mtls"
    versioned: bool

def classify(spec_path: Path) -> ApiSlice:
    text = spec_path.read_text(encoding="utf-8").lower()
    style = "rest"
    if "type query" in text or "schema {" in text:
        style = "graphql"
    elif "service " in text and "rpc " in text:
        style = "grpc"
    auth = "bearer" if "authorization: bearer" in text else "none"
    return ApiSlice(
        style=style,
        transport="http" if style != "grpc" else "tcp",
        auth=auth,
        versioned="version" in text or "/v1/" in text,
    )
```

The output of `classify` selects which detail modules to load.
A REST API with bearer auth needs the REST conventions module
and the OAuth/bearer module, not the gRPC streaming module.

## Loading Map

A typical API skill keeps these modules separate so each loads
only when relevant. The frontmatter `triggers` declared in
`selection-strategies.md` controls activation.

| Slice | Load Trigger | Token Estimate |
|-------|--------------|----------------|
| REST conventions | `style == "rest"` | 600 |
| GraphQL schema rules | `style == "graphql"` | 700 |
| gRPC service patterns | `style == "grpc"` | 500 |
| Pagination strategies | `paginated` field present | 400 |
| Auth: bearer/OAuth2 | `auth in ("bearer","oauth2")` | 500 |
| Versioning policy | `versioned == True` | 300 |
| Error envelopes | always (small) | 200 |

The error envelope module is small and always loaded because
every API has errors. Everything else is gated.

## Concrete Example: Bearer-Auth REST Endpoint

When the classifier returns
`ApiSlice(style="rest", auth="bearer", versioned=True)`, the
hub loads three modules and skips the rest.

```yaml
# hub frontmatter (illustrative; module names are placeholders
# the consuming skill author would supply for their own domain)
modules:
  - modules/<rest-conventions>.md
  - modules/<auth-bearer>.md
  - modules/<versioning-policy>.md
  - modules/<error-envelopes>.md
```

For a GraphQL API with no auth, the load list shrinks to two
modules plus the always-loaded error envelopes. The token saved
by skipping REST and auth content is redirected to the actual
review work.

## Pitfalls

1. **Loading by file extension alone**: A `.proto` file might be
   a vendored copy in a REST project. Read the file content for
   classification, not just the suffix.
2. **Treating "API" as one module**: Authors who put REST,
   GraphQL, gRPC, and SDK guidance in one file force every API
   review to load all of it. Split by style first.
3. **Skipping the error module**: Error contracts are the most
   common review finding. Keep error guidance always loaded so
   reviewers see it without a second pass.
4. **Hard-coding versioning into core**: Some APIs are
   intentionally unversioned (internal RPCs, single-tenant
   tools). Gate versioning content on the `versioned` flag.
5. **Re-classifying on every turn**: Cache the classification per
   spec file. A REST API does not become a gRPC API mid-session.

## Cross-Reference

See `api-review.md` for the review workflow that consumes these
loading slices, and the parent `SKILL.md` for the hub-and-spoke
contract these slices fit into.
