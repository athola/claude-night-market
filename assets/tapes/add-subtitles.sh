#!/usr/bin/env bash
# Burn a timed bottom-band narration onto skills-showcase.gif.
#
# The subtitle plan below is aligned to the *original* tape
# (skills-showcase.tape) which drives a real `claude` session.
# Timestamps map to the tape's typing time + Sleep beats, not
# to Claude's response wording (responses are non-deterministic;
# the narration describes the workflow, not the literal output).
#
# After regenerating the GIF with VHS, re-run this script to
# re-apply the subtitle band.
#
# Usage:
#   bash assets/tapes/add-subtitles.sh
#   bash assets/tapes/add-subtitles.sh path/to/in.gif path/to/out.gif

set -eu

INPUT="${1:-assets/gifs/skills-showcase.gif}"
OUTPUT="${2:-assets/gifs/skills-showcase.gif}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
TMP_GIF="$TMPDIR/captioned.gif"

# Pick a font that ships on most Linux boxes; fall back gracefully.
FONT_CANDIDATES=(
  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
  "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
)
FONT=""
for f in "${FONT_CANDIDATES[@]}"; do
  if [[ -f "$f" ]]; then FONT="$f"; break; fi
done
if [[ -z "$FONT" ]]; then
  echo "ERROR: no candidate font found; install fonts-dejavu" >&2
  exit 1
fi

# Subtitle plan: start_sec | end_sec | text
# Aligned to skills-showcase.tape (~130s total: typing at 100ms/char
# plus the script's Sleep directives).
SUBS=(
  "0.0:5.0:Open the night-market repo in a terminal"
  "5.0:10.0:Set the stage — Claude CLI demonstration"
  "10.0:15.0:Announce: starting an interactive Claude session"
  "15.0:19.0:Launch claude with --dangerously-skip-permissions"
  "19.0:28.0:Claude boots — 23 plugins, 188 skills auto-loaded"
  "28.0:38.0:Ask: what skills does parseltongue offer?"
  "38.0:73.0:Claude auto-discovers and summarizes parseltongue skills"
  "73.0:84.0:Ask: how do I weave these into my workflow?"
  "84.0:119.0:Claude shows real-world skill composition in action"
  "119.0:125.0:Exit the interactive session"
  "125.0:131.0:Powered by claude-night-market — no manual /skill needed"
)

# drawtext escaping for ffmpeg's filtergraph syntax.
escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//:/\\:}"
  s="${s//\'/\\\\\\\'}"
  s="${s//%/\\%}"
  printf '%s' "$s"
}

filters=()
for sub in "${SUBS[@]}"; do
  IFS=':' read -r start end text <<<"$sub"
  text_esc="$(escape "$text")"
  filters+=("drawtext=fontfile=${FONT}:text='${text_esc}':fontcolor=#ffffff:fontsize=14:x=(w-text_w)/2:y=h-26:box=1:boxcolor=0x000000@0.78:boxborderw=8:enable='between(t,${start},${end})'")
done

IFS=','; drawtext_chain="${filters[*]}"; unset IFS

# Palette regen so the band doesn't quantize ugly against the
# Catppuccin Mocha background.
vf="${drawtext_chain},split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a"

echo "Burning subtitles into $INPUT…"
ffmpeg -y -hide_banner -loglevel error -i "$INPUT" -vf "$vf" -loop 0 "$TMP_GIF"

mv "$TMP_GIF" "$OUTPUT"
size=$(du -h "$OUTPUT" | cut -f1)
echo "✓ Wrote $OUTPUT ($size)"
