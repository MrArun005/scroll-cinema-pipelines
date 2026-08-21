#!/usr/bin/env bash
#
# build.sh — video in, finished single-file scroll-scrub site out.
#
#   ./build.sh input.mp4 site.html
#   ./build.sh input.mp4 site.html --title "Held" --budget 5 --delogo x=1132:y=576:w=54:h=52
#
# Keeps the source resolution. Fits the budget by lowering frame COUNT, never
# by downscaling, because resolution is what you see and framerate is what the
# easing hides.
#
# Options
#   --budget N     target output size in MB (default 5)
#   --delogo BOX   inpaint a watermark: x=..:y=..:w=..:h=..
#                  find the box with:  analyse.py in.mp4 --corners
#   --crop BOX     explicit crop w:h:x:y (e.g. portrait reframe)
#   --title TEXT   page <title> and hero wordmark
#   --quality N    WebP quality 0-100 (default 82)
#   --fps N        force a framerate instead of deriving one
#   --no-grade     skip colour grading
#   --keep-frames  leave the frame directory behind for inspection

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IN="${1:?usage: build.sh input.mp4 output.html [options]}"
OUT="${2:?missing output .html}"
shift 2

BUDGET=5; QUALITY=82; TITLE="Scroll"; DELOGO=""; CROPBOX=""; FORCE_FPS=""
GRADE_ON=1; KEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --budget) BUDGET="$2"; shift 2;;
    --delogo) DELOGO="$2"; shift 2;;
    --crop) CROPBOX="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --quality) QUALITY="$2"; shift 2;;
    --fps) FORCE_FPS="$2"; shift 2;;
    --no-grade) GRADE_ON=0; shift;;
    --keep-frames) KEEP=1; shift;;
    *) echo "unknown option: $1"; exit 1;;
  esac
done

command -v ffmpeg >/dev/null || { echo "ffmpeg not found"; exit 1; }
[ -f "$IN" ] || { echo "no such file: $IN"; exit 1; }

echo
echo "  ANALYSING  $IN"
eval "$(python3 "$HERE/scripts/analyse.py" "$IN" --emit)"
python3 "$HERE/scripts/analyse.py" "$IN"

[ "$CUTS" != "0" ] && echo "  Proceeding anyway, but expect the cuts to read as broken frames."
[ "$GRADE_ON" = "0" ] && GRADE=""

# ---- build the filter chain -------------------------------------------------
CHAIN=""
[ -n "$DELOGO" ] && CHAIN="delogo=${DELOGO},"
[ -n "$CROPBOX" ] && CHAIN="${CHAIN}crop=${CROPBOX},"
CHAIN_TAIL=""
[ -n "$GRADE" ] && CHAIN_TAIL=",${GRADE}"

# ---- probe cost per frame at full resolution --------------------------------
PROBE_DIR="$(mktemp -d)"
ffmpeg -y -v error -i "$IN" -vf "${CHAIN}fps=2${CHAIN_TAIL}" \
  -c:v libwebp -quality "$QUALITY" -compression_level 6 -an "$PROBE_DIR/p_%03d.webp"
PN=$(ls "$PROBE_DIR" | wc -l | tr -d ' ')
PB=$(du -bc "$PROBE_DIR"/*.webp | tail -1 | cut -f1)
PER=$(( PB / PN ))
rm -rf "$PROBE_DIR"

# base64 inflates by 4/3; leave 120 KB for the page itself
CAP=$(python3 -c "print(int(($BUDGET*1048576 - 120000) * 3 / 4))")
MAXF=$(( CAP / PER ))
[ "$MAXF" -lt 24 ] && MAXF=24

if [ -n "$FORCE_FPS" ]; then
  FPS="$FORCE_FPS"
else
  FPS=$(python3 -c "
import math
fps = min($MAXF / $DUR, $SRC_FPS)
print(max(6, math.floor(fps)))")
  if [ "$FPS" -lt "$FPS_MIN" ]; then
    echo
    echo "  NOTE: budget allows only ${FPS}fps but this motion wants ${FPS_MIN}fps."
    echo "        Raise --budget for smoother scrubbing."
  fi
fi

echo
echo "  BUILDING"
echo "    resolution  ${SRC_W}x${SRC_H} (unchanged)"
echo "    quality     WebP ${QUALITY}   ~$(( PER / 1024 )) KB/frame"
echo "    framerate   ${FPS}fps"

FRAMES="$(mktemp -d)"
ffmpeg -y -v error -i "$IN" -vf "${CHAIN}fps=${FPS}${CHAIN_TAIL}" \
  -c:v libwebp -quality "$QUALITY" -compression_level 6 -an "$FRAMES/f_%03d.webp"

N=$(ls "$FRAMES" | wc -l | tr -d ' ')
RAW=$(du -bc "$FRAMES"/*.webp | tail -1 | cut -f1)
echo "    frames      ${N}   raw $(( RAW / 1024 )) KB"

# ---- assemble ---------------------------------------------------------------
TPL="$(mktemp).html"
sed "s|__TITLE__|${TITLE}|g" "$HERE/template/page.html" > "$TPL"
python3 "$HERE/scripts/embed.py" "$TPL" "$FRAMES" "$OUT" >/dev/null
rm -f "$TPL"

if [ "$KEEP" = "1" ]; then
  mv "$FRAMES" "./frames-$(basename "${OUT%.html}")"
  echo "    frames kept in ./frames-$(basename "${OUT%.html}")"
else
  rm -rf "$FRAMES"
fi

SIZE=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
DEC=$(python3 -c "print(round($SRC_W*$SRC_H*4*$N/1048576))")

echo
echo "  DONE  $OUT   $(( SIZE / 1024 )) KB"
echo "        self-contained: open it directly, no server, no folder"
echo "        ~${DEC} MB decoded in memory"
[ "$DEC" -gt 500 ] && echo "        (over 500 MB — the page trims frames on mobile automatically)"
echo
