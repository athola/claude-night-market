# Binary Provenance

## What ships in bin/

The `skrills` binary is an optional performance accelerator for
skill validation, analysis, and metrics. It is **never required**
-- all functionality falls back to Python scripts when the binary
is absent.

## Build from source (recommended)

```bash
# Clone and build
git clone https://github.com/athola/skrills.git
cd skrills && cargo build --release

# Install into this plugin
make skrills-build SKRILLS_REPO=/path/to/skrills

# Verify the hash
make skrills-verify
```

## Security model

**The binary is not committed to git.** Users build from auditable
Rust source or download a CI-built release with SLSA attestation.

| Concern | Mitigation |
|---------|------------|
| Opaque compiled code | Build from source; Rust source is auditable |
| Supply chain attack | Cargo.lock pins all dependencies; `cargo audit` runs in CI |
| Tampered binary | SHA-256 hash pinned in `.skrills-version`; `make skrills-verify` checks it |
| Stale binary | Version file tracks build; `make skrills-build` rebuilds from latest source |
| Pre-2.1.91 users | All bin/ usage has Python fallback; no functionality is lost |

## Why a binary?

Hooks run on every tool call with strict timeouts (1-2s). Python
startup alone consumes 200-400ms. The skrills binary starts in
<10ms and validates 150+ skills in <100ms, leaving budget for
the actual hook logic.

## Fallback chain

1. `plugins/abstract/bin/skrills` (local build)
2. `skrills` on PATH (cargo install)
3. Python script equivalent (always works)
