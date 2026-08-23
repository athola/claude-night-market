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
| `AUTH: missing` | A required environment variable is unset. The probe can see this |
| `AUTH: ok` | A probe command confirmed credentials |
| `AUTH: unknown` | The CLI owns its own credentials and the probe will not spawn it to find out |

**`unknown` is not `ok`.** Four of the eight CLIs keep credentials in
their own config files and expose no cheap status command, so the probe
declines to guess.
The only way to resolve an `unknown` is to run one delegation and read
what comes back. Run it from `plugins/conjure`, substituting the
provider whose row you are resolving:

```bash
uv run python scripts/delegation_executor.py codex "Reply with exactly: pong"
```

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
`qwen` with a rejected key prints
`[API Error: 401 Incorrect API key provided]` and exits 0 with nothing
on stdout.
Before the chain existed, selection stopped at qwen because it verified
as available, and returned that silence as the answer.
The chain now advances past it, so the symptom of a bad qwen key is a
slower delegation rather than an empty one. Read the `attempts` trail
to see it.

**An ambient `OPENAI_API_KEY` reaches the wrong endpoint.**
`qwen` is an OpenAI-compatible client with its own base URL, and with
no credentials in `~/.qwen/settings.json` it picks up whatever
`OPENAI_API_KEY` the shell exports.
An OpenAI key sent to Alibaba's endpoint is rejected, which is the 401
above.
Nothing warns about this, because from the CLI's side a key was
supplied. Authenticate qwen on its own terms rather than relying on an
inherited variable.

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
gemini     GEMINI_API_KEY not set          -> set the key
qwen       exit 0 with an empty answer     -> key present and rejected
minimax    Service not authenticated       -> mmx auth login
glm        answered                        -> nothing to do
```

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
