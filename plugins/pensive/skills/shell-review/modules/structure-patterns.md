---
parent_skill: pensive:shell-review
module: structure-patterns
description: Library vs executable structure, main(), preamble, depcheck(), platform detection
tags: [structure, main, library, depcheck, platform, readonly, shfmt]
---

# Shell Script Structure Patterns

## Library vs executable

A script is a **library** if it has no `main()` function (e.g.
`scripts/logging.sh`). A script is an **executable** if it defines
`main()` and ends with `main "${@}"`.

Libraries signal their presence by setting a `__`-prefixed guard
variable (e.g. `__logging_loaded=1`). Callers verify it was sourced
with the canonical form:

```sh
case "${__logging_loaded:-NULL}" in
  1) : ;;
  *) printf 'logging.sh not loaded\n' >&2; exit 1 ;;
esac
```

See also: `safety-patterns.md` → "Library loading check form".

| Property | Library | Executable |
|----------|---------|------------|
| Execute bit | No | Yes |
| `main()` | No | Required |
| Last line | — | `main "${@}"` |
| `usage()` | Not needed | Recommended |
| `set -e`/`set -u` | Never | Allowed |
| `__`-prefixed globals | Yes (guards) | Allowed |

Detection: library with execute bit

```sh
find scripts/ -name "*.sh" -perm /u+x | while IFS= read -r f; do
  rg -q 'main\(\)' "${f}" || printf 'Library with +x: %s\n' "${f}"
done
```

Detection: executable missing `main "${@}"` as last line

```sh
find scripts/ -name "*.sh" -perm /u+x | while IFS= read -r f; do
  last="$(tail -1 "${f}")"
  case "${last}" in
    'main "${@}"') : ;;
    *) printf 'Missing main call: %s\n' "${f}" ;;
  esac
done
```

## Preamble for executable scripts

Every executable script must start with this preamble (using
`scripts/shellcheck.sh` as the canonical example):

```sh
#!/bin/sh
set -eu

MYDIR="${0%/*}"
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"
```

- `#!/bin/sh`: POSIX dialect; no Bash extensions
- `set -eu`: exit on error (`-e`), error on unset (`-u`)
- `MYDIR="${0%/*}"`: script directory without `dirname`
- `readonly MYDIR`: marks the variable immutable
- `# shellcheck source=…`: lets shellcheck follow the source
- `. "${MYDIR%/}/logging.sh"`: loads `log()` and `banner()`

## All functionality in functions; no top-down execution

Scripts must never execute logic at top level. Every statement
belongs inside a named function. The only top-level calls are:

1. `set -eu` (preamble)
2. Variable declarations (`readonly`, assignments)
3. Source statements (`. lib.sh`)
4. `main "${@}"` on the last line

Detection:

```sh
# Top-level commands outside function definitions
# (rough heuristic — awk parses function body depth)
awk '/^[a-z_][a-z_0-9]*\(\)/{depth++} /^\}/{depth--}
     depth==0 && /^\s*[a-z]/ && !/^(readonly|MYDIR|LOG|\.|\s*#)/{print NR": "$0}' script.sh
```

## depcheck() for external dependencies

Any script relying on tools beyond POSIX must define `depcheck()`.
Required tools use `log 5` (critical); optional tools use `log 3`
(notice). Dependency lists allow the check logic to stay unchanged
when tools are added.

```sh
REQUIRED_DEPENDENCIES="shellcheck shfmt"

depcheck() {
  _dc_missing=""
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 ||
      _dc_missing="${_dc_missing:+"${_dc_missing} "}${_dc_util}"
  done
  case "${#_dc_missing}" in
    0) return 0 ;;
  esac
  log 5 "Required utilities not found: ${_dc_missing}"
  return 1
}
```

Building `_dc_missing` with `${_dc_missing:+"${_dc_missing} "}${_dc_util}`
is the POSIX way to append a space-separated word without leaving a
leading space. It avoids arrays, which are a Bash extension.

