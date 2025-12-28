#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Generate a small sample video and convert it to a GIF using temp paths.

Usage:
  gif-demo.sh

Environment overrides:
  TMP_DIR     (default: /tmp/scry-gif-test)
  INPUT       (default: $TMP_DIR/input.mp4)
  OUTPUT      (default: $TMP_DIR/output.gif)
  DURATION    (default: 4)
  SIZE        (default: 1280x720)
  INPUT_FPS   (default: 30)
  GIF_FPS     (default: 10)
  GIF_WIDTH   (default: 800)
EOF
  exit 0
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg is not installed"
  exit 1
fi

TMP_DIR="${TMP_DIR:-/tmp/scry-gif-test}"
INPUT="${INPUT:-$TMP_DIR/input.mp4}"
OUTPUT="${OUTPUT:-$TMP_DIR/output.gif}"

DURATION="${DURATION:-4}"
SIZE="${SIZE:-1280x720}"
INPUT_FPS="${INPUT_FPS:-30}"
GIF_FPS="${GIF_FPS:-10}"
GIF_WIDTH="${GIF_WIDTH:-800}"

mkdir -p "$TMP_DIR"

if [[ ! -f "$INPUT" ]]; then
  ffmpeg -hide_banner -loglevel error \
    -f lavfi -i "testsrc2=size=${SIZE}:rate=${INPUT_FPS}" \
    -t "$DURATION" -pix_fmt yuv420p "$INPUT"
fi

ffmpeg -hide_banner -loglevel error -i "$INPUT" \
  -vf "fps=${GIF_FPS},scale=${GIF_WIDTH}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  "$OUTPUT"

if [[ ! -f "$OUTPUT" ]]; then
  echo "Error: GIF generation failed"
  exit 1
fi

echo "Input:  $INPUT"
echo "Output: $OUTPUT"
echo "Input size:  $(du -h "$INPUT" | cut -f1)"
echo "Output size: $(du -h "$OUTPUT" | cut -f1)"
echo "GIF stream info (width,height,nb_frames):"
ffprobe -v quiet -select_streams v:0 -show_entries stream=width,height,nb_frames -of csv=p=0 "$OUTPUT"
