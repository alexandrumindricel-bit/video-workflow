#!/usr/bin/env python3
"""Step 1: normalize the raw video and analyze framing.

- Constant 30 fps (phone footage is often variable-frame-rate, which causes lip-sync
  drift after cutting), 1080x1920 (scale to cover + center crop), 48 kHz stereo audio.
- Extracts 16 kHz mono WAV for transcription.
- Detects the face across the video (OpenCV Haar cascade) and writes layout.json with the
  zones where graphics can go without covering the face.

Usage: prepare.py RAW_VIDEO WORKDIR
"""
import json, os, subprocess, sys

W, H, FPS = 1080, 1920, 30


def run(cmd):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                          "-show_format", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def detect_faces(video, samples=24):
    import cv2
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    boxes = []
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * n / samples))
        ok, frame = cap.read()
        if not ok:
            continue
        small = cv2.resize(frame, (W // 3, H // 3))
        gray = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            boxes.append([int(x) * 3, int(y) * 3, int(w) * 3, int(h) * 3])
    cap.release()
    return boxes


# User-approved colour look ("Mindri-Box-v3" / "Comanda-Ionut-v2/v4", same studio): the footage's own colours, SIMPLE -
# deep blacks, clean whites, natural (not boosted) colour, white clothes neutral-warm (not orange).
# Tone targets: upper 60% of the frame (backdrop + person), grey 0..255. Colour targets: whole frame, mean HSV
# Lab chroma of lit areas ~13.5 and the cast of bright near-neutral pixels (white T-shirt/hoodie) at Lab a ~1, b ~5.
LOOK = {"p5": 38.0, "p25": 52.0, "p50": 76.0, "p95": 226.0, "sat": 13.5, "white_ab": (1.0, 5.0)}


def _look_eval(frames, lut, g, du, dv):
    """Apply the candidate look to sample frames (tone LUT on RGB, chroma gain/offset in YCrCb) and measure
    whole-frame saturation and the white cast."""
    import cv2
    import numpy as np
    sats, wab = [], []
    for fr in frames:
        x = cv2.LUT(fr, lut)
        ycc = cv2.cvtColor(x, cv2.COLOR_BGR2YCrCb).astype(np.float32)
        ycc[..., 1] = (ycc[..., 1] - 128) * g + 128 + dv
        ycc[..., 2] = (ycc[..., 2] - 128) * g + 128 + du
        x = cv2.cvtColor(np.clip(ycc, 0, 255).astype(np.uint8), cv2.COLOR_YCrCb2BGR)
        lab = cv2.cvtColor(x, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
        L, A, B = lab[:, 0] * 100 / 255, lab[:, 1] - 128, lab[:, 2] - 128
        lit = L > 25                                   # colourfulness of the lit areas (dark noise ignored)
        sats.append(float(np.hypot(A[lit], B[lit]).mean()) if lit.any() else 0.0)
        m = (L > 70) & (np.hypot(A, B) < 30)
        if m.sum() > 50:
            wab.append((float(A[m].mean()), float(B[m].mean())))
    return float(np.mean(sats)), (tuple(np.mean(wab, 0)) if wab else None)


def look_match(video, samples=12):
    """ffmpeg filter (tone curve + chroma gain + white-cast correction) that brings a normalised clip to the approved
    SIMPLE look, or None if it is already there. Tone: only deepens shadows/mids and lifts dim whites (max 35 levels per
    point). Colour: saturation is pulled towards the target in BOTH directions (gain 0.6-1.2, untouched within +-15%),
    an orange/blue/green cast on white clothes is neutralised towards the approved warm-neutral (offsets max 8)."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frames, g0 = [], []
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * n / samples))
        ok, fr = cap.read()
        if ok:
            fr = cv2.resize(fr, (270, 480))
            frames.append(fr)
            g0.append(cv2.cvtColor(fr[:290], cv2.COLOR_BGR2GRAY).ravel())
    cap.release()
    if not frames:
        return None
    g = np.concatenate(g0)
    p5, p25, p50, p75, p95 = (float(x) for x in np.percentile(g, [5, 25, 50, 75, 95]))
    lim = lambda v, t: v - min(35.0, max(0.0, v - t))
    pts = [(0, 0), (p5, lim(p5, LOOK["p5"])), (p25, lim(p25, LOOK["p25"])), (p50, lim(p50, LOOK["p50"])),
           (p75, p75), (p95, min(255.0, p95 + min(25.0, max(0.0, LOOK["p95"] - p95)))), (255, 255)]
    tone_moved = max(abs(a - b) for a, b in pts) >= 10
    xs, ys, last = [], [], -1.0
    for x, y in sorted(pts):
        if xs and x <= xs[-1] + 2:
            continue
        y = max(y, last + 1.0)
        xs.append(x); ys.append(y); last = y
    lut = np.clip(np.interp(np.arange(256), xs, ys), 0, 255).astype(np.uint8) if tone_moved else np.arange(256, dtype=np.uint8)
    # white cast: offsets that move the white clothes towards the approved warm-neutral
    du = dv = 0.0
    s0, w0 = _look_eval(frames, lut, 1.0, 0, 0)
    if w0 is not None:
        ta, tb = LOOK["white_ab"]
        if w0[1] > tb + 3 or abs(w0[0] - ta) > 4:      # only REMOVE an orange/yellow (or magenta/green) cast
            for _ in range(6):                    # Lab a ~ +Cr, Lab b ~ -Cb
                _, w = _look_eval(frames, lut, 1.0, du, dv)
                if w is None:
                    break
                dv = float(np.clip(dv - 0.8 * (w[0] - ta), -8, 8))
                du = float(np.clip(du + 0.8 * max(0.0, w[1] - tb), 0, 8))   # towards blue only: never warms
    # saturation: pull towards the target in both directions
    gain = 1.0
    s1, _ = _look_eval(frames, lut, 1.0, du, dv)
    if not (0.85 * LOOK["sat"] <= s1 <= 1.15 * LOOK["sat"]):
        lo, hi = 0.6, 1.2
        for _ in range(10):
            mid = (lo + hi) / 2
            sm, _ = _look_eval(frames, lut, mid, du, dv)
            lo, hi = (mid, hi) if sm < LOOK["sat"] else (lo, mid)
        gain = (lo + hi) / 2
    if not tone_moved and abs(gain - 1) < 0.04 and abs(du) < 1.5 and abs(dv) < 1.5:
        return None
    s2, w2 = _look_eval(frames, lut, gain, du, dv)
    print(f"look match: tone {'curve' if tone_moved else 'kept'}, saturation {s0:.0f}->{s2:.0f} (x{gain:.2f}), "
          f"white cast {tuple(round(v, 1) for v in w0) if w0 else '-'}->{tuple(round(v, 1) for v in w2) if w2 else '-'}")
    parts = []
    if tone_moved:
        parts.append("curves=all='" + " ".join(f"{x / 255:.4f}/{min(1.0, y / 255):.4f}" for x, y in zip(xs, ys)) + "'")
    # limited-range chroma is ~224/255 of the full-range values used above
    k = 224 / 255
    parts.append(f"lutyuv=u='clip((val-128)*{gain:.3f}+128+{du * k:.2f},16,240)':v='clip((val-128)*{gain:.3f}+128+{dv * k:.2f},16,240)'")
    return ",".join(parts)


def apply_look(src):
    """Re-encode WORK/source.mov in place with look_match (all clips: HDR-tonemapped, washed and normal SDR)."""
    f = look_match(src)
    if not f:
        return
    tmp = src.replace(".mov", "_look.mov")
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vf", f, "-c:v", "libx264", "-preset", "fast",
         "-crf", "14", "-g", "15", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-color_range", "tv", "-c:a", "copy", tmp])
    os.replace(tmp, src)


def washed_levels(video, samples=10):
    """lutyuv filter that restores milky SDR footage (black point lifted above ~Y45), else None."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    vals = []
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * n / samples))
        ok, fr = cap.read()
        if ok:
            vals.append(cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY).ravel())
    cap.release()
    if not vals:
        return None
    g = np.concatenate(vals)
    lo, hi = (16 + float(np.percentile(g, p)) * 219 / 255 for p in (1, 99.5))   # in limited-range Y
    # milky blacks OR dim whites (white T-shirt at ~Y193 instead of ~Y219 like tone-mapped HDR clips of the same set)
    if lo <= 45 and hi >= 203:
        return None
    lo_t, hi_t = min(34.0, lo), min(222.0, max(hi + 20, 216.0))
    k = (hi_t - lo_t) / max(1.0, hi - lo)
    print(f"washed SDR source (black Y{lo:.0f}, white Y{hi:.0f}) -> levels restored to Y{lo_t:.0f}..{hi_t:.0f}")
    c = "clip(128+(val-128)*1.08,16,240)"
    return f"lutyuv=y='clip({lo_t:.1f}+(val-{lo:.1f})*{k:.3f},16,235)':u='{c}':v='{c}'"


