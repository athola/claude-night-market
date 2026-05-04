# Windows Patterns

This module covers progressive-loading for skills that target
Windows as the development or deployment host. The selection
question is which Windows-specific modules to load: file paths
(drive letters, UNC paths), shells (PowerShell vs cmd), package
managers (winget, Chocolatey, Scoop), services, and WSL bridging.

## When This Module Applies

Load this module when:

- The active machine reports `Windows_NT` from `$env:OS` or
  `MSYS_NT-*` from `uname -s`.
- The task touches paths with drive letters (`C:\...`) or UNC
  prefixes (`\\server\share`).
- The user mentions PowerShell, cmd, winget, or WSL.
- The deployment target is Windows desktop or Windows Server.

For Linux paths and tools, load `linux-patterns.md`. For macOS,
load `macos-patterns.md`. The three are mutually exclusive per
session unless the task is explicitly cross-platform.

## Detect Shell and Subsystem First

Windows ships multiple shells with different syntax. The shell
detection drives the syntax sub-module.

```powershell
# PowerShell detection (v5.1+ on Windows by default, v7+ if installed)
$PSVersionTable.PSVersion.Major

# WSL detection from PowerShell
wsl --status

# From inside WSL, detect the host
test -f /proc/sys/kernel/osrelease && \
  grep -qi microsoft /proc/sys/kernel/osrelease && echo "WSL"
```

PowerShell 5.1 ships with Windows; PowerShell 7+ is a separate
install. Their syntax differs subtly (e.g., null handling,
parallel execution). The sub-module documents what works in
both.

## Loading Map

| Sub-Concern | Module | Token Estimate |
|-------------|--------|----------------|
| PowerShell scripting | `powershell-rules.md` | 500 |
| cmd / batch scripting | `cmd-rules.md` | 300 |
| WSL interop | `wsl-bridge.md` | 400 |
| Path conventions | `windows-paths.md` | 300 |
| Package managers | `windows-packages.md` | 400 |
| Services | `windows-services.md` | 400 |

The path conventions sub-module is small enough to keep
always-loaded when targeting Windows.

## Path Conventions

Windows paths differ from POSIX in three ways: drive letters,
backslash separators, and case-insensitive comparison.

```powershell
# User profile (PowerShell)
$env:USERPROFILE              # C:\Users\alex
$env:APPDATA                  # C:\Users\alex\AppData\Roaming
$env:LOCALAPPDATA             # C:\Users\alex\AppData\Local
$env:PROGRAMDATA              # C:\ProgramData

# Programs
$env:PROGRAMFILES             # C:\Program Files
${env:PROGRAMFILES(X86)}      # C:\Program Files (x86)
```

For cross-platform Python, `Path` accepts both separators on
Windows but normalizes to backslash on output. Use forward
slashes in source code and let `Path` handle the conversion.

## Package Manager Detection

Windows has three popular package managers, each with its own
defaults.

```powershell
# winget (Microsoft, ships with Windows 10+ since 2020)
winget --version

# Chocolatey (community, requires admin install)
choco --version

# Scoop (community, user-scope by default)
scoop --version
```

For new tooling, prefer `winget` because it ships by default.
The package sub-module documents install commands for each.

## WSL Bridging

WSL2 lets Linux processes run alongside Windows. The bridge
sub-module documents the path translation rules.

```powershell
# Run a WSL command from PowerShell
wsl ls /home/user

# Access WSL files from Windows
\\wsl$\Ubuntu\home\user

# Access Windows files from WSL
/mnt/c/Users/alex/Documents
```

File operations across the boundary are slow. For performance,
keep files on the side that uses them most: WSL files for Linux
tooling, Windows paths for Windows-native tools.

## Concrete Example: PowerShell Path Handling

The PowerShell sub-module documents the path operators.

```powershell
# Join paths portably
$config = Join-Path $env:APPDATA "myapp\config.toml"

# Test existence
Test-Path $config

# Read text with explicit encoding (UTF-8 without BOM)
$text = Get-Content $config -Raw -Encoding UTF8

# Write with explicit encoding
Set-Content -Path $config -Value $text -Encoding UTF8 -NoNewline
```

`Get-Content -Raw` returns the file as one string. Without
`-Raw`, it returns an array of lines, which surprises authors
expecting POSIX semantics.

## Pitfalls

1. **Hard-coding `/` separators in shell scripts**: cmd.exe
   does not accept forward slashes for executables (only
   arguments). Use `Path` in Python and `Join-Path` in
   PowerShell.
2. **Assuming POSIX line endings**: Windows files default to
   CRLF. Reading a Windows file with `splitlines()` works, but
   writing back without specifying line endings produces mixed
   content.
3. **Skipping the encoding flag**: PowerShell 5.1 defaults to
   UTF-16 LE for `Out-File`. Always specify `-Encoding UTF8`
   for portable output.
4. **Confusing PowerShell 5 and 7**: Some cmdlets behave
   differently. The PowerShell sub-module documents the major
   differences.
5. **Treating WSL as fully Linux**: WSL has caveats around
   file permissions, network namespaces, and `/proc` content.
   Test cross-boundary workflows explicitly.

## Cross-Reference

See `linux-patterns.md` and `macos-patterns.md` for the other
platforms in the mutually-exclusive group, and the parent
`SKILL.md` for the platform-selection contract.
