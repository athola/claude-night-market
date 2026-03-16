# ADR 0008: Behavioral Contract Verification Framework

## Status

Superseded - 2026-03-15

ERC-8004 (blockchain) replaced by GitHub Attestations (SLSA).

## Context

The night-market plugin marketplace needs verifiable trust
signals. Currently, consumers install plugins on faith:
there is no mechanism to prove that a plugin's behavioral
contracts (content assertions, quality gates) passed at a
given version.

### Requirements

- Publish L1/L2/L3 content assertion results to a
  verifiable registry
- Give each plugin a portable, queryable identity
- Enable cross-repo consumers to verify plugin trust
  before installation
- Minimize cost and operational complexity

### Candidates Evaluated

**ERC-8004 (Trustless Agents)**: Ethereum standard live
on mainnet since January 2026. Three registries: Identity
(ERC-721), Reputation (feedback signals), Validation
(independent checks). Requires wallet configuration, RPC
endpoints, and gas fees even on L2 chains.

**GitHub Attestations (SLSA)**: Built into GitHub Actions.
Generates cryptographically signed SLSA provenance
attestations for build artifacts. Zero cost for public
repos. No wallet, RPC, or chain configuration needed.
Uses Sigstore for signing, with verification via
`gh attestation verify`.

**Fetch.ai uAgents**: Python-native agent framework with
Almanac smart contract registration. Designed for agent
discovery, not assertion publishing. Gas model uses FET
tokens on a separate chain.

**Runtime Verification K Framework**: Formal verification
methodology using rewrite-based executable semantics.
Verification tool, not a registry infrastructure.

## Decision (Original - Superseded)

The original decision adopted ERC-8004 as the verification
framework. This was superseded on 2026-03-15 due to
operational costs and complexity.

## Decision (Current)

Adopt **GitHub Attestations (SLSA)** as the behavioral
contract verification framework. Use GitHub Actions
workflow runs as the trust signal source, with SLSA
provenance attestations for cryptographic proof.

### Rationale

| Criterion | GitHub Attestations | ERC-8004 |
|-----------|-------------------|----------|
| Cost | Free (GitHub-hosted) | Gas fees on L2 |
| Setup | Zero (built into Actions) | Wallet + RPC config |
| Signing | Sigstore (automatic) | Ethereum keys |
| Verification | `gh attestation verify` | Custom SDK + web3 |
| Infrastructure | GitHub (already used) | Blockchain node/RPC |
| Python deps | None (uses `gh` CLI) | web3.py |
| Maturity | GA since 2024 | Mainnet since Jan 2026 |

**Key factors:**

1. Zero marginal cost: GitHub Actions runs already happen
   for CI. Attestations add no cost for public repos.
2. No new infrastructure: no wallets, no RPC endpoints,
   no chain selection, no gas management.
3. SLSA provenance is cryptographically signed via
   Sigstore, providing tamper-evident build records.
4. The `gh` CLI is the only runtime dependency, already
   available in all CI environments and most dev machines.
5. Cross-repo verification works via `gh attestation
   verify` without trusting the source CI configuration.

### Architecture

```
pytest (content assertions)
    |
    v
GitHub Actions workflow (captures test results)
    |
    v
trust-report.json (test pass/fail summary)
    |
    v
actions/attest-build-provenance (SLSA attestation)
    |
    v
gh api / gh attestation verify (consumer verification)
```

### Implementation Phases

| Phase | Scope |
|-------|-------|
| 1 | Remove ERC-8004 SDK and blockchain dependencies |
| 2 | Rewrite verify_plugin.py to use GitHub API |
| 3 | Create trust-attestation.yml workflow |
| 4 | Update trust badge generator for GitHub Actions |

## Consequences

### Positive

- Zero cost verification for all plugins
- No wallet or blockchain configuration needed
- Cryptographically signed via Sigstore/SLSA
- Uses infrastructure already in place (GitHub Actions)
- Simpler dependency tree (no web3.py)
- Cross-repo verification via `gh attestation verify`

### Negative

- Tied to GitHub as the attestation provider
- No immutable on-chain record (GitHub can delete runs)
- Attestation history limited by GitHub retention policy
- Less decentralized than blockchain approach

### Risks

- GitHub Actions retention policy may limit historical
  depth (mitigated by SLSA attestations which persist
  independently)
- GitHub API rate limits for heavy verification use
  (mitigated by caching and offline mode)

## Historical Context (ERC-8004 Research)

The original evaluation of ERC-8004, Fetch.ai uAgents,
and K Framework is preserved here for reference. The
ERC-8004 approach was technically sound but introduced
operational overhead (wallet management, gas costs, RPC
configuration) that was disproportionate to the project's
current scale. If the project grows to require
cross-platform, decentralized verification beyond GitHub,
ERC-8004 remains a viable future option.

## References

- [GitHub Attestations docs](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations)
- [SLSA framework](https://slsa.dev/)
- [Sigstore](https://www.sigstore.dev/)
- [actions/attest-build-provenance](https://github.com/actions/attest-build-provenance)
- [ERC-8004 specification](https://eips.ethereum.org/EIPS/eip-8004) (historical)
