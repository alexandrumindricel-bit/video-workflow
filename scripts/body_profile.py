#!/opt/vw-seg/bin/python
"""Where is the person in the frame? Coarse occupancy map per clip, from MediaPipe selfie segmentation.

Adds to WORK/layout.json (per clip in clips[], or top level for single-clip videos):
  "palette": {"accents": [hex...], "neutral": hex} = dominant colours of the RAW footage (caption colours)
  "occ": 48 rows x 54 cols of floats 0..1 (40 px x 20 px cells) = how often each cell is covered by the person
The renderer uses it to place caption keywords BEHIND the person only where most of the word stays visible.
Usage: body_profile.py WORK
"""
import json, os, sys
import numpy as np
import cv2
import mediapipe as mp

W, H, ROWS, COLS = 1080, 1920, 48, 54


def scene_palette(frames, k=7):
    """Dominant colours of the RAW footage (for caption colours): accents = clearly coloured clusters that are not
    skin, neutral = the most common low-chroma tone. Hex strings, sorted by importance."""
    if not frames:
        return {"accents": [], "neutral": "#7A7A7A"}
    px = np.concatenate([f.reshape(-1, 3) for f in frames]).astype(np.float32)
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    _, lbl, cen = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    share = np.bincount(lbl.ravel(), minlength=k) / len(lbl)
    out_acc, neutrals = [], []
    for i in range(k):
        L, a, b = cen[i][0] * 100 / 255, cen[i][1] - 128, cen[i][2] - 128
        chroma = float(np.hypot(a, b))
        hue = float(np.degrees(np.arctan2(b, a)) % 360)
        bgr = cv2.cvtColor(np.uint8([[cen[i]]]), cv2.COLOR_LAB2BGR)[0, 0]
        hx = "#%02X%02X%02X" % (bgr[2], bgr[1], bgr[0])
        skin = 25 <= hue <= 75 and 8 <= chroma <= 32 and 35 <= L <= 85      # typical skin / hair tones
        if chroma >= 14 and not skin:
            out_acc.append((share[i] * (chroma ** 1.3), hx))
        elif chroma < 10 and 20 < L < 85:
            neutrals.append((share[i], hx))
    # second pass: cluster only clearly coloured pixels (logos, plants, clothes, lights) so small but strong colours
    # are not averaged away by large grey areas
    ch = np.hypot(lab[:, 1] - 128, lab[:, 2] - 128)
    hue_all = np.degrees(np.arctan2(lab[:, 2] - 128, lab[:, 1] - 128)) % 360
    L_all = lab[:, 0] * 100 / 255
    skin_all = (hue_all >= 25) & (hue_all <= 75) & (ch <= 32) & (L_all >= 35) & (L_all <= 85)
    sat = lab[(ch > 22) & ~skin_all]
    if len(sat) > 200:
        k2 = min(5, max(2, len(sat) // 400))
        _, l2, c2 = cv2.kmeans(sat, k2, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0), 3, cv2.KMEANS_PP_CENTERS)
        sh2 = np.bincount(l2.ravel(), minlength=k2) / len(lab)
        for i in range(k2):
            if sh2[i] < 0.002:
                continue
            bgr = cv2.cvtColor(np.uint8([[c2[i]]]), cv2.COLOR_LAB2BGR)[0, 0]
            chroma = float(np.hypot(c2[i][1] - 128, c2[i][2] - 128))
            out_acc.append((sh2[i] * (chroma ** 1.3) * 3, "#%02X%02X%02X" % (bgr[2], bgr[1], bgr[0])))
    # de-duplicate similar colours
    out_acc.sort(reverse=True)
    picked = []
    for sc, hx in out_acc:
        rgb = np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)], float)
        if all(np.linalg.norm(rgb - np.array([int(q[i:i + 2], 16) for i in (1, 3, 5)], float)) > 60 for q in picked):
            picked.append(hx)
    neutrals.sort(reverse=True)
    return {"accents": picked[:4], "neutral": neutrals[0][1] if neutrals else "#7A7A7A"}
work = sys.argv[1]
lay_p = os.path.join(work, "layout.json")
layout = json.load(open(lay_p))
dur = json.load(open(os.path.join(work, "segments.json")))["duration"]
clips = layout.get("clips") or [{"start": 0.0, "end": dur}]
cap = cv2.VideoCapture(os.path.join(work, "cut.mov"))
fps = cap.get(cv2.CAP_PROP_FPS) or 30
with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as seg:
    for c in clips:
        acc, n, frames = np.zeros((ROWS, COLS), np.float32), 0, []
        for k in range(12):
            t = c["start"] + (k + 0.5) * (c["end"] - c["start"]) / 12
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
            ok, fr = cap.read()
            if not ok:
                continue
            frames.append(cv2.resize(fr, (90, 160), interpolation=cv2.INTER_AREA))
            m = seg.process(cv2.cvtColor(cv2.resize(fr, (W // 4, H // 4)), cv2.COLOR_BGR2RGB)).segmentation_mask
            acc += cv2.resize((m > 0.5).astype(np.float32), (COLS, ROWS), interpolation=cv2.INTER_AREA)
            n += 1
        c["occ"] = np.round(acc / max(1, n), 2).tolist()
        c["palette"] = scene_palette(frames)
if layout.get("clips"):
    layout["clips"] = clips
else:
    layout["occ"] = clips[0]["occ"]
    layout["palette"] = clips[0]["palette"]
json.dump(layout, open(lay_p, "w"), indent=1)
print("body occupancy map:", len(clips), "clip(s)")
