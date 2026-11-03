#!/usr/bin/env bash
# Video workflow driver. Judgment steps (reviewing cuts, writing the storyboard) happen between commands.
#   ./vw.sh setup                              install deps, fonts check, SFX
#   ./vw.sh prep RAW.mp4 WORKDIR [--language ro] [--model small]
#                                              normalize + framing + transcribe + propose cuts
#   ./vw.sh cut WORKDIR                        apply edit.json (silences + mistakes), lip-sync safe
#   ./vw.sh render WORKDIR OUT.mp4             camera fx + cut-out, graphics layers, SFX, final 1080x1920 encode
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cmd="${1:-}"; shift || true
case "$cmd" in
  setup)  bash "$HERE/scripts/setup.sh" ;;
  prep)
    raw="$1"; work="$2"; shift 2
    python3 "$HERE/scripts/prepare.py" "$raw" "$work"
    python3 "$HERE/scripts/transcribe.py" "$work" "$@"
    python3 "$HERE/scripts/propose_cuts.py" "$work" ;;
  cut)    python3 "$HERE/scripts/cut.py" "$1" ;;
  render)
    /opt/vw-seg/bin/python "$HERE/scripts/body_profile.py" "$1"
    node "$HERE/scripts/render_overlay.cjs" "$1"
    /opt/vw-seg/bin/python "$HERE/scripts/fx.py" "$1"
    python3 "$HERE/scripts/compose.py" "$1" "$2" ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
