#!/usr/bin/env bash
# One-time setup for a fresh container. Safe to re-run.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v ffmpeg >/dev/null || { echo "ffmpeg missing (apt-get install -y ffmpeg)"; exit 1; }
python3 -c "import faster_whisper, numpy" 2>/dev/null || pip install --break-system-packages -q faster-whisper numpy
# OpenCV 5 dropped the Haar face detector used for framing -> pin 4.x
python3 -c "import cv2; assert hasattr(cv2,'CascadeClassifier')" 2>/dev/null || pip install --break-system-packages -q "opencv-python-headless<5"
# segmentation (person cut-out) needs mediapipe 0.10.14, which bundles its model but only ships for Python <=3.12
if ! /opt/vw-seg/bin/python -c "import mediapipe" 2>/dev/null; then
  python3.12 -m venv /opt/vw-seg && /opt/vw-seg/bin/pip install -q "mediapipe==0.10.14" "opencv-python-headless<5" "numpy<2"
fi
node -e "require('playwright')" 2>/dev/null || { echo "Playwright (node) not found"; exit 1; }
ls "$HERE"/renderer/fonts/*.woff2 >/dev/null 2>&1 || { echo "fonts missing in renderer/fonts"; exit 1; }
python3 "$HERE/scripts/make_sfx.py" --keep-existing
# Whisper model reachability (huggingface.co must be allowed by the network policy, or models/ pre-filled)
if ls "$HERE"/models/models--Systran--faster-whisper-* >/dev/null 2>&1; then
  echo "Whisper model cache present in models/"
elif curl -sS -m 10 -o /dev/null -w "%{http_code}" https://huggingface.co/api/models/Systran/faster-whisper-small 2>/dev/null | grep -q 200; then
  echo "huggingface.co reachable - the model downloads on first transcription"
else
  echo "WARNING: huggingface.co is blocked and no model is cached - transcription will fail."
  echo "         Allow huggingface.co in the environment's network settings (Allowed domains)."
fi
echo "Setup OK"
