#!/opt/vw-seg/bin/python
"""Where is the person in the frame? Coarse occupancy map per clip, from MediaPipe selfie segmentation.

Adds to WORK/layout.json (per clip in clips[], or top level for single-clip videos):
  "occ": 48 rows x 54 cols of floats 0..1 (40 px x 20 px cells) = how often each cell is covered by the person
The renderer uses it to place caption keywords BEHIND the person only where most of the word stays visible.
Usage: body_profile.py WORK
"""
import json, os, sys
import numpy as np
import cv2
import mediapipe as mp

W, H, ROWS, COLS = 1080, 1920, 48, 54
work = sys.argv[1]
lay_p = os.path.join(work, "layout.json")
layout = json.load(open(lay_p))
dur = json.load(open(os.path.join(work, "segments.json")))["duration"]
clips = layout.get("clips") or [{"start": 0.0, "end": dur}]
cap = cv2.VideoCapture(os.path.join(work, "cut.mov"))
fps = cap.get(cv2.CAP_PROP_FPS) or 30
with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as seg:
    for c in clips:
        acc, n = np.zeros((ROWS, COLS), np.float32), 0
        for k in range(12):
            t = c["start"] + (k + 0.5) * (c["end"] - c["start"]) / 12
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
            ok, fr = cap.read()
            if not ok:
                continue
            m = seg.process(cv2.cvtColor(cv2.resize(fr, (W // 4, H // 4)), cv2.COLOR_BGR2RGB)).segmentation_mask
            acc += cv2.resize((m > 0.5).astype(np.float32), (COLS, ROWS), interpolation=cv2.INTER_AREA)
            n += 1
        c["occ"] = np.round(acc / max(1, n), 2).tolist()
if layout.get("clips"):
    layout["clips"] = clips
else:
    layout["occ"] = clips[0]["occ"]
json.dump(layout, open(lay_p, "w"), indent=1)
print("body occupancy map:", len(clips), "clip(s)")
