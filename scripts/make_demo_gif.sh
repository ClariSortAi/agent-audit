#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_GIF="${1:-$ROOT_DIR/artifacts/demo.gif}"
WORK_DIR="${2:-$ROOT_DIR/artifacts/.demo_work}"
CONFIG_HOME="$ROOT_DIR/.tmp-config"
FRAME_RATE="${FRAME_RATE:-0.7}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing dependency: $1" >&2
    exit 1
  fi
}

require_cmd asciinema
require_cmd termtosvg
require_cmd ffmpeg
require_cmd convert

mkdir -p "$WORK_DIR" "$CONFIG_HOME" "$(dirname "$OUT_GIF")"
rm -f "$WORK_DIR/demo.cast"
rm -rf "$WORK_DIR/frames" "$WORK_DIR/frames_light" "$WORK_DIR/png"
mkdir -p "$WORK_DIR/frames" "$WORK_DIR/frames_light" "$WORK_DIR/png"

DEMO_SCRIPT="$WORK_DIR/demo_script.sh"
cat > "$DEMO_SCRIPT" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT_DIR"
printf '\n$ agent-audit scan ~/.openclaw --format table\n\n'
.venv/bin/agent-audit scan ~/.openclaw --format table
sleep 2
printf '\n$ agent-audit compare ~/.openclaw tests/fixtures/codex_scoped --format markdown\n\n'
.venv/bin/agent-audit compare ~/.openclaw tests/fixtures/codex_scoped --format markdown
sleep 2
printf '\n$ agent-audit monitor --exec "openclaw --help" --duration 2 --format json\n\n'
.venv/bin/agent-audit monitor --exec "openclaw --help" --duration 3 --format json
sleep 2
SCRIPT
chmod +x "$DEMO_SCRIPT"

XDG_CONFIG_HOME="$CONFIG_HOME" asciinema rec -q --overwrite --cols 120 --rows 36 \
  -c "ROOT_DIR=$ROOT_DIR bash $DEMO_SCRIPT" "$WORK_DIR/demo.cast"

termtosvg render "$WORK_DIR/demo.cast" "$WORK_DIR/frames" -s -t solarized_light >/dev/null

for svg in "$WORK_DIR"/frames/*.svg; do
  base="$(basename "$svg" .svg)"
  perl -0pe '
    s/(\.foreground\s*\{fill:\s*)#[0-9a-fA-F]{6}(;\s*\})/${1}#000000$2/g;
    s/(\.background\s*\{fill:\s*)#[0-9a-fA-F]{6}(;\s*\})/${1}#ffffff$2/g;
    s/(\.color0\s*\{fill:\s*)#[0-9a-fA-F]{6}(;\s*\})/${1}#ffffff$2/g;
    s/(\.color([1-9]|1[0-5])\s*\{fill:\s*)#[0-9a-fA-F]{6}(;\s*\})/${1}#000000$3/g;
  ' "$svg" > "$WORK_DIR/frames_light/${base}.svg"
  convert -background '#ffffff' "$WORK_DIR/frames_light/${base}.svg" -alpha remove -alpha off "$WORK_DIR/png/${base}.png"
done

ffmpeg -y -framerate "$FRAME_RATE" -i "$WORK_DIR/png/termtosvg_%05d.png" \
  -vf "scale=1200:-1:flags=lanczos,format=rgb24,split[s0][s1];[s0]palettegen=max_colors=256:stats_mode=full:reserve_transparent=0[p];[s1][p]paletteuse=dither=none:alpha_threshold=255" \
  -gifflags -transdiff \
  "$OUT_GIF" >/dev/null 2>&1

echo "generated: $OUT_GIF"
