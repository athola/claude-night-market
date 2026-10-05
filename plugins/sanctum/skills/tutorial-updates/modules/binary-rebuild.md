# Binary Rebuild Module

**CRITICAL**: Ensure the binary being tested in tapes matches the latest source code. Stale binaries produce misleading demos.

### Step 1.6.1: Detect Build System

Identify the project's build system:

```bash
# Check for Cargo (Rust)
if [ -f "Cargo.toml" ]; then
  BUILD_SYSTEM="cargo"
  BINARY_NAME=$(grep '^name = ' Cargo.toml | head -1 | sed 's/.*"\(.*\)"/\1/')
  echo "Detected Cargo project: $BINARY_NAME"
# Check for Makefile
elif [ -f "Makefile" ]; then
  BUILD_SYSTEM="make"
  echo "Detected Make project"
# Unknown
else
  echo "WARNING: Unknown build system, skipping binary check"
  BUILD_SYSTEM="unknown"
fi
```
**Verification:** Run `make --dry-run` to verify build configuration.

### Step 1.6.2: Check Binary Freshness

Compare binary modification time against Git HEAD:

```bash
check_binary_freshness() {
  local binary_name="$1"

  # Locate binary (check cargo install location first, then PATH)
  local binary_path=$(which "$binary_name" 2>/dev/null)

  if [ -z "$binary_path" ]; then
    echo "WARNING: Binary '$binary_name' not found in PATH"
    return 1
  fi

  # Get binary modification time (Linux/macOS compatible)
  local binary_mtime
  if command -v stat >/dev/null 2>&1; then
    # Linux
    binary_mtime=$(stat -c %Y "$binary_path" 2>/dev/null || \
    # macOS
    stat -f %m "$binary_path" 2>/dev/null)
  else
    echo "WARNING: stat command not available, skipping freshness check"
    return 2
  fi

  # Get Git HEAD commit time
  local git_head_time=$(git log -1 --format=%ct 2>/dev/null)

  if [ -z "$git_head_time" ]; then
    echo "WARNING: Not a git repository, skipping freshness check"
    return 2
  fi

  # Compare timestamps
  if [ "$binary_mtime" -lt "$git_head_time" ]; then
    echo "STALE: Binary is older than Git HEAD"
    echo "  Binary: $(date -d @$binary_mtime 2>/dev/null || date -r $binary_mtime)"
    echo "  HEAD:   $(date -d @$git_head_time 2>/dev/null || date -r $git_head_time)"
    return 1
  else
    echo "OK: Binary is up-to-date"
    return 0
  fi
}
```
**Verification:** Run `git status` to confirm working tree state.

### Step 1.6.3: Rebuild Binary

Rebuild using the detected build system:

```bash
rebuild_binary() {
  local build_system="$1"
  local binary_name="$2"

  case "$build_system" in
    cargo)
      echo "Rebuilding with Cargo..."
      # Use cargo install for CLI binaries
      if [ -d "crates/cli" ]; then
        cargo install --path crates/cli --locked --quiet
      else
        cargo install --path . --locked --quiet
      fi
      ;;
    make)
      echo "Rebuilding with Make..."
      make --quiet
      ;;
    *)
      echo "ERROR: Cannot rebuild, unknown build system"
      return 1
      ;;
  esac

  echo "Build complete: $binary_name"
}
```
**Verification:** Run `make --dry-run` to verify build configuration.

### Step 1.6.4: Verify Binary Accessibility

Ensure the rebuilt binary is accessible:

```bash
verify_binary() {
  local binary_name="$1"

  if ! command -v "$binary_name" >/dev/null 2>&1; then
    echo "ERROR: Binary '$binary_name' not found after rebuild"
    echo "  Check PATH includes: $HOME/.cargo/bin"
    return 1
  fi

  # Test binary can execute
  if ! "$binary_name" --version >/dev/null 2>&1; then
    echo "WARNING: Binary exists but --version failed"
  else
    echo "OK: Binary is accessible and functional"
    "$binary_name" --version
  fi
}
```
**Verification:** Run `pytest -v` to verify tests pass.

### Rebuild Flags

| Flag | Behavior |
|------|----------|
| `--skip-rebuild` | Skip binary freshness check and rebuild |
| `--force-rebuild` | Force rebuild even if binary is fresh |

### Rebuild Exit Criteria

- [ ] Build system detected (Cargo, Make, or explicitly skipped)
- [ ] Binary freshness checked against Git HEAD
- [ ] Binary rebuilt if stale (or forced)
- [ ] Rebuilt binary is accessible in PATH
- [ ] Binary executes successfully (--version test)

**If rebuild fails**: Stop immediately, report build errors, and do NOT proceed to tape validation or VHS recording.
