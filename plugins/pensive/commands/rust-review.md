# Rust Review Command

Expert-level Rust audits for safety and correctness.

## Usage

```bash
/rust-review
```

## What It Does

1. **Borrowing & Lifetimes**: Check ownership patterns
2. **Error Handling**: Evaluate Result/Option usage
3. **Concurrency**: Review async and sync primitives
4. **Unsafe & FFI**: Audit unsafe blocks
5. **Traits & Generics**: Check API design
6. **Cargo Dependencies**: Scan for issues
7. **Idiomatic Type Use**: Conversions (`From`/`TryFrom` over
   `Into`/`TryInto`, no discarded `try_into().unwrap()`), deref-coercion
   parameters (`&str`/`&[T]`/`&Path` over `&String`/`&Vec<T>`/`&PathBuf`),
   and elision (needless lifetimes, explicit `-> ()` unit returns)

## Scope

- Ownership correctness
- Memory safety
- Thread safety
- FFI boundaries
- Dependency security

## Output

- Safety audit results
- Concurrency analysis
- Unsafe block documentation
- Dependency scan
- Recommendations
