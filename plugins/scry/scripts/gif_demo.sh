#!/usr/bin/env bash
# Generate a sample video and convert it to a GIF, then report both sizes.
# Usage: gif_demo.sh [-h] [-x|-t]
set -euo pipefail

MYDIR="${0%/*}"
readonly MYDIR

REQUIRED_DEPENDENCIES="ffmpeg ffprobe mktemp du cut"
readonly REQUIRED_DEPENDENCIES

XTRACE=0

# The plugin is installed on its own, so the repository's
# scripts/logging.sh is not on disk beside it. This is the same
# interface at level 1: informational output on stdout, errors on
# stderr, and no bare echo anywhere.
log() {
  _log_level=1
  case "${1:-}" in
    [0-9])
      _log_level="${1}"
      shift
      ;;
  esac
  case "${_log_level}" in
    4 | 5) printf '[ERROR] %s\n' "${*}" >&2 ;;
    2 | 3) printf '[WARN]  %s\n' "${*}" >&2 ;;
    *) printf '[INFO]  %s\n' "${*}" ;;
  esac
}

usage() {
  log "Usage: ${MYDIR%/}/gif_demo.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '\nEnvironment overrides:\n'
  printf '  TMP_DIR     (default: a fresh mktemp -d directory)\n'
  printf '  INPUT       (default: $TMP_DIR/input.mp4)\n'
  printf '  OUTPUT      (default: $TMP_DIR/output.gif)\n'
  printf '  DURATION    (default: 4)\n'
  printf '  SIZE        (default: 1280x720)\n'
  printf '  INPUT_FPS   (default: 30)\n'
  printf '  GIF_FPS     (default: 10)\n'
  printf '  GIF_WIDTH   (default: 800)\n'
}

# Runs before anything external, so a machine without ffmpeg reports
# the missing utility rather than failing inside mktemp or du.
depcheck() {
  _dc_missing=""
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 ||
      _dc_missing="${_dc_missing:+"${_dc_missing} "}${_dc_util}"
  done
  case "${_dc_missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${_dc_missing}"
  log 5 "Install with your package manager, e.g.: brew install ffmpeg"
  return 1
}

# TMP_DIR wins when the caller sets it; otherwise a fresh private
# directory, because a fixed path lets another user pre-create it.
resolve_paths() {
  TMP_DIR="${TMP_DIR:-$(mktemp -d)}"
  INPUT="${INPUT:-${TMP_DIR%/}/input.mp4}"
  OUTPUT="${OUTPUT:-${TMP_DIR%/}/output.gif}"
  DURATION="${DURATION:-4}"
  SIZE="${SIZE:-1280x720}"
  INPUT_FPS="${INPUT_FPS:-30}"
  GIF_FPS="${GIF_FPS:-10}"
  GIF_WIDTH="${GIF_WIDTH:-800}"
  mkdir -p "${TMP_DIR}"
}

make_input() {
  _mi_path="${1:?No input path provided}"
  if [ -f "${_mi_path}" ]; then
    return 0
  fi
  ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i "testsrc2=size=${SIZE}:rate=${INPUT_FPS}" \
    -t "${DURATION}" -pix_fmt yuv420p "${_mi_path}"
}

make_gif() {
  ffmpeg -y -hide_banner -loglevel error -i "${INPUT}" \
    -vf "fps=${GIF_FPS},scale=${GIF_WIDTH}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
    "${OUTPUT}"
  if [ ! -s "${OUTPUT}" ]; then
    log 5 "GIF generation failed or produced empty file: ${OUTPUT}"
    return 1
  fi
}

report() {
  log "Input:  ${INPUT}"
  log "Output: ${OUTPUT}"
  log "Input size:  $(du -h "${INPUT}" | cut -f1)"
  log "Output size: $(du -h "${OUTPUT}" | cut -f1)"
  log "GIF stream info (width,height,nb_frames):"
  ffprobe -v quiet -select_streams v:0 \
    -show_entries stream=width,height,nb_frames -of csv=p=0 "${OUTPUT}"
}

main() {
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t)
        XTRACE=1
        shift
        ;;
      *)
        log 5 "Unknown argument: ${1}"
        usage
        exit 1
        ;;
    esac
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1
  resolve_paths
  make_input "${INPUT}"
  make_gif
  report
}

main "$@"
