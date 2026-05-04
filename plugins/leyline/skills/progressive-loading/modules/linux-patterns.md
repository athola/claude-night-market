# Linux Patterns

This module covers progressive-loading for skills that target
Linux as the host or production OS. The selection question is
which OS-specific modules to load: file paths, process control,
package managers, systemd services, or container runtimes. Linux
distros differ enough that some sub-modules are themselves
mutually exclusive.

## When This Module Applies

Load this module when:

- The target machine runs Linux (Ubuntu, Debian, Fedora, RHEL,
  Alpine, Arch, or similar).
- The task touches paths under `/etc`, `/var`, `/proc`, `/sys`,
  or `~/.config`.
- The user mentions `systemd`, `apt`, `dnf`, `pacman`, or a
  Linux package manager.
- The deployment target is a Linux container.

For macOS-specific paths and tools, load `macos-patterns.md`.
For Windows, load `windows-patterns.md`. The three are mutually
exclusive per session unless the task explicitly compares
platforms.

## Detect the Distro Family Before Sub-Loading

Linux distros split into families with different package
managers and init systems. The loader picks one sub-module per
family.

```bash
# Distro detection (POSIX-portable)
. /etc/os-release && echo "$ID $ID_LIKE"

# Examples of expected output:
# ubuntu debian          (Debian family, apt)
# fedora                 (Red Hat family, dnf)
# arch                   (Arch family, pacman)
# alpine                 (Alpine family, apk)
```

`/etc/os-release` is standardized by systemd and present on every
modern distro. The `ID` and `ID_LIKE` fields drive sub-module
selection.

## Loading Map

| Distro Family | Package Manager Module | Init Module |
|---------------|------------------------|-------------|
| Debian/Ubuntu | `apt-patterns.md` | `systemd-patterns.md` |
| RHEL/Fedora | `dnf-patterns.md` | `systemd-patterns.md` |
| Arch | `pacman-patterns.md` | `systemd-patterns.md` |
| Alpine | `apk-patterns.md` | `openrc-patterns.md` |

`systemd-patterns.md` is shared across most families. Alpine and
some minimal containers use OpenRC or no init system at all, so
the init module is gated on detection rather than assumed.

## Path Conventions

The shared Linux module documents the standard paths every
sub-module references. The XDG Base Directory spec is the
modern source.

```bash
# Configuration: ~/.config/<app>/
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"

# Data: ~/.local/share/<app>/
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

# Cache: ~/.cache/<app>/
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Runtime (per-user, cleared on logout)
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
```

System-wide configs live under `/etc`, system data under
`/var/lib`, and system cache under `/var/cache`. The path module
documents both user and system layouts.

## Process Inspection

Linux exposes process state through `/proc`. The process module
documents the most useful entries.

```bash
# All processes for a user
ps -u "$USER" -o pid,pcpu,pmem,comm

# Open files for a process
ls -l /proc/PID/fd/

# Resource limits
cat /proc/PID/limits

# Memory map
cat /proc/PID/maps | head
```

For container introspection, `/proc/1/cgroup` reveals whether
the process runs inside a cgroup-namespaced container. This is
the canonical detection signal for "am I in Docker?".

## Pitfalls

1. **Assuming `apt` everywhere**: A skill that runs `apt install`
   on Fedora fails. Always detect the distro family first.
2. **Skipping XDG**: Hard-coding paths under `$HOME` directly
   (e.g., `~/.myapp`) ignores the XDG spec and conflicts with
   user customization.
3. **Loading the systemd module on Alpine**: Alpine ships with
   OpenRC by default. Detect the init system before loading.
4. **Treating `/proc` as portable**: macOS does not have
   `/proc`. The Linux module is the only place to reference it.
5. **Mixing root and user contexts**: `XDG_RUNTIME_DIR` has a
   sensible value only for interactive user sessions. System
   services need different runtime paths.

## Cross-Reference

See `macos-patterns.md` and `windows-patterns.md` for the other
platforms in the mutually-exclusive group, and the parent
`SKILL.md` for the platform-selection contract.
