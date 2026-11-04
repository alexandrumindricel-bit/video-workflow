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
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", raw, "-vf", vf,
         "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-g", "15",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
         "-af", "aresample=48000:async=1:first_pts=0", "-ac", "2", "-c:a", "pcm_s16le", src])
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
