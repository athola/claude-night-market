# Cross-Cutting Hardening Checks

Checks that apply regardless of the source language: dependency
posture, secret hygiene, CI/CD chain, container shape, and the
SBOM.

## Dependency posture (composes leyline:supply-chain-advisory)

| ID | Check | CWE / NIST | Detection |
|----|-------|------------|-----------|
| DEP01 | Lockfile committed | PW.4 | absence of `uv.lock` / `Cargo.lock` / `package-lock.json` |
| DEP02 | Dependency scanner runs in CI | RV.1 | no `pip-audit`/`cargo audit`/`npm audit` step in workflows |
| DEP03 | Known-bad versions blocked | CWE-829 | `leyline:supply-chain-advisory` blocklist not consulted |
| DEP04 | Auto-update bot configured | RV.1 | no `dependabot.yml` / `renovate.json` |
| DEP05 | Direct deps pinned to exact versions | CWE-494 | `^1.2` / `~1.2` / `1.2.*` for security-critical deps |
| DEP06 | Hash-pinned for top-tier supply-chain trust | CWE-494 | `--require-hashes` not used in `pip` / `requirements.txt` |
| DEP07 | License policy enforced | none | no `cargo deny` license rules / no `pip-licenses` check |

## Secret hygiene

| ID | Check | CWE | Detection |
|----|-------|-----|-----------|
| SEC01 | Pre-commit secret scanner installed | CWE-798 | no `gitleaks` / `trufflehog` / `talisman` in `.pre-commit-config.yaml` |
| SEC02 | `.env` files git-ignored | CWE-200 | `.env` tracked or unmatched in `.gitignore` |
| SEC03 | Long-lived secrets in CI | CWE-798 | `secrets.SOME_KEY` used without `if: github.event_name != 'pull_request'` |
| SEC04 | OIDC publishing configured | CWE-798 | PyPI/Cargo publish step uses `password:` rather than OIDC `id-token: write` |
| SEC05 | Audit trail for secret access | PW.7 | repo settings: secret-access logs not retained |
| SEC06 | Sealed-secrets / secret manager | CWE-798 | secrets baked into config files instead of fetched from a manager |

## CI/CD chain (GitHub Actions example)

| ID | Check | NIST SSDF | Detection |
|----|-------|-----------|-----------|
| CI01 | Third-party actions pinned by SHA, not tag | PW.4 | `uses: foo/bar@v1` instead of `@<full SHA>` |
| CI02 | `permissions:` block per workflow | PW.4 | top-level `permissions:` missing or `permissions: write-all` |
| CI03 | `GITHUB_TOKEN` minimum scope | PW.4 | default permissions used when `contents: read` would suffice |
| CI04 | Concurrency cancel for stale runs | RV.2 | no `concurrency.cancel-in-progress: true` |
| CI05 | Workflow dispatch requires approval for protected branches | PW.4 | branch protection allows direct dispatch |
| CI06 | SLSA provenance generated for releases | RV.2 | release workflow does not invoke `slsa-framework/slsa-github-generator` |
| CI07 | SBOM generated and attached to releases | RV.2 | release workflow lacks `cyclonedx`/`syft`/`spdx-sbom-generator` step |

## Container hardening (when Dockerfiles exist)

| ID | Check | CWE | Detection |
|----|-------|-----|-----------|
| CO01 | Non-root `USER` set | CWE-269 | `USER root` or `USER` directive missing |
| CO02 | `FROM` is digest-pinned | CWE-494 | `FROM ubuntu:22.04` instead of `FROM ubuntu@sha256:...` |
| CO03 | Distroless or slim base for production | PW.4 | `FROM ubuntu:latest` / `FROM debian:latest` for runtime image |
| CO04 | Read-only root filesystem in compose | CWE-269 | `read_only: true` not set |
| CO05 | seccomp/apparmor profile referenced | CWE-269 | runtime config lacks profile |
| CO06 | Multi-stage build to drop build deps | CWE-665 | single-stage `FROM` keeps `gcc`, `make`, etc. in runtime |
| CO07 | `HEALTHCHECK` defined | none | no liveness signal (operational hygiene) |

## SBOM and provenance

```bash
# CycloneDX SBOM for the whole repo
syft . -o cyclonedx-json > sbom.cdx.json

# SPDX SBOM (alternative format)
syft . -o spdx-json > sbom.spdx.json

# Verify against the in-toto attestation if released
cosign verify-attestation --type slsaprovenance \
  --certificate-identity-regexp '.*' --certificate-oidc-issuer-regexp '.*' \
  ghcr.io/<org>/<image>:<tag>
```

The hardening report includes an SBOM-coverage row: present /
absent for each release artifact in the repo.

## Pre-commit security suite

The skill proposes adding (or extending) `.pre-commit-config.yaml`
with:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
```

If `cargo` is on PATH:

```yaml
  - repo: local
    hooks:
      - id: cargo-deny
        name: cargo deny
        entry: cargo deny check
        language: system
        files: 'Cargo\.(toml|lock)$'
```

## Severity defaults

| Family | Default | Justification |
|--------|---------|---------------|
| DEP04, DEP07, CI07, CO07 | LOW | operational hygiene; no exploit narrative |
| DEP01, DEP02, SEC01, SEC02, CI02, CI03, CO01, CO02 | MEDIUM | one defense-in-depth layer missing |
| DEP03, SEC03, SEC04, CI01, CI06, CO03 | HIGH | exploitable supply-chain or privilege issue |
| SEC03 with leaked active credential | CRITICAL | active exploit path |

A finding can be promoted from default with evidence (e.g.,
DEP01 promoted to HIGH if the lockfile is missing AND auto-merge
is enabled on dep PRs).
