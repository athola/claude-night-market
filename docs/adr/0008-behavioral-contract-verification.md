# ADR 0008: Behavioral Contract Verification Framework

## Status

Accepted - 2026-03-15

## Context

The night-market plugin marketplace needs verifiable trust
signals. Currently, consumers install plugins on faith:
there is no mechanism to prove that a plugin's behavioral
contracts (content assertions, quality gates) passed at a
given version. Three candidate frameworks exist for
on-chain behavioral contract verification.

### Requirements

- Publish L1/L2/L3 content assertion results to a
  verifiable registry
- Give each plugin a portable, queryable identity
- Enable cross-repo consumers to verify plugin trust
  before installation
- Minimize gas costs and operational complexity

### Candidates Evaluated

**ERC-8004 (Trustless Agents)**: Ethereum standard live
on mainnet since January 2026. Three registries: Identity
(ERC-721), Reputation (feedback signals), Validation
(independent checks). Deployed on Ethereum, Base, Polygon,
Monad, and BNB Chain. Active community on Ethereum
Magicians forum. V2 spec in development with MCP support.

**Fetch.ai uAgents**: Python-native agent framework with
Almanac smart contract registration on the Fetch.ai
blockchain. Auto-registration on startup. Python SDK is
mature for agent-to-agent communication but the Almanac
contract is designed for agent discovery, not assertion
publishing. Gas model uses FET tokens on a separate chain.

**Runtime Verification K Framework**: Formal verification
methodology using rewrite-based executable semantics.
Proven in smart contract verification (KEVM, KAVM).
Python interface (pyk) exists. Recent research (2026)
introduces Agent Behavioral Contracts (ABC) with hard
and soft constraint distinctions. However, this is a
verification methodology, not a registry infrastructure.

## Decision

Adopt **ERC-8004** as the behavioral contract verification
framework. Defer formal verification (K Framework) as a
future enhancement for L3 assertions. Do not use uAgents
(wrong abstraction level).

### Rationale

| Criterion | ERC-8004 | uAgents | K Framework |
|-----------|----------|---------|-------------|
| Registry model | Three-registry (Identity, Reputation, Validation) | Single Almanac (discovery only) | No registry (verification tool) |
| Assertion publishing | Native via Reputation Registry | Would need custom extension | N/A |
| Python SDK | Community SDKs (web3.py) | Native Python SDK | pyk (limited) |
| Chain options | Ethereum, Base, Polygon, Monad, BNB | Fetch.ai chain only | Chain-agnostic |
| Gas costs | Low on L2s (Base, Polygon) | FET token model | N/A |
| Community | Active, Ethereum Magicians | Moderate | Niche |
| Maturity | Mainnet since Jan 2026 | Production | Research phase for ABC |
| Fit with L1/L2/L3 | Direct mapping to reputation signals | Would need adapting | Direct for formal proofs |

**Key factors:**

1. ERC-8004's three-registry model maps directly to our
   needs: Identity for plugins, Reputation for assertion
   results, Validation for independent checks.
2. L2 deployment (Base or Polygon) keeps gas costs under
   $0.01 per assertion batch.
3. The standard is live and actively maintained with
   ecosystem support.
4. uAgents solves agent discovery, not trust verification.
5. K Framework is complementary (could verify L3 assertions
   formally) but does not provide the registry layer.

### Architecture

```
pytest (content assertions)
    |
    v
Post-test hook (captures L1/L2/L3 results)
    |
    v
ERC-8004 SDK wrapper
    |
    +---> Identity Registry (plugin identity, ERC-721)
    +---> Reputation Registry (assertion results per commit)
    +---> Validation Registry (independent validator hooks)
```

### Implementation Phases

| Phase | Issue | Scope |
|-------|-------|-------|
| 1 | #238 | On-chain identity registry for plugins/skills |
| 2 | #239 | Publish assertion results to Reputation Registry |
| 3 | #240 | Cross-repo verification CLI |
| 4 | #241 | Marketplace trust badges and dashboard |

### Deployment Target

Base L2 (Ethereum rollup) for low gas costs with
Ethereum mainnet security guarantees. Testnet
development on Base Sepolia.

## Consequences

### Positive

- Verifiable trust signals for plugin consumers
- Immutable assertion history per plugin version
- Cross-repo verification without trusting source CI
- Standard-based approach with ecosystem support

### Negative

- Requires wallet/RPC configuration for publishing
- Gas costs (minimal on L2 but nonzero)
- Additional CI complexity for assertion publishing
- Dependency on ERC-8004 ecosystem stability

### Risks

- ERC-8004 v2 may change APIs (mitigated by abstraction
  layer in SDK wrapper)
- L2 bridge delays for mainnet verification (mitigated
  by using L2 natively)
- Low adoption may reduce network effects (mitigated by
  standalone utility for night-market)

## References

- [ERC-8004 specification](https://eips.ethereum.org/EIPS/eip-8004)
- [ERC-8004 community discussion](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098)
- [Fetch.ai uAgents framework](https://github.com/fetchai/uAgents)
- [K Framework](https://kframework.org/)
- [Agent Behavioral Contracts paper](https://arxiv.org/html/2602.22302)
