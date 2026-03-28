# Session Replay

Convert a Claude Code or Codex session JSONL file into an
animated replay of the conversation. Supports GIF, MP4,
and WebM output formats. Auto-detects the session format
(Claude Code or Codex) from file content.

## Usage

```bash
/session-replay [session-path] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `session-path` | Path to session JSONL file (default: most recent) |

## Options

| Option | Description |
|--------|-------------|
| `--session-format` | Input session format: `claude`, `codex`, or auto-detect (default: auto) |
| `--show` | Layers to include: `user`, `assistant`, `tools`, `thinking` (default: `user,assistant,tools`) |
| `--turns` | Turn range: `1-5` or `3` (default: all) |
| `--output` | Output file path (default: `session-replay.gif`) |
| `--format` | Output format: `gif`, `mp4`, `webm` (default: from `--output` extension) |
| `--theme` | VHS terminal theme (default: `Dracula`) |
| `--speed` | Timing multiplier (default: `1.0`) |
| `--max-duration` | Max GIF duration in seconds (default: none) |
| `--cols` | Text wrapping width in chars (default: `80`) |
| `--rows` | Text truncation height in lines (default: `24`) |

## Workflow

1. Invoke `Skill(scribe:session-replay)` to run the full
   pipeline: parse session, generate tape, render GIF
2. If no session path given, list recent sessions from
   `~/.claude/projects/` for the user to pick
3. Show session date and first user message for confirmation
4. Parse, generate tape, render via `Skill(scry:vhs-recording)`

## Examples

```bash
# Replay most recent session
/session-replay

# Replay specific session file
/session-replay ~/.claude/projects/.../session.jsonl

# Show only user and assistant turns, first 5 turns
/session-replay --show user,assistant --turns 1-5

# Include Claude's thinking in the replay
/session-replay --show user,assistant,tools,thinking

# Custom theme and faster playback
/session-replay --theme "Solarized Dark" --speed 1.5

# Cap GIF duration at 30 seconds
/session-replay --output demo.gif --max-duration 30

# Output as MP4 video
/session-replay --output demo.mp4

# Output as WebM video
/session-replay --format webm

# Override extension with explicit format
/session-replay --output replay.gif --format mp4

# Replay a Codex session (auto-detected)
/session-replay ~/.codex/sessions/latest.jsonl

# Force Codex format parsing
/session-replay session.jsonl --session-format codex
```

## Supported Formats

VHS supports three output formats, selected by the file
extension in `--output` or explicitly via `--format`:

- **gif** -- animated GIF (default), good for docs and READMEs
- **mp4** -- H.264 video, smaller files for longer replays
- **webm** -- VP8/VP9 video, open format for web embedding

SVG output is not supported by VHS and is not available.

## Output

```
Parsed 42 turns from session (12 user, 15 assistant, 15 tools)
Generated tape: /tmp/session-replay-1711234567.tape
Rendering via scry...
Done: session-replay.mp4 (18s, 960x540)
```

## See Also

- `Skill(scribe:session-replay)` -- full skill reference
- `Skill(scry:vhs-recording)` -- terminal recording
- `/session-to-post` -- convert sessions to blog posts
