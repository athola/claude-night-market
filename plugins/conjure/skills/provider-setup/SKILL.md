---
name: provider-setup
description: Reports which delegation CLIs are installed and authenticated, installs missing ones, and stores the result. Use before delegating or when a provider errors.
alwaysApply: false
category: delegation-infrastructure
tags:
- setup
- providers
- authentication
- installation
dependencies:
- delegation-core
---

# Provider Setup

## Intent

An operator should be able to ask what this machine can delegate to,
get a truthful answer, install what is missing, and have that answer
remembered. Before this skill existed, an unconfigured provider
surfaced only as a failed delegation, and every call re-derived the
same facts by spawning up to sixteen subprocesses.

## When To Use

- Before the first delegation on a new machine
- When a provider errors out and it is unclear whether the cause is
  the binary, the credential, or the model
- When deciding which provider to name in a delegation request

## When NOT To Use

- Choosing between two providers that are both ready
  (`Skill(conjure:delegation-core)` routes)
- Debugging a provider's output rather than its availability

## What it reports

`scripts/delegation_setup.py` probes each registered service and
prints a table: binary, version, installed, authenticated, and the
fix for each unhealthy row.

```bash
python3 scripts/delegation_setup.py --status
python3 scripts/delegation_setup.py --doctor
python3 scripts/delegation_setup.py --available
```

`--available` is the short answer: the providers confirmed ready to
take work right now.

## Installing

Installs come from the provenance map in `delegation_executor`, which
is the only source of install commands. A binary with no recorded
provenance raises instead of falling back to a guess, because #655
shipped a service naming a binary that an unaffiliated package
publishes.

```bash
python3 scripts/delegation_setup.py --install gemini
python3 scripts/delegation_setup.py --all
```

Every install asks first. Declining is a recorded outcome, not a
failure, so `--all` on a machine where two of eight CLIs are wanted
still exits 0.

## What is remembered, and what is not

`plugins/conjure/scripts/provider_ledger.py` writes
`~/.claude/hooks/delegation/provider-state.json`. What it stores is
asymmetric on purpose:

| Fact | Cached | Why |
|------|--------|-----|
| Installed, version | Yes, under a 6-hour TTL | Cheap to re-derive, stable between runs |
| Confirmed credential | As a timestamp, never a boolean | A token expires without touching the binary |
| A recorded failure | Clears the confirmation immediately | A stale success must not outlive the credential |

A provider whose credentials live inside its CLI reports
`auth_checked: false`, and that never becomes a confirmation. "We did
not look" and "it works" are different claims, and the table keeps
them apart.

The file is a cache. A truncated or unreadable ledger loads as empty
and costs one round of probes.

## What this does not change

Routing still probes live. `Delegator.verify_service` spawns the
version and auth probes on the delegation path as it always did, and
the ledger does not short-circuit it.

That is a deliberate boundary, not an unfinished edge. Reading a cached
success into the router would send work to a provider whose token
expired since the probe, and reading a cached failure into the router
would disable a provider for the rest of the TTL after one transient
error. The ledger answers an operator's question, "what is set up on
this machine", where a six-hour-old answer is useful and a wrong one
costs a re-run. The router answers "can this call succeed now", where a
wrong answer costs the call.

Wiring the ledger into `verify_service` needs a failure taxonomy that
separates a transient refusal from a revoked credential. That does not
exist yet.

## Exit Criteria

- [ ] `python3 scripts/delegation_setup.py --status` prints one row
      per registered service with its installed and authenticated
      state
- [ ] `--available` names only providers that are installed, carry a
      confirmed credential, are inside the TTL, and have no recorded
      failure
- [ ] `~/.claude/hooks/delegation/provider-state.json` exists after a
      probe and parses as JSON with `"version": 1`
- [ ] An install request for a binary with no provenance entry raises
      `UnverifiedBinaryError` instead of running a guessed command
- [ ] A recorded failure clears any standing `auth_confirmed_at`, so a
      provider that starts refusing work leaves `--available`
- [ ] A corrupt ledger file loads as empty rather than raising

## Related Skills

- `Skill(conjure:delegation-core)`: the routing this setup feeds
- `Skill(leyline:service-registry)`: health checks for external
  services generally
