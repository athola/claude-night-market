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
# Usage: add-subtitles.sh [-h] [-x|-t] [in.gif [out.gif]]
#   bash assets/tapes/add-subtitles.sh
#   bash assets/tapes/add-subtitles.sh path/to/in.gif path/to/out.gif

set -euo pipefail

# A bare name has no slash, and `${0%/*}` would return the name itself.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/../../scripts/logging.sh"

REQUIRED_DEPENDENCIES="ffmpeg mktemp du cut"
readonly REQUIRED_DEPENDENCIES

# SUBTITLE_FONT names a font file directly. Otherwise take the first
# candidate present: common Linux fonts, then fonts every macOS ships.
FONT_CANDIDATES=(
  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
  "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
  "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
  "/System/Library/Fonts/Helvetica.ttc"
)
readonly FONT_CANDIDATES

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
readonly SUBS

XTRACE=0
INPUT="assets/gifs/skills-showcase.gif"
OUTPUT="assets/gifs/skills-showcase.gif"
WORK_DIR=""

usage() {
  log "Usage: ${MYDIR%/}/add-subtitles.sh [-h] [-x|-t] [in.gif [out.gif]]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  in.gif      GIF to caption (default: %s)\n' "${INPUT}"
  printf '  out.gif     Where to write it (default: %s)\n' "${OUTPUT}"
  printf '\nEnvironment overrides:\n'
  printf '  SUBTITLE_FONT  Font file to draw with (default: first candidate found)\n'
}

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

# Prints the font file to draw with.
select_font() {
  local f
  case "${SUBTITLE_FONT:-}" in
    "") ;;
    *)
      if [ ! -f "${SUBTITLE_FONT}" ]; then
        log 5 "SUBTITLE_FONT=${SUBTITLE_FONT} is not a file"
        return 1
      fi
      printf '%s' "${SUBTITLE_FONT}"
      return 0
      ;;
  esac
  for f in "${FONT_CANDIDATES[@]}"; do
    if [ -f "${f}" ]; then
      printf '%s' "${f}"
      return 0
    fi
  done
  log 5 "no candidate font found; install fonts-dejavu or set SUBTITLE_FONT"
  return 1
}

# drawtext escaping for ffmpeg's filtergraph syntax.
escape() {
  local s="${1}"
  s="${s//\\/\\\\}"
  s="${s//:/\\:}"
  s="${s//\'/\\\\\\\'}"
  s="${s//%/\\%}"
  printf '%s' "${s}"
}

# Prints the drawtext chain plus the palette pass for one font.
build_filtergraph() {
  local font_esc sub start end text text_esc drawtext_chain
  local filters=()
  # Quoted and escaped like the text: "Arial Bold.ttf" has a space, and
  # a colon in a path would end the option.
  font_esc="$(escape "${1:?build_filtergraph needs a font}")"
  for sub in "${SUBS[@]}"; do
    IFS=':' read -r start end text <<<"${sub}"
    text_esc="$(escape "${text}")"
    filters+=("drawtext=fontfile='${font_esc}':text='${text_esc}':fontcolor=#ffffff:fontsize=14:x=(w-text_w)/2:y=h-26:box=1:boxcolor=0x000000@0.78:boxborderw=8:enable='between(t,${start},${end})'")
  done

  IFS=','
  drawtext_chain="${filters[*]}"
  unset IFS

  # Palette regen so the band doesn't quantize ugly against the
  # Catppuccin Mocha background.
  printf '%s' "${drawtext_chain},split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a"
}

burn_subtitles() {
  local font vf tmp_gif size
  font="$(select_font)" || return 1
  vf="$(build_filtergraph "${font}")"

  WORK_DIR="$(mktemp -d)"
  trap 'rm -rf "${WORK_DIR}"' EXIT
  tmp_gif="${WORK_DIR}/captioned.gif"

  log "Burning subtitles into ${INPUT}…"
  ffmpeg -y -hide_banner -loglevel error -i "${INPUT}" -vf "${vf}" -loop 0 "${tmp_gif}"

  mv "${tmp_gif}" "${OUTPUT}"
  size="$(du -h "${OUTPUT}" | cut -f1)"
  log "Wrote ${OUTPUT} (${size})"
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
        ;;
      *) break ;;
    esac
    shift
  done
  INPUT="${1:-${INPUT}}"
  OUTPUT="${2:-${OUTPUT}}"

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1
  burn_subtitles
}

main "$@"
