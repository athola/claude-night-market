---
parent_skill: pensive:shell-review
module: safety-patterns
description: POSIX safety rules: no echo, braced vars, :? expansion, cd subshells
tags: [safety, posix, quoting, expansion, cd]
---

# Shell Safety Patterns

## No echo: use log() or printf

All output must go through `log()` from `scripts/logging.sh` or via
`printf(1)`. The only exception is `usage()` body lines (after
the first), where `printf` is used directly.

Detection:

```sh
# Bare echo calls in non-comment lines
rg -n '^\s*echo\s' scripts/ .githooks/ plugins/*/hooks/
# fallback: grep -rn '^\s*echo\s' scripts/ .githooks/
```

Fix: replace `echo "msg"` with `log "msg"` or `printf '%s\n' "msg"`.

## Braced variable references

Every variable reference must use the braced form `${VAR}`, not
bare `$VAR`. This avoids surprises with adjacent text and is
required for consistent ShellCheck compliance.

Detection:

```sh
rg -n '\$[A-Za-z_][A-Za-z_0-9]*[^}]' scripts/
```

Fix: `$VAR` → `${VAR}`, `$1` → `${1}`, `$@` → `"${@}"`.

## :? expansion instead of branching on unset

Never branch on an unset variable before triggering an exit-path.
Use `${VAR:?message}` so the shell emits the message and exits
immediately when the variable is unset or empty.

```sh
# Bad — branches on unset, then exits
if [ -z "${DIR}" ]; then
  log 4 "DIR is unset"
  exit 1
fi

# Good — parameter expansion handles it
process_dir "${DIR:?DIR must be set}"
```

Detection:

```sh
rg -n '\[ -z.*\$\{?\w' scripts/   # [ -z "$VAR" ] before exit
```

## cd inside a subshell

Every `cd` must be wrapped in a subshell so that the change of
directory does not persist and a failed `cd` cannot leave the
script in the wrong directory.

```sh
# Bad — cd leaks to caller scope; fails silently without set -e
cd "${build_dir}"
make clean

# Good — scoped and guarded
(cd "${build_dir:?No build dir}" && make clean)
```

Detection:

```sh
rg -n '^\s*cd\s+[^(]' scripts/     # cd not wrapped in (
```

## Source relative to script location

External files must be sourced relative to the script's own
location, not the caller's working directory.

```sh
# Bad — breaks when invoked from any other directory
. ./logging.sh

# Good — always resolves from the script's directory
MYDIR="${0%/*}"
. "${MYDIR%/}/logging.sh"
```

Use `${0%/*}` (POSIX parameter expansion) instead of `dirname "$0"`.

## No basename or dirname

Use POSIX parameter expansion instead of the external commands
`basename` and `dirname`.

| Command | Expansion |
|---------|-----------|
| `basename "$path"` | `"${path##*/}"` |
| `dirname "$path"` | `"${path%/*}"` |
| `basename "$path" .ext` | `f="${path##*/}"; "${f%.ext}"` |

Detection:

```sh
rg -n '\bbasename\b|\bdirname\b' scripts/
```

## Library loading check form

When a script must verify a library was sourced, use the canonical
`case` form, not `[ -z … ]` or `[ -n … ]`:

```sh
# Required form — distinguishes unset/empty/loaded
case "${__logging_loaded:-NULL}" in
  1) : ;;    # loaded
  *) printf 'logging.sh not loaded\n' >&2; exit 1 ;;
esac
```

Detection for non-canonical form:

```sh
rg -n '\[ -[zn].*__\w+_loaded' scripts/
```

## set -e / set -u in libraries

Files meant to be sourced must not enable `set -e` or `set -u`
because the flags leak to the caller and can exit the caller's
session on unrelated commands.

Detection:

```sh
rg -n '^set -[eu]' scripts/logging.sh
```

## printf over echo

For data output and multi-line messages, prefer `printf` with a
fixed format string. Never build the format string from untrusted
text.

```sh
# Bad — echo interprets escape sequences inconsistently
echo "Processing ${file}"

# Good — fixed format, no interpretation surprises
printf 'Processing %s\n' "${file}"
```

For logging through `log()`, pass the message as an argument.
`log()` uses `printf` internally.

## Checklist

- [ ] No raw `echo` calls (use `log()` or `printf`)
- [ ] All variables in braced form `${VAR}`
- [ ] Unset required variables caught with `:?` expansion
- [ ] Every `cd` is wrapped in a subshell
- [ ] External files sourced via `${0%/*}` relative path
- [ ] No `basename`/`dirname`; use param expansion
- [ ] Library guard uses `case "${__lib_loaded:-NULL}" in`
- [ ] Library scripts have no `set -e` or `set -u`
