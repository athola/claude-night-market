---
module: transmute-audit
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 600
tags: [transmute, unsafe, undefined-behavior, layout, bytemuck]
---

# Transmute Audit

`mem::transmute` reinterprets the bytes of one type as another with no
layout check. When the source and target layouts disagree it produces an
invalid value, which is undefined behavior. This dimension flags every
`transmute` and `transmute_copy` so the reviewer can confirm a typed,
checked conversion is not the better tool.

## What This Detects

The analyzer (`analyze_transmute_safety`) flags two shapes:

1. **`transmute`**: a `transmute(...)` or `transmute::<A, B>(...)` call,
   whether written `mem::transmute`, `std::mem::transmute`, or an
   imported bare `transmute`. The call reinterprets bytes with only a
   compile-time size-equality check.
2. **`transmute_copy`**: a `transmute_copy(&src)` call. It does not even
   require the sizes to match and reads through a reference, so it can
   read past the end of the source.

A method call (`pipeline.transmuter(x)`) and any longer identifier are
left alone: the regex requires a call or turbofish directly after the
name and a non-`.` character before it.

## Why `transmute` Hides Bugs

The Rust Reference lists "producing an invalid value" under behavior
considered undefined (`src/behavior-considered-undefined.md`), and a
transmute across mismatched layouts does exactly that. The
`std::mem::transmute` documentation calls it "incredibly unsafe" and
spells out the traps: differing alignment, niche-optimized layouts
(`Option<&T>`), uninitialized padding, and lifetimes invented from
nothing. None of this is checked beyond size equality, so a transmute
reads as deliberate even when the layouts have silently drifted apart.

## The Fix

```rust
// Flag: reinterpret integer bits as a float
let f: f32 = unsafe { mem::transmute(bits) };
// Checked: a named, total operation with no unsafe
let f = f32::from_bits(bits);

// Flag: bytes to a struct
let header: Header = unsafe { mem::transmute(buf) };
// Checked: validated, alignment-safe plain-old-data conversion
let header: Header = bytemuck::pod_read_unaligned(&buf);

// Numbers <-> bytes use the explicit endian methods
let n = u32::from_le_bytes(buf);   // not transmute(buf)
let buf = n.to_le_bytes();         // not transmute(n)
```

Reach for `from_bits`/`to_bits` and `from_le_bytes`/`to_le_bytes` for
numbers, `bytemuck`/`zerocopy` for plain-old-data structs, `as` or
`.cast()` for pointers, and `From`/`TryFrom` for ordinary conversions.
Keep `transmute` only where no safe operation exists, and pair it with a
`// SAFETY:` comment proving the layouts match.

## Exclusions (Not Flagged)

- **Method calls**: `value.transmute(...)` is a user method, not the std
  function.
- **Longer identifiers**: `transmuter(...)`, `transmute_foo(...)` are not
  the `transmute` call (the name is not followed by a call or turbofish).
- **Comments**: a `transmute` shown in a `//` comment is not code.

## Related Clippy Lints

| Lint | Detects |
|------|---------|
| `clippy::transmute_int_to_float` | Integer bits transmuted to a float |
| `clippy::transmute_ptr_to_ref` | Pointer transmuted to a reference |
| `clippy::transmute_bytes_to_str` | Bytes transmuted to `&str` |
| `clippy::useless_transmute` | A transmute that `From`/`as` replaces |
| `clippy::transmute_undefined_repr` | Transmute across unspecified `repr` |

## Output Section

```markdown
## Transmute Audit
### Issues Found
- [file:line] `mem::transmute` reinterprets bytes with no layout check;
  prefer `f32::from_bits` / `from_le_bytes` / `bytemuck`
  (clippy::transmute_int_to_float)
- [file:line] `transmute_copy` skips the size check and can over-read;
  use a typed conversion or audited `ptr::read` (clippy::transmute_copy)
```

## Exit Criteria

- [ ] `mem::transmute(...)` and `transmute::<A, B>(...)` calls are flagged
  as `transmute`
- [ ] `transmute_copy(...)` is flagged separately as the more dangerous
  sibling
- [ ] Method calls (`x.transmute(...)`) and longer identifiers
  (`transmuter(...)`) are not flagged
- [ ] A `transmute` inside a `//` comment is not flagged
- [ ] Each finding names a typed alternative (`from_bits`,
  `from_le_bytes`, `bytemuck`, `TryFrom`) and the clippy lint