## usage() function

Scripts that accept flags must define `usage()`. The first output
line must use `log "Usage: …"`. Subsequent lines use `printf`.

```sh
usage() {
  log "Usage: scripts/myscript.sh [-h] [-x|-t] [ARGS]"
  printf '  -h       Show this help and exit (exit 0)\n'
  printf '  -x, -t   Enable xtrace for debugging\n'
  printf '  ARGS     Files or patterns to process\n'
}
```

The `usage` and `help` case patterns must accept both spellings and
any case:

```sh
case "${1}" in
  *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
    usage
    exit 0
    ;;
esac
```

## xtrace support (-x / -t flags)

Every executable script must support a flag to enable `xtrace`
for debugging. The preferred flags are `-x` and `-t`.

```sh
XTRACE=0

# …inside main() after arg parsing:
case "${XTRACE}" in
  1) set -x ;;
esac
```

## readonly for non-modified globals

Global variables that do not change during execution must be
marked `readonly`. Group these declarations near the top of the
script, after the preamble.

```sh
readonly MYDIR
readonly VERSION="1.0.0"
readonly CONFIG_FILE="${MYDIR%/}/../.config"
```

## Platform detection

When commands differ by OS, assign the command and its arguments
to separate variables using `uname -s` and distribution files.

```sh
KERNEL="$(uname -s)"
case "${KERNEL}" in
  *BSD | [Ll]inux)
    . /etc/os-release
    case "${ID}" in
      freebsd) INSTALLER="pkg"; INSTALLER_ARG="install" ;;
      ubuntu | debian) INSTALLER="apt-get"; INSTALLER_ARG="install -yqq" ;;
      alpine) INSTALLER="apk"; INSTALLER_ARG="add" ;;
      fedora | centos | rhel)
        for _pm_cmd in dnf yum; do
          command -v "${_pm_cmd}" >/dev/null 2>&1 && INSTALLER="${_pm_cmd}"
        done
        INSTALLER_ARG="install"
        ;;
    esac
    ;;
  Darwin)
    INSTALLER="brew"
    INSTALLER_ARG="install"
    ;;
esac

"${INSTALLER:?No known installer selected}" ${INSTALLER_ARG} "${PACKAGES}"
```

Note: `${INSTALLER_ARG}` is intentionally unquoted here so its
space-separated arguments expand into multiple words.

## case over test / [ ]

Prefer `case` statements over `test`/`[ ]` for branching. `case`
is faster (no subprocess), cleaner, and handles patterns natively.

```sh
# Preferred
case "${answer}" in
  [yY] | [yY][eE][sS]) confirm ;;
  *) abort ;;
esac

# Avoid
if [ "${answer}" = "y" ] || [ "${answer}" = "Y" ]; then
  confirm
fi
```

## Formatting: shfmt -p -i 2 -ci

All scripts must be formatted with:

```sh
shfmt -p -i 2 -ci -w script.sh
```

- `-p` POSIX mode (no Bash extensions)
- `-i 2` two-space indent
- `-ci` indent `case` label bodies

Run from the repository root:

```sh
# Check all scripts
shfmt -p -i 2 -ci -d scripts/

# Apply formatting in-place
shfmt -p -i 2 -ci -w scripts/*.sh
```

## Checklist

- [ ] Library: no execute bit, no `main()`, `__`-guard present
- [ ] Executable: starts with preamble, ends with `main "${@}"`
- [ ] No top-level logic (only declarations, source, `main "${@}"`)
- [ ] `depcheck()` present when external tools are required
- [ ] `usage()` present and accepts `-h` / `usage`/`help` variants
- [ ] `-x`/`-t` flags supported and enable xtrace
- [ ] Non-modified globals are `readonly`
- [ ] Platform branching uses `uname -s` + INSTALLER pattern
- [ ] `case` used instead of `[ ]` for branching
- [ ] `shfmt -p -i 2 -ci -d` reports no diff
