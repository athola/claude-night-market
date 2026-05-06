# Session to Post

Convert the current session's work into a shareable blog post, case study, or social thread.

## Usage

```bash
/session-to-post [format] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `format` | Output format: `blog` (default), `case-study`, `thread` |

## Options

| Option | Description |
|--------|-------------|
| `--output` | Output file path (default: `docs/posts/`) |
| `--since` | Git ref or date for session start (default: last 20 commits) |
| `--record` | Generate scry recordings: `terminal`, `browser`, `both`, `none` (default: `none`) |
| `--verify` | Run proof-of-work on all claims (default: true) |

## Workflow

1. Invoke `Skill(scribe:session-to-post)` to run the full pipeline
2. If `--record terminal`: invoke `Skill(scry:vhs-recording)` for test/build GIFs
3. If `--record browser`: invoke `Skill(scry:browser-recording)` for app demo GIFs
4. If `--record both`: invoke both, then `Skill(scry:media-composition)` to combine
5. Invoke `Skill(imbue:proof-of-work)` to verify all claims
6. Invoke `Skill(scribe:slop-detector)` for final quality pass

## Examples

```bash
# Quick blog post from recent work
/session-to-post

# Case study with terminal recording
/session-to-post case-study --record terminal

# Social thread, work since a specific commit
/session-to-post thread --since abc1234

# Blog post with all recordings, custom output
/session-to-post blog --record both --output blog/q2-port.md
```

## Output

Generated file with quality report:

```
Generated: docs/posts/2026-03-26-rewriting-quake2-in-rust.md (1,180 words)

Quality:
- Slop score: 1.2 (clean)
- Verifiable claims: 8, all PASS
- Recordings: tests.gif, demo.gif

Assets written to docs/posts/assets/
```

## See Also

- `Skill(scribe:session-to-post)`: full skill reference
- `Skill(scry:vhs-recording)`: terminal recordings
- `Skill(scry:browser-recording)`: browser recordings
- `Skill(imbue:proof-of-work)`: claim verification
- `/doc-generate`: general documentation generation
