# macOS Patterns

This module covers progressive-loading for skills that target
macOS as the development or deployment host. The selection
question is which macOS-specific modules to load: file system
layout (HFS+/APFS), process control via `launchd`, package
managers (Homebrew, MacPorts), code signing, and the security
sandbox.

## When This Module Applies

Load this module when:

- The active machine reports `Darwin` from `uname -s`.
- The task touches paths under `/Applications`, `~/Library`, or
  `/System`.
- The user mentions `brew`, `launchctl`, `codesign`, or
  `xcode-select`.
- The deployment target is macOS desktop or mac-hosted CI.

For Linux paths and tools, load `linux-patterns.md`. For
Windows, load `windows-patterns.md`. The three are mutually
exclusive per session unless the task is cross-platform.

## Detect macOS Version Before Sub-Loading

Major macOS versions change defaults significantly. The version
detection drives which sub-module loads.

```bash
# Get macOS version (e.g., "14.4.1")
sw_vers -productVersion

# Get the major version only
sw_vers -productVersion | cut -d. -f1
```

macOS 11 (Big Sur) and later use APFS by default and ship with
zsh as the user shell. macOS 10.15 (Catalina) introduced
notarization requirements. The version-specific module documents
what changed in each release relevant to skill behavior.

## Path Conventions

macOS uses a layered file system that differs from Linux. The
shared module documents the conventions.

```bash
# User configs (Apple convention)
~/Library/Application Support/<bundle-id>/

# User caches
~/Library/Caches/<bundle-id>/

# User logs
~/Library/Logs/<bundle-id>/

# Per-user launchd agents
~/Library/LaunchAgents/

# System-wide apps
/Applications/

# Command-line tools (Homebrew on Apple Silicon)
/opt/homebrew/bin/

# Command-line tools (Homebrew on Intel)
/usr/local/bin/
```

Bundle IDs use reverse-DNS notation (`com.example.myapp`). For
non-bundled tools, the convention is the tool name as a folder
under `Application Support`.

## launchd Service Pattern

Long-running services on macOS use `launchd` instead of systemd.
The launchd sub-module documents the plist format.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.example.myagent</string>
    <key>ProgramArguments</key>
    <array>
      <string>/usr/local/bin/myagent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
  </dict>
</plist>
```

User-scoped agents go in `~/Library/LaunchAgents/`. System-scoped
daemons go in `/Library/LaunchDaemons/` and require root. Load
with `launchctl load -w <path>`, unload with `launchctl unload`.

## Homebrew Detection

Homebrew is in different prefixes on Apple Silicon versus
Intel. The Homebrew sub-module documents detection.

```bash
# Detect Homebrew prefix
if command -v brew >/dev/null 2>&1; then
    BREW_PREFIX=$(brew --prefix)
elif [ -x /opt/homebrew/bin/brew ]; then
    BREW_PREFIX=/opt/homebrew
elif [ -x /usr/local/bin/brew ]; then
    BREW_PREFIX=/usr/local
fi
```

Apple Silicon Macs default to `/opt/homebrew`. Intel Macs use
`/usr/local`. Skills installing tools via Homebrew should never
hard-code one prefix.

## Pitfalls

1. **Hard-coding `/usr/local/bin`**: This breaks on Apple Silicon
   Macs where Homebrew is at `/opt/homebrew`. Use the
   detection block above.
2. **Treating `~/Library/Application Support` as `~/.config`**:
   They are conceptually similar but the Apple convention uses
   bundle IDs and case-sensitive folder names with spaces.
3. **Skipping notarization for distribution**: macOS 10.15+
   blocks unsigned and unnotarized executables from running.
   Distribution skills must load the codesign sub-module.
4. **Using `service` or `systemctl`**: macOS does not ship these
   commands. Use `launchctl` and the plist format.
5. **Assuming bash**: macOS 10.15+ ships zsh as the user
   default. Scripts that rely on bash 4 features need an
   explicit `#!/usr/bin/env bash` shebang and a Homebrew bash
   install (the system bash is 3.2).

## Cross-Reference

See `linux-patterns.md` and `windows-patterns.md` for the other
platforms in the mutually-exclusive group, and the parent
`SKILL.md` for the platform-selection contract.
