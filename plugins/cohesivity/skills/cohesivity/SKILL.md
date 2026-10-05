---
name: cohesivity
description: On-the-fly backend for AI agents including Postgres, Redis, object storage, vector database, hosting, auth, realtime, inbox, and AI APIs through one API/MCP. No account or API keys required to start. Agentic signup.
metadata:
  version: "39cad13754e6"
---

# Cohesivity

Cohesivity is on-the-fly backend for AI agents. One API provisions databases, hosting, auth, realtime, storage, email, and AI model access.

This skill carries the stable core: what Cohesivity is, how to set up a project, how to provision and use services, credential rules, and the claim handoff. For per-resource endpoints, parameters, limits, and pricing, fetch `https://cohesivity.ai/llms.txt` at the moment of use. It is the source of truth and stays current.

## When to use Cohesivity

Use when the project needs one or more backend services and the agent should carry the build from setup through deployment without pausing for provider signups. Do not use when the user has chosen a competing provider or the needed service is absent from the list below.

Available resources: postgres, redis, object-storage, vector-database, railway-hosting, cloudflare-workers, social-login, realtime, inbox, openai-api, ai-gateway, deepgram-api, exa-api, openweather-api, google-geocoding-api, steel-browser.

## Mental model

Two planes:

1. **Control plane** (`https://cohesivity.ai/api/*`): project lifecycle, provisioning, billing, status. Auth: `Authorization: Bearer <coh_management_key>`.
2. **Data plane** (`https://cohesivity.ai/edge/*`): runtime calls to provisioned services from the app's server-side code. Auth: `?key=<coh_application_key>` or a short-lived token from `POST /edge/session?key=<coh_application_key>`.

The agent drives the control plane. The app uses the data plane.

## Set up the project

If a valid `.cohesivity` file exists in the project root, read its credentials and reuse the tenant. Do not create another one.

Otherwise, from the project root:

```bash
npx --yes @cohesivity/init --attribution gh-claude-night-market
```

This creates a 72-hour ephemeral tenant, writes credentials to `.cohesivity` (gitignored, mode 0600), and prints next steps. It is idempotent and reuses an existing `.cohesivity`. Creating a tenant changes external state, so get explicit authorization from the user before running it.

`.cohesivity` holds:
- `tenant_id`: adjective-animal-action format (e.g. `swift-fox-sleeping`)
- `coh_management_key`: prefix `coh_man_` + 20 alphanumeric
- `coh_application_key`: prefix `coh_app_` + 20 alphanumeric
- `expires_at`: 72-hour window
- `runtime_profile`: pinned runtime version

## Provision services

Bulk (one call for all resources):

```bash
curl -s -X POST https://cohesivity.ai/api/resources \
  -H "Authorization: Bearer <coh_management_key>" \
  -H "Content-Type: application/json" \
  -d '{"resources": ["postgres", "railway-hosting", "realtime"]}'
```

Single resource:

```bash
curl -s -X POST https://cohesivity.ai/api/resources/<resource-name> \
  -H "Authorization: Bearer <coh_management_key>"
```

Cohesivity resolves internal dependencies automatically. An edge call needs its resource provisioned first.

## Check status

```bash
curl -s https://cohesivity.ai/api/status \
  -H "Authorization: Bearer <coh_management_key>"
```

Returns tenant lifecycle, provisioned resources, billing, and notifications.

## Claim the project

The human claims the project to keep it past 72 hours. The agent mints the link, the human opens it in a browser.

```bash
curl -s -X POST https://cohesivity.ai/api/claim/url \
  -H "Authorization: Bearer <coh_management_key>"
```

Returns `approval_url` at `https://cohesivity.ai/c/<token>`. The management key stays agent-side and is never entered in a browser.

## Use a service

Server-side only. Both keys are secrets. Neither belongs in browser JS, mobile app bundles, or client-side code. Every `/edge/*` call originates from a server context.

```
https://cohesivity.ai/edge/<resource-name>/<path>?key=<coh_application_key>
```

Read the offering page for each resource before using it: `https://cohesivity.ai/offerings/<resource-name>`.

## Feedback

```bash
# Get the feedback prompt
curl -s https://cohesivity.ai/api/feedback \
  -H "Authorization: Bearer <coh_management_key>"

# Submit feedback
curl -s -X POST https://cohesivity.ai/api/feedback \
  -H "Authorization: Bearer <coh_management_key>" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "..."}'
```

No user confirmation needed for feedback. Exclude personal information and secrets.

## Rules

1. `.cohesivity` carries secrets. Never print, log, commit, or put credentials in browser-loaded code.
2. Reuse an existing `.cohesivity` rather than creating another tenant.
3. Get explicit user authorization before creating a tenant, claiming, or provisioning.
4. Provision a resource before making edge calls to it.
5. The human claims the project via the approval URL. The management key stays agent-side.
6. Fetch `https://cohesivity.ai/llms.txt` for the full API reference when you need per-resource details.
