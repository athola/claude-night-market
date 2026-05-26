# Cargo Patterns

This module covers progressive-loading inside skills that work
with Rust crates managed by Cargo. The loading question is how
to decide which Cargo-related modules to pull in: dependency
audit, build configuration, workspace handling, or release
publishing. Each is a separate slice with its own token cost.

## When This Module Applies

Load this module when the active task touches:

- A `Cargo.toml` or `Cargo.lock` file.
- A workspace root with multiple member crates.
- A `cargo` subcommand: `build`, `test`, `audit`, `publish`,
  `tree`, `update`, or `bench`.
- Dependency review for supply-chain risk.

If the task is reviewing Rust source for ownership or unsafe
code, load `rust-review.md` instead. This module focuses on the
Cargo tooling layer, not the language semantics.

## Detect the Cargo Layout First

Cargo projects come in two shapes: single-crate and workspace.
The loader needs to know which before pulling in workspace-only
guidance.

```bash
# Single-crate project root
test -f Cargo.toml && ! grep -q '^\[workspace\]' Cargo.toml

# Workspace root
grep -q '^\[workspace\]' Cargo.toml
```

A workspace root delegates dependency versions to member crates
or pins them in `[workspace.dependencies]`. The audit rules
differ enough that they are in separate modules.

## Loading Map

| Slice | Load Trigger | Token Estimate |
|-------|--------------|----------------|
| Dependency audit | `cargo audit` mention or `Cargo.lock` review | 500 |
| Build profile review | `[profile.*]` table edits | 300 |
| Workspace coordination | `[workspace]` detected | 400 |
| Feature flag analysis | `[features]` table edits | 400 |
| Publish checklist | `cargo publish` or release task | 300 |
| MSRV check | `rust-version` field present | 200 |

The smallest slice (MSRV check) is cheap to keep loaded; the
publish checklist is rarely needed and should stay deferred
until the user explicitly asks about a release.

## Concrete Cargo Commands the Modules Reference

Each loaded module documents its own commands; the hub keeps a
small index so users know where to look.

```bash
# Inspect resolved dependency graph
cargo tree --duplicates

# Find unused features
cargo tree -e features

# Audit known advisories (requires cargo-audit)
cargo audit --json

# Check minimum supported Rust version
cargo +1.75 check  # adjust version to declared rust-version
```

`cargo audit` is a real subcommand provided by the
`cargo-audit` crate from RustSec. It is not a built-in
subcommand. The dependency-audit module installs it once per
toolchain with `cargo install cargo-audit`.

## Workspace-Specific Loading

For workspaces, the hub also needs to decide whether to load
guidance per member crate or once for the workspace. The cheap
default is once per workspace, with member-crate detail loaded
on explicit drill-down.

```python
from pathlib import Path
import tomllib

def is_workspace(cargo_toml: Path) -> bool:
    data = tomllib.loads(cargo_toml.read_text(encoding="utf-8"))
    return "workspace" in data

def member_crates(cargo_toml: Path) -> list[str]:
    data = tomllib.loads(cargo_toml.read_text(encoding="utf-8"))
    return data.get("workspace", {}).get("members", [])
```

`tomllib` is in the standard library since Python 3.11. For
older Python, the `tomli` backport offers the same API.

## Pitfalls

1. **Loading workspace guidance for single crates**: Single-crate
   projects do not have member coordination concerns. Skip the
   workspace module unless `[workspace]` is present.
2. **Confusing `Cargo.lock` with dependency declarations**: The
   lock file lists resolved versions. The declarations in
   `Cargo.toml` define the constraints. Audit the lock file for
   advisories and the toml for version policy.
3. **Skipping MSRV when present**: If `rust-version` is set,
   builds against newer toolchains may pass while CI on the
   declared MSRV fails. Always load the MSRV check when the
   field exists.
4. **Caching `cargo tree` output across edits**: Tree output
   changes whenever dependencies change. Re-run after any
   `Cargo.toml` or `Cargo.lock` edit.
5. **Mixing audit and rust-review concerns**: Cargo audit is
   about advisories on dependency versions. Rust review is about
   source code. Keep them in separate modules.

## Cross-Reference

See `rust-review.md` for source-level review concerns, and the
parent `SKILL.md` for how Cargo module loading fits the
hub-and-spoke pattern.
