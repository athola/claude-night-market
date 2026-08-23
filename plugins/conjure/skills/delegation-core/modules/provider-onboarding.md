---
name: provider-onboarding
description: Per-provider install and authentication steps, and the failure shapes each one produces when half-configured
parent_skill: conjure:delegation-core
category: delegation-framework
estimated_tokens: 700
---

# Getting Providers Answering

Delegation is on by default, so an unconfigured machine is not broken.
It costs one availability probe per provider and then does the work
locally.
This module is for turning that fallback into an answer.

## Start Here

```bash
make -C plugins/conjure delegate-doctor
```

The doctor reports three states per provider, and only the first two
are trustworthy.

| Column | Meaning |
|--------|---------|
| `INSTALLED: no` | The binary is absent. Install it, or ignore the provider |
| `AUTH: missing` | A variable is unset, a credential file is absent, or one states an expiry that has passed |
| `AUTH: ok` | A check confirmed credentials |
| `AUTH: unknown` | The CLI owns its credentials, holds a file, and states no expiry |

**`unknown` is not `ok`.** It means every cheap check came back
inconclusive, not that anything passed.
None of these checks spawns a provider CLI: they read the environment
and the credential files each CLI names in its own error messages.

The only way to resolve an `unknown` is to run one delegation and read
what comes back. Run it from `plugins/conjure`, substituting the
provider whose row you are resolving:

```bash
uv run python scripts/delegation_executor.py codex "Reply with exactly: pong"
```

`codex` is the honest example: its `auth.json` records a
`last_refresh` and no deadline, so a spent refresh token looks
identical to a working one until a call is made.

## Per-Provider Steps

| Provider | Binary | Authenticate with |
|----------|--------|-------------------|
| gemini | `gemini` | `export GEMINI_API_KEY=<key>` from AI Studio |
| qwen | `qwen` | `qwen` once interactively, or `--openai-api-key` with a key its endpoint accepts |
| minimax | `mmx` | `mmx auth login` |
| glm | `claude` | `export ZAI_API_KEY=<key>` from z.ai |
| muse | `muse` | `muse login`, or `export META_API_KEY=<key>` |
| codex | `codex` | `codex login` |
| opencode | `opencode` | `opencode auth login` |
| glimmer | `ollama` | No credentials. `ollama pull muse-glimmer:30b` |

`glm` runs the stock `claude` binary against Z.ai's
Anthropic-compatible endpoint, so it needs no separate CLI.
`glimmer` is local and needs no key, but it needs the model on disk:
`ollama list` showing nothing means the pull has not happened, and the
first delegation will sit downloading roughly 18GB.

## Failure Shapes Worth Recognizing

Each of these was observed on a real machine. They matter because none
of them looks like an authentication problem at a glance.

**A provider that exits 0 with an empty answer is unauthenticated.**
`qwen` with a rejected credential prints
`[API Error: 401 Incorrect API key provided]` and exits 0 with nothing
on stdout.
Verification reads `~/.qwen/oauth_creds.json` and its stated
`expiry_date`, so an expired qwen is skipped before it is spawned and
the trail reads `Credential ... expired <date>`.
A credential that is present, unexpired and still refused would get
past that and produce the empty answer, which the chain advances past.

**`qwen` has no `auth` subcommand, and asking for one costs money.**
Anything after `qwen` that is not a recognized flag becomes the prompt,
so the inherited `qwen auth status` probe asked Qwen the question "auth
status" and was billed for a completion, on every chain walk, while
reporting success because it exited 0.
The registry now declares no auth probe for qwen.
`~/.qwen/settings.json` exists whether or not credentials do, so it is
not the file to test.

**A Google Workspace account needs a project, not a key.**
`gemini` authenticated through OAuth on a Workspace account fails with
`This account requires setting the GOOGLE_CLOUD_PROJECT or
GOOGLE_CLOUD_PROJECT_ID env var`.
Setting `GEMINI_API_KEY` from AI Studio sidesteps the whole code-assist
path and is the shorter route.

**A refresh token can be spent.**
`codex` reports `your refresh token was already used` and retries five
times before failing.
`codex logout` then `codex login` is the fix; re-running the delegation
is not.

**An `opencode` token can be present and wrong.**
`Could not find the appropriate key in your authentication token`
means a stored token exists, so nothing reports it as missing.
Run `opencode auth login` again.

## Reading the Attempts Trail

When no provider answers, the result names what each one did.
That trail is the diagnostic, and it distinguishes cases the doctor
cannot:

```
gemini     Environment variable GEMINI_API_KEY not set
qwen       Credential ~/.qwen/oauth_creds.json expired 2026-03-25
minimax    No credential file found; looked for ~/.mmx/config.json
glm        answered
```

An `exit=None` on an attempt means the provider was ruled out without
being spawned, which is the cheap path working.
An attempt carrying an exit code means a delegation ran and did not
answer, and those are the ones no local check could have predicted.

A machine where every line reads "not set" needs credentials.
A machine where lines read "exit 0 with an empty answer" has
credentials that are being refused, which is a different afternoon.

## One Provider Is Enough

The chain stops at the first real answer, so a single working provider
makes delegation useful.
Adding more buys resilience against one provider's outage and lets
`requirements` steer toward a strength, not a higher chance of success.

Order matters only in that the chain walks registry priority. A
provider that is slow to fail, such as one that retries a stale token,
delays every delegation behind it. Either fix it or drop its priority.

## Exit Criteria

- [ ] `delegate-doctor` run and each `unknown` resolved by one real
      delegation.
- [ ] At least one provider returns a non-empty answer.
- [ ] Any provider that exits 0 with an empty answer is fixed or
      deprioritized, not left in the chain.
- [ ] No provider is reached by a delegation that a credential file
      already ruled out.
