---
module: repr-packed-audit
category: rust-review
dependencies: [Read, Grep]
estimated_tokens: 550
tags: [repr, packed, alignment, unaligned, layout]
---

# Repr Packed Audit

`#[repr(packed)]` removes the padding that keeps struct fields naturally
aligned. Borrowing a field of a packed struct then produces an unaligned
reference, which is undefined behavior. This dimension flags every packed
representation so the reviewer can confirm field access copies out rather
than borrows in place.

## What This Detects

The analyzer (`analyze_repr_packed`) flags any `repr` attribute whose
parentheses contain the `packed` token:

- `#[repr(packed)]`
- `#[repr(C, packed)]`
- `#[repr(packed(2))]`

A `#[repr(C)]` or `#[repr(transparent)]` attribute keeps natural
alignment and is left alone. A `repr` shown in a comment is not an
attribute and is skipped.

## Why Packed Fields Are Dangerous

The Rust Reference type-layout chapter (`src/type-layout.md`) defines the
`packed` representation: it lowers the struct alignment to the given value
(default `1`) and drops inter-field padding. A field can then sit at an
address that does not satisfy its own alignment. Creating a reference to
such a field (`&s.field`, or implicitly when calling a `&self` method on
it, or via `println!("{}", s.field)`) is instant undefined behavior, and
the compiler enforces this through the `unaligned_references` lint, which
is a hard error rather than a warning.

The packed layout itself is legitimate (wire formats, hardware registers,
FFI structs). The hazard is in how fields are read after the fact.

## The Fix

```rust
#[repr(C, packed)]
struct Header {
    tag: u8,
    len: u32,   // not 4-byte aligned inside the packed struct
}

// Flag: borrowing a packed field is UB
let n = &header.len;            // unaligned reference

// Checked: copy the field into a local first (the field is Copy)
let len = header.len;           // reads by value, no reference taken
let n = &len;

// When you must take the address, use the raw-pointer macros, which do
// not create a reference, then read unaligned.
let p = std::ptr::addr_of!(header.len);
let len = unsafe { p.read_unaligned() };
```

Copy `Copy` fields out by value before borrowing, use
`ptr::addr_of!` / `read_unaligned` when you need the address, and keep
`#[repr(packed)]` only where an external format dictates the layout. If
the only goal is a stable field order, `#[repr(C)]` without `packed`
keeps alignment intact.

## Exclusions (Not Flagged)

- **`#[repr(C)]`**: defines field order but keeps natural alignment.
- **`#[repr(transparent)]`**: a single-field wrapper with the field's own
  layout.
- **Comments**: a `repr` shown in a `//` comment is not an attribute.

## Related Lints

| Lint | Detects |
|------|---------|
| `unaligned_references` | A reference to a packed field (hard error) |
| `clippy::transmute_undefined_repr` | Transmute across unspecified repr |

## Output Section

```markdown
## Repr Packed Audit
### Issues Found
- [file:line] `#[repr(packed)]` under-aligns fields; borrowing one
  (`&s.field`) is undefined behavior. Copy the field into a local first
  or use `ptr::addr_of!` + `read_unaligned` (unaligned_references)
```

## Exit Criteria

- [ ] `#[repr(packed)]`, `#[repr(C, packed)]`, and `#[repr(packed(2))]`
  are flagged
- [ ] `#[repr(C)]` and `#[repr(transparent)]` are not flagged
- [ ] A `repr` inside a `//` comment is not flagged
- [ ] Each finding explains the unaligned-reference hazard and names the
  copy-out / `addr_of!` alternative