def main():
    raw, work = sys.argv[1], sys.argv[2]
    os.makedirs(work, exist_ok=True)
    info = probe(raw)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if not has_audio:
        sys.exit("ERROR: the video has no audio track - nothing to transcribe.")
    src = os.path.join(work, "source.mov")  # mov so the audio can stay lossless PCM
    vf = (f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={W}:{H},setsar=1,format=yuv420p")
    # iPhone / modern phones film HDR (HLG or PQ, BT.2020, 10-bit). Converting that to normal 8-bit video without
    # tone mapping makes everything pale and milky - so tone-map HDR to SDR BT.709 first (hable curve, 100 nits).
    trc = v.get("color_transfer", "")
    if trc in ("arib-std-b67", "smpte2084"):
        tm = (f"zscale=tin={trc}:min=bt2020nc:pin=bt2020:rin={'tv' if v.get('color_range', 'tv') == 'tv' else 'pc'}:t=linear:npl=100,"
              f"format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")
        vf = tm + vf
        print(f"HDR source ({trc}, {v.get('color_primaries')}) -> tone-mapped to SDR BT.709")
    else:
        # "washed" SDR: iPhone HDR clips re-encoded by a compressor app without tone mapping arrive as SDR with
        # lifted, milky blacks and dim whites. Restore the levels (luma only, gentle chroma) so they match the look
        # of properly tone-mapped HDR footage (user-approved "natural" look, Mindri-Box-v3).
        # USER RULE: no colour effects - the footage stays exactly as filmed. Level restore only on request.
        fix = washed_levels(raw) if os.environ.get("VW_COLOR_FIX") == "1" else None
        if fix:
            vf += "," + fix
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", raw, "-vf", vf,
         "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-g", "15",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
         "-af", "aresample=48000:async=1:first_pts=0", "-ac", "2", "-c:a", "pcm_s16le", src])
    if os.environ.get("VW_COLOR_FIX") == "1":   # USER RULE: no colour filter - only when explicitly asked
        apply_look(src)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
         os.path.join(work, "audio16k.wav")])

    boxes = None
    venv_py = "/opt/vw-seg/bin/python"
    if os.path.exists(venv_py):  # MediaPipe full-range face detector: reliable for small/far faces
        r = subprocess.run([venv_py, os.path.join(os.path.dirname(os.path.abspath(__file__)), "detect_face.py"), src],
                           capture_output=True, text=True)
        try:
            boxes = [b[:4] for b in json.loads(r.stdout.strip().splitlines()[-1])]
        except Exception:
            boxes = None
    if not boxes:
        boxes = detect_faces(src)  # fallback: OpenCV Haar cascade
    layout = {"width": W, "height": H, "fps": FPS,
              "source": {"width": int(v["width"]), "height": int(v["height"]), "rotation": rot,
                         "duration": float(info["format"]["duration"]),
                         # phone videos are often stored landscape + a -90/90 rotation flag (ffmpeg auto-rotates)
                         "landscape_cropped": (int(v["height"]) > int(v["width"])) if abs(rot) == 90 else (int(v["width"]) > int(v["height"]))}}
    if boxes:
        import statistics as st
        x, y, w, h = (int(st.median(b[i] for b in boxes)) for i in range(4))
        # drop false positives (hands, posters): boxes far from the median face
        boxes = [b for b in boxes if abs(b[0] + b[2] / 2 - (x + w / 2)) < w and abs(b[1] + b[3] / 2 - (y + h / 2)) < h] or boxes
        import numpy as np
        top = int(np.percentile([b[1] for b in boxes], 15))
        bottom = int(np.percentile([b[1] + b[3] for b in boxes], 85))
        layout["face"] = {"x": x, "y": y, "w": w, "h": h, "min_top": top, "max_bottom": bottom,
                          "detected_in": f"{len(boxes)} samples"}
        # head incl. hair is ~35% taller than the Haar box on top
        head_top = max(0, top - int(0.35 * h))
        layout["zones"] = {
            # graphics/titles above the head
            "top": {"y0": int(0.06 * H), "y1": max(int(0.06 * H) + 120, head_top - 20)},
            # captions: below the chin, above the platform UI (bottom ~18%)
            "captions_y": int(min(0.74 * H, max(bottom + 0.18 * H, 0.62 * H))),
            "side_free": "left" if x + w / 2 > W * 0.55 else ("right" if x + w / 2 < W * 0.45 else "both-narrow"),
        }
    else:
        layout["face"] = None
        layout["zones"] = {"top": {"y0": int(0.06 * H), "y1": int(0.26 * H)},
                           "captions_y": int(0.70 * H), "side_free": "unknown"}
    # brightness of the title zone: on bright backgrounds (white walls, sky) light titles need a box/tint
    try:
        import cv2
        cap = cv2.VideoCapture(src)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        z = layout["zones"]["top"]
        vals = []
        for i in range(8):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int((i + 0.5) * n / 8))
            ok, fr = cap.read()
            if ok:
                vals.append(float(cv2.cvtColor(fr[z["y0"]:max(z["y1"], z["y0"] + 380)], cv2.COLOR_BGR2GRAY).mean()) / 255)
        cap.release()
        if vals:
            layout["zones"]["top_luma"] = round(sum(vals) / len(vals), 3)
            layout["zones"]["top_bright"] = layout["zones"]["top_luma"] > 0.6
    except Exception as e:
        print("brightness check skipped:", e)
    json.dump(layout, open(os.path.join(work, "layout.json"), "w"), indent=2)
    print(json.dumps(layout, indent=2))
    if layout["source"]["landscape_cropped"]:
        print("WARNING: source is landscape - it was center-cropped to 9:16. Check framing.")


if __name__ == "__main__":
    main()
