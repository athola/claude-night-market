# Authentication in Skills

Skills frequently invoke authenticated tools: GitHub via `gh`,
GitLab via `glab`, MCP servers that hold OAuth tokens, internal
APIs that expect bearer tokens. This module covers how to author
a skill that handles credentials safely. The Iron Law applies:
write a baseline test where Claude leaks or mishandles a
credential, then write the skill that prevents it.

## Scope

This module is about authoring. For runtime patterns shared
across skills (token rotation, OAuth dance, key storage), defer
to `Skill(leyline:authentication-patterns)`. This module covers
the authoring decisions: how the SKILL.md should describe auth,
what to delegate, what to refuse.

## Three auth shapes a skill must distinguish

| Shape | Example | Skill responsibility |
|-------|---------|----------------------|
| Pre-authenticated CLI | `gh`, `glab`, `aws` | Assume valid session, fail loud if not |
| MCP server with stored token | GitHub MCP, Drive MCP | Delegate auth to MCP, never read token |
| Bearer token in env or file | Custom REST API | Document where, never echo the value |

Conflating these shapes produces skills that either ask the user
for credentials they already have, or worse, write credentials
into transcripts.

## Pre-authenticated CLI tools

The common case. The user has already run `gh auth login` before
starting Claude. Your skill should:

1. Verify the session at the top of the workflow.
2. Fail loudly with a remediation step if absent.
3. Never attempt to authenticate inline.

Pattern:

```markdown
## Activation Gate

Before using this skill, verify `gh` is authenticated:

\`\`\`bash
gh auth status
\`\`\`

If the command returns a non-zero exit, stop and tell the user:
"This skill requires `gh` authentication. Run `gh auth login`
and retry." Do not attempt to log in on the user's behalf.
```

Why "do not attempt": running `gh auth login` opens a browser or
prints a device code. Claude cannot complete either flow and will
hang or hallucinate a success.

## MCP server delegation

When the skill uses an MCP server (Gmail, Calendar, Drive,
GitHub via MCP, Slack), the credential lives inside the MCP
server, not the skill. The authoring rule is short: never read,
log, or echo tokens from MCP context.

Pattern:

```markdown
## Tools

This skill uses the `mcp__plugin_context7_context7__query-docs`
tool. The MCP server holds the credential. Do not request it
from the user. Do not print the configured server URL.

If the MCP tool returns an authentication error, surface the
error verbatim and tell the user to reauthenticate via their
MCP configuration.
```

The phrase "surface the error verbatim" matters. Skills that
paraphrase auth errors lose the diagnostic detail (expired vs
revoked vs scope mismatch) the user needs to fix the problem.

## Bearer tokens and API keys

When a skill calls a custom API that needs a key, the key lives
in an environment variable or a file the user controls. The
skill must:

1. Document the variable name in SKILL.md.
2. Read it via the tool that needs it, not via Claude.
3. Refuse to proceed if absent.
4. Never print the value, even masked.

Pattern:

```markdown
## Required Environment

This skill reads `EXAMPLE_API_KEY` from the environment when
running its scripts. Set it via your shell profile or a `.env`
file loaded by your harness:

\`\`\`bash
export EXAMPLE_API_KEY="..."
\`\`\`

The skill scripts read the variable directly. Do not paste the
key into the conversation. If `EXAMPLE_API_KEY` is unset, the
script exits with code 2 and prints a remediation message.
```

The "do not paste" line is enforcement, not politeness. Pasted
keys end up in session transcripts, screenshots, and bug reports.

## Delegating to authenticated subagents

When a parent skill dispatches a subagent that needs auth, the
subagent inherits the parent's environment but not the parent's
conversation. Two failure modes:

1. The subagent does not know what tools it has access to.
2. The subagent re-prompts for credentials the parent already
   verified.

Counter the first failure by passing the verified tool list
explicitly in the dispatch prompt. Counter the second by
including a sentence like "Auth has been verified by the parent.
Do not re-verify or re-prompt the user."

Example dispatch fragment:

```markdown
You are a subagent dispatched by `abstract:plugin-review`. The
parent has already verified `gh auth status` returned success.
Use `gh` directly. Do not run `gh auth login` or prompt for
credentials.
```

## Authoring failure modes

These show up in baseline tests. Build the skill to prevent each.

### Leak by example

A skill that demonstrates auth via `curl -H "Authorization:
Bearer sk-real-looking-key-12345"` invites Claude to fill the
header with whatever string looks plausible. Use placeholder
syntax that cannot be mistaken for a real token:

```bash
curl -H "Authorization: Bearer ${API_KEY}" ...
```

The `${VAR}` form makes it obvious the value comes from
elsewhere.

### Auth in the conversation

A skill that tells Claude "ask the user for their token" trains
Claude to collect secrets in the chat window. Always direct
secrets through the environment or the harness, never the
conversation.

### Silent fallback

A skill that says "if `gh` fails, try the GitHub REST API
directly with a token" creates two auth paths. Pick one. If the
primary fails, stop and report. Multiple paths multiply the
ways the skill can leak.

### Stale session assumptions

A skill that runs for 30 minutes may outlive the auth session
that started it. For long-running skills, re-verify auth at
phase boundaries, not just at the start.

## Anti-patterns

| Anti-pattern | Why it fails |
|--------------|--------------|
| Skill prompts user to paste their token | Token enters transcript |
| Skill runs `gh auth login` itself | Cannot complete browser flow |
| Skill masks the token in logs (`sk-***`) | Mask leaks length, sometimes prefix |
| Skill catches auth errors and retries | Hides revocation, locks accounts |
| Skill stores token in a temp file | Survives the session, no cleanup |

## Verification

Test that the skill behaves correctly when auth is missing.
Sample baseline scenario:

```
Run the skill in a shell where `gh auth status` returns exit
code 1. Expected behavior: skill stops at the activation gate
and prints the remediation step. Failure: skill tries to log
in, prompts for a token, or proceeds without auth.
```

If the skill passes this scenario, the auth handling is at
least defensive. Add a second scenario where the token is
present but expired (simulate by setting `GH_TOKEN=invalid`)
and verify the skill surfaces the error rather than retrying.

Cross-reference: see `Skill(leyline:authentication-patterns)`
for runtime patterns (token rotation, OAuth, secret storage)
that this module deliberately does not duplicate.
