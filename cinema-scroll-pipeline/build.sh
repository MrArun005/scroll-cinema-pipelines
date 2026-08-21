#!/usr/bin/env bash
#
# build.sh — scene.json in, standalone cinematic scroll site out.
#
#   ./build.sh examples/mostar/scene.json out/mostar
#   ./build.sh scene.json out/ --serve
#
# Options
#   --serve       serve the result on http://127.0.0.1:PORT after building
#   --port N      port for --serve (default 8123)
#   --open        open the served page in the default browser

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCENE="${1:?usage: build.sh scene.json out-dir [--serve] [--port N] [--open]}"
OUT="${2:?missing output directory}"
shift 2

SERVE=0
PORT=8123
OPEN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --serve) SERVE=1; shift;;
    --port) PORT="$2"; shift 2;;
    --open) SERVE=1; OPEN=1; shift;;
    *) echo "unknown option: $1"; exit 1;;
  esac
done

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null || { echo "$PY not found (set PYTHON=... to override)"; exit 1; }
[ -f "$SCENE" ] || { echo "no such scene: $SCENE"; exit 1; }

echo
echo "  COMPILING  $SCENE"
"$PY" "$HERE/scripts/compile.py" "$SCENE" "$OUT"

# report weight: local files on disk, remote layers over the network
LOCAL=$(find "$OUT" -type f -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
echo "  local       $(( LOCAL / 1024 )) KB on disk"

REMOTE=$(grep -oE 'src="https://[^"]+"' "$OUT/index.html" 2>/dev/null | sed 's/src="//;s/"$//' | sort -u || true)
if [ -n "$REMOTE" ]; then
  N=$(echo "$REMOTE" | wc -l | tr -d ' ')
  echo "  remote      $N layer URL(s) — not bundled, fetched at runtime"
fi

echo
echo "  DONE  $OUT/index.html"

if [ "$SERVE" = "1" ]; then
  echo "        serving on http://127.0.0.1:${PORT}/  (ctrl-c to stop)"
  [ "$OPEN" = "1" ] && { command -v explorer.exe >/dev/null && explorer.exe "http://127.0.0.1:${PORT}/" || true; }
  cd "$OUT" && exec "$PY" -m http.server "$PORT" --bind 127.0.0.1
fi
echo
