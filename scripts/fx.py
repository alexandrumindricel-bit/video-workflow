#!/opt/vw-seg/bin/python
"""Step 6a: camera / compositing effects on the cut video (runs in the /opt/vw-seg venv: mediapipe 0.10.14).

Produces, on the cut timeline (all 1080x1920, 30 fps):
  fx_bg.mov       background plate: the video with camera effects applied
  fx_person.mov   the person as they should appear on top        (only if a cut-out is needed)
  fx_matte.mkv    person alpha (0 when no cut-out is active)       (only if needed)
  fx_sticker.mkv  white "sticker" border alpha (paper cut)          (only if used)
  fx_outline.mkv  hand-drawn boiling outline alpha (doodle boil)    (only if used)
  fx_flags.json   which of those exist
Compose stacks:  bg -> back overlay layer -> sticker -> person -> outline -> front overlay layer.
So anything on the BACK layer appears behind the person whenever the cut-out is active.

storyboard.effects[]:  {"kind": ..., "start": s, "end": e, ...}
  punch        scale (1.06-1.12)                  constant punch-in (also: storyboard.zooms)
  push         from, to (e.g. 1.0 -> 1.15)        smooth digital zoom
  zoom_through at (transition time), dur 0.36     zoom + radial blur into the cut and out of it
  vertigo      amount 0.18                        dolly zoom: background zooms, person stays
  frame_break  rect [x,y,w,h], color, radius      video shown inside a frame, person breaks out of it
  pull_back    scale 0.58, y, bg "#ECE8DF"         video shrinks into a floating window on a canvas
  cutout       -                                  force person cut-out (for back-layer elements)
  track        scale 1.3, smooth 0.88             zoomed crop that follows the face (face tracking)
storyboard.grade: "cinematic" | {"preset": ..., "strength": 0.85, "clips": [per-clip presets], "subject_pop": true}
  presets: cinematic (teal-orange), warm (golden/night), olive, clean (bright high-key), mindricel (brand), none
  sticker      width 16                           white sticker border around the person (paper cut)
  outline      width 7, color                     boiling hand-drawn outline around the person
Usage: fx.py WORKDIR
"""
import json, os, subprocess, sys
import numpy as np
import cv2

W, H, FPS = 1080, 1920, 30


def ease(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def ease_io(p):
    p = min(1.0, max(0.0, p))
    return 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2


def writer(path, gray=False):
    args = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray" if gray else "bgr24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    args += (["-c:v", "ffv1", "-pix_fmt", "gray"] if gray else
             ["-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p"])
    return subprocess.Popen(args + [path], stdin=subprocess.PIPE)


def zoom(img, s, cx, cy, interp=cv2.INTER_LINEAR):
    if abs(s - 1) < 1e-3:
        return img
    cw, ch = W / s, H / s
    x0 = min(max(cx - cw / 2, 0), W - cw)
    y0 = min(max(cy - ch * 0.42, 0), H - ch)
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    return cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT)


def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(m, (cx, cy), r, 255, -1)
    return cv2.GaussianBlur(m, (3, 3), 0).astype(np.float32) / 255


def blurred_canvas(img, dark=0.55):
    small = cv2.resize(img, (W // 8, H // 8))
    small = cv2.GaussianBlur(small, (0, 0), 6)
    return (cv2.resize(small, (W, H)) * dark).astype(np.uint8)


def hex_bgr(h):
    h = h.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


# ------------------------------------------------------------------ colour grade (applied to the footage only)
# lift/gain are per-channel offsets in BGR order (shadows / highlights), contrast = S-curve amount,
# sat = saturation (skin tones protected), vig = vignette strength, pop = darken+soften background (needs mask)
GRADES = {
    "cinematic": dict(lift=(0.075, 0.02, -0.045), gain=(-0.07, 0.0, 0.075), contrast=0.55, sat=1.2, vig=0.45, pop=0.14, bright=-0.02, hl=0.22),
    "warm":      dict(lift=(-0.03, -0.015, 0.0), gain=(-0.09, 0.035, 0.09), contrast=0.6, sat=1.2, vig=0.6, pop=0.18, bright=-0.05, hl=0.2),
    "olive":     dict(lift=(-0.035, 0.045, 0.012), gain=(-0.04, 0.015, 0.05), contrast=0.42, sat=1.0, vig=0.4, pop=0.12, bright=-0.02, hl=0.2),
    "clean":     dict(lift=(0.01, 0.01, 0.01), gain=(0.02, 0.0, 0.0), contrast=0.32, sat=1.08, vig=0.2, pop=0.08, bright=0.02, hl=0.08),
    "mindricel": dict(lift=(0.05, 0.02, -0.03), gain=(-0.085, 0.015, 0.08), contrast=0.55, sat=1.2, vig=0.48, pop=0.14, bright=-0.03, hl=0.22),
    "none":      None,
}


def build_luts(g, strength):
    x = np.linspace(0, 1, 256, dtype=np.float32)
    s = x * x * (3 - 2 * x)                                   # smoothstep S-curve
    base = np.clip(x + (s - x) * g["contrast"] * 1.6 + g.get("bright", 0), 0, 1)
    # highlight roll-off: bright walls / overcast sky get detail back instead of clipping to white
    hl = g.get("hl", 0)
    knee = np.clip((base - 0.62) / 0.38, 0, 1)
    base = base - hl * knee ** 1.5 * (base - 0.62)
    luts = []
    for c in range(3):                                        # B, G, R
        y = base + g["lift"][c] * (1 - base) ** 2 + g["gain"][c] * base ** 2
        y = np.clip(x + (y - x) * strength, 0, 1)
        luts.append((y * 255).astype(np.uint8))
    return luts


_VIG = {}


def vignette(h, w, amount):
    key = (h, w, round(amount, 3))
    if key not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h * 0.45) / (h / 2)) ** 2)
        _VIG[key] = (1 - amount * np.clip(r - 0.35, 0, None) ** 1.6).clip(0.3, 1)[..., None]
    return _VIG[key]


def apply_grade(F, g, luts, strength, M=None):
    out = cv2.merge([cv2.LUT(ch, lut) for ch, lut in zip(cv2.split(F), luts)])
    if g["sat"] != 1.0:
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
        hch, sch, vch = cv2.split(hsv)
        skin = ((hch < 25) | (hch > 170)).astype(np.float32)   # warm hues: keep skin natural
        k = 1 + (g["sat"] - 1) * strength
        sf = sch.astype(np.float32) * (k * (1 - skin) + min(k, 1.04) * skin)
        out = cv2.cvtColor(cv2.merge([hch, np.clip(sf, 0, 255).astype(np.uint8), vch]), cv2.COLOR_HSV2BGR)
    if M is not None and g.get("pop"):
        small = cv2.resize(out, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
        soft = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2.2), (W, H))
        bgw = (1 - M)[..., None] * strength
        out = (out * (1 - bgw * 0.45) + soft * (bgw * 0.45)) * (1 - bgw * g["pop"])
        out = out.astype(np.float32)
    if g["vig"]:
        out = out.astype(np.float32) * vignette(H, W, g["vig"] * strength)
    return np.clip(out, 0, 255).astype(np.uint8)


class FaceTracker:
    """Smoothly follows the face (MediaPipe full-range detector) for the 'track' effect."""
    def __init__(self, cx, cy):
        import mediapipe as mp
        self.fd = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        self.cx, self.cy = cx, cy

    def update(self, F, smooth):
        res = self.fd.process(cv2.cvtColor(cv2.resize(F, (W // 3, H // 3)), cv2.COLOR_BGR2RGB))
        if res.detections:
            b = max(res.detections, key=lambda d: d.location_data.relative_bounding_box.width).location_data.relative_bounding_box
            tx, ty = (b.xmin + b.width / 2) * W, (b.ymin + b.height / 2) * H
            # dead zone: ignore small jitters, glide towards bigger moves
            if abs(tx - self.cx) > 18 or abs(ty - self.cy) > 18:
                self.cx = smooth * self.cx + (1 - smooth) * tx
                self.cy = smooth * self.cy + (1 - smooth) * ty
        return self.cx, self.cy


def main():
    work = sys.argv[1]
    sb = json.load(open(os.path.join(work, "storyboard.json")))
    layout = json.load(open(os.path.join(work, "layout.json")))
    dur = json.load(open(os.path.join(work, "segments.json")))["duration"]
    def center_of(f):
        return (f["x"] + f["w"] / 2, f["y"] + f["h"] / 2) if f else (W / 2, H * 0.4)
    clips = layout.get("clips") or [{"start": 0, "end": 1e9, "face": layout.get("face")}]
    def center_at(t):  # multi-clip: zoom around the face of the clip on screen
        for c in clips:
            if c["start"] - 1e-3 <= t < c["end"]:
                return center_of(c.get("face"))
        return center_of(clips[-1].get("face"))
    cx, cy = center_at(0)

    fx = list(sb.get("effects", []))
    for z in sb.get("zooms", []):
        fx.append({"kind": "punch", "start": z["start"], "end": z["end"], "scale": z.get("scale", 1.1)})
    for tr in sb.get("transitions", []):
        if tr["kind"] == "zoom_through":
            d = tr.get("dur", 0.36)
            fx.append({"kind": "zoom_through", "start": tr["at"] - d / 2, "end": tr["at"] + d / 2, "at": tr["at"]})
    for e in fx:
        if e["kind"] == "zoom_through" and "start" not in e:
            d = e.get("dur", 0.36); e["start"], e["end"] = e["at"] - d / 2, e["at"] + d / 2
    BACK_TYPES = {"backdrop", "glass", "cover", "wall"}
    back_windows = [(el["start"], el["end"]) for el in sb.get("elements", [])
                    if el["type"] == "orbit" or el.get("layer", "back" if el["type"] in BACK_TYPES else "front") == "back"]
    bw = os.path.join(work, "back_windows.json")  # captions placed behind the person (from render_overlay.cjs)
    if os.path.exists(bw):
        back_windows += [tuple(x) for x in json.load(open(bw))]
    CUT_KINDS = {"vertigo", "frame_break", "cutout", "sticker", "outline"}

    def active(t, kinds):
        return [e for e in fx if e["kind"] in kinds and e["start"] <= t < e["end"]]

    need_cut = bool(back_windows) or any(e["kind"] in CUT_KINDS for e in fx)
    # grade: storyboard "grade": {"preset": "cinematic", "strength": 0.85, "clips": ["warm", ...]} (per clip optional)
    gcfg = sb.get("grade", {"preset": "none"})
    if isinstance(gcfg, str):
        gcfg = {"preset": gcfg}
    g_strength = gcfg.get("strength", 0.85)
    def grade_at(t):
        name = gcfg.get("preset", "none")
        per = gcfg.get("clips")
        if per:
            for k, c in enumerate(clips):
                if c["start"] - 1e-3 <= t < c["end"] and k < len(per):
                    name = per[k]
        return GRADES.get(name)
    lut_cache = {}
    need_pop = any(g and g.get("pop") for g in [GRADES.get(gcfg.get("preset", "none"))] + [GRADES.get(n) for n in gcfg.get("clips", [])]) \
        and gcfg.get("subject_pop", True)
    tracker = None
    use_sticker = any(e["kind"] == "sticker" for e in fx)
    use_outline = any(e["kind"] == "outline" for e in fx)

    seg = None
    if need_cut or need_pop:
        import mediapipe as mp
        seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)

    cap = cv2.VideoCapture(os.path.join(work, "cut.mov"))
    out_bg = writer(os.path.join(work, "fx_bg.mov"))
    out_p = writer(os.path.join(work, "fx_person.mov")) if need_cut else None
    out_m = writer(os.path.join(work, "fx_matte.mkv"), True) if need_cut else None
    out_s = writer(os.path.join(work, "fx_sticker.mkv"), True) if use_sticker else None
    out_o = writer(os.path.join(work, "fx_outline.mkv"), True) if use_outline else None
    zero = np.zeros((H, W), np.uint8)
    ema = None
    rng = np.random.default_rng(3)
    n_frames = int(round(dur * FPS))
    for f in range(n_frames):
        ok, F = cap.read()
        if not ok:
            break
        t = f / FPS
        cx, cy = center_at(t)
        M = None
        if seg is not None:
            res = seg.process(cv2.cvtColor(cv2.resize(F, (W // 2, H // 2)), cv2.COLOR_BGR2RGB)).segmentation_mask
            ema = res if ema is None else 0.55 * res + 0.45 * ema  # temporal smoothing: less edge flicker
            m = np.clip((ema - 0.35) / 0.3, 0, 1)
            M = cv2.GaussianBlur(cv2.resize(m, (W, H)), (0, 0), 1.6)

        g = grade_at(t)
        if g:
            key = id(g)
            if key not in lut_cache:
                lut_cache[key] = build_luts(g, g_strength)
            F = apply_grade(F, g, lut_cache[key], g_strength, M if need_pop else None)
        tr = active(t, {"track"})
        if tr:
            if tracker is None:
                tracker = FaceTracker(cx, cy)
            cx, cy = tracker.update(F, tr[0].get("smooth", 0.88))
        elif tracker is not None:
            tracker.cx, tracker.cy = cx, cy

        bg, person, matte = F, F, None
        cut_on = any(a <= t < b for a, b in back_windows) or bool(active(t, CUT_KINDS))

        pb = active(t, {"pull_back"})
        fb = active(t, {"frame_break"})
        zt = active(t, {"zoom_through"})
        vg = active(t, {"vertigo"})
        pu = active(t, {"push"})
        pc = active(t, {"punch"})
        if pb:
            e = pb[0]
            p = ease_io((t - e["start"]) / 0.45) * ease_io((e["end"] - t) / 0.3)
            s = 1 - (1 - e.get("scale", 0.58)) * p
            canvas = np.full((H, W, 3), hex_bgr(e.get("bg", "#ECE8DF")), np.uint8)
            if e.get("bg") == "blur":
                canvas = blurred_canvas(F, 0.6)
            w, h = int(W * s) // 2 * 2, int(H * s) // 2 * 2
            x0 = (W - w) // 2
            y0 = int((H - h) / 2 + (e.get("y", H * 0.56) - H / 2) * p)
            y0 = min(max(y0, 0), H - h)
            if p > 0.01:  # soft shadow
                sh = np.zeros((H, W), np.float32)
                cv2.rectangle(sh, (x0 + 10, y0 + 30), (x0 + w - 10, y0 + h + 30), 1, -1)
                sh = cv2.GaussianBlur(sh, (0, 0), 30) * 0.35 * p
                canvas = (canvas * (1 - sh[..., None])).astype(np.uint8)
            small = cv2.resize(F, (w, h), interpolation=cv2.INTER_AREA)
            r = max(2, int(44 * p))
            rm = rounded_mask(w, h, r)[..., None]
            roi = canvas[y0:y0 + h, x0:x0 + w]
            canvas[y0:y0 + h, x0:x0 + w] = (small * rm + roi * (1 - rm)).astype(np.uint8)
            bg = person = canvas
            cut_on = False
        elif fb:
            e = fb[0]
            rx, ry, rw, rh = e.get("rect", [150, 520, 780, 1000])
            p = ease((t - e["start"]) / 0.35) * ease((e["end"] - t) / 0.3)
            x0, y0 = int(rx * p), int(ry * p)
            x1, y1 = int(W - (W - rx - rw) * p), int(H - (H - ry - rh) * p)
            canvas = blurred_canvas(F, 0.45)
            win = np.zeros((H, W), np.float32)
            win[y0:y1, x0:x1] = rounded_mask(x1 - x0, y1 - y0, max(2, int(e.get("radius", 36) * p)))
            bg = (F * win[..., None] + canvas * (1 - win[..., None])).astype(np.uint8)
            if p > 0.02:
                col = hex_bgr(e.get("color", "#F1EBDD"))
                cv2.rectangle(bg, (x0, y0), (x1, y1), col, max(1, int(e.get("border", 7) * p)), cv2.LINE_AA)
            person = F
            cut_on = True
            # only the parts of the person OUTSIDE the window need the cut-out (inside is already identical)
        elif zt:
            e = zt[0]
            at = e.get("at", (e["start"] + e["end"]) / 2)
            half = (e["end"] - e["start"]) / 2
            p = 1 - abs(t - at) / half  # 0 -> 1 at the cut -> 0
            s = 1 + 0.9 * ease_io(p)
            acc = np.zeros((H, W, 3), np.float32)
            taps = 6
            for k in range(taps):  # radial (zoom) blur, stronger near the cut
                acc += zoom(F, s * (1 + 0.06 * p * k), cx, cy)
            bg = person = (acc / taps).astype(np.uint8)
            cut_on = False
        elif vg:
            e = vg[0]
            p = ease_io((t - e["start"]) / max(0.01, e["end"] - e["start"]))
            s = 1 + e.get("amount", 0.18) * p
            # clean plate: fill the person area with blurred surroundings before zooming the background
            small_f = cv2.resize(F, (W // 4, H // 4)).astype(np.float32)
            small_m = cv2.resize(M, (W // 4, H // 4))
            small_m = cv2.dilate(small_m, np.ones((9, 9), np.uint8))
            keep = (1 - small_m)[..., None]
            num = cv2.GaussianBlur(small_f * keep, (0, 0), 14)
            den = cv2.GaussianBlur(keep, (0, 0), 14)[..., None] + 1e-4
            fill = cv2.resize((num / den).astype(np.uint8), (W, H))
            mm = cv2.resize(small_m, (W, H))[..., None]
            plate = (F * (1 - mm) + fill * mm).astype(np.uint8)
            bg = zoom(plate, s, cx, cy)
            person = F
            cut_on = True
        else:
            s = 1.0
            if pu:
                e = pu[0]
                s = e.get("from", 1.0) + (e.get("to", 1.15) - e.get("from", 1.0)) * ease_io((t - e["start"]) / max(0.01, e["end"] - e["start"]))
            elif pc:
                s = pc[0].get("scale", 1.1)
            if tr:  # face tracking: zoomed crop that follows the face, eased in/out
                e = tr[0]
                k = ease_io((t - e["start"]) / 0.4) * ease_io((e["end"] - t) / 0.4)
                s *= 1 + (e.get("scale", 1.3) - 1) * k
            bg = person = zoom(F, s, cx, cy)
            if M is not None and s != 1.0:
                M = zoom(M, s, cx, cy)

        out_bg.stdin.write(bg.tobytes())
        if need_cut:
            mat = (M * 255).astype(np.uint8) if (cut_on and M is not None) else zero
            out_p.stdin.write(person.tobytes())
            out_m.stdin.write(mat.tobytes())
            if out_s:
                st = active(t, {"sticker"})
                if st and M is not None:
                    wpx = st[0].get("width", 16)
                    d = cv2.dilate((M > 0.5).astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * wpx + 1,) * 2))
                    a = ease((t - st[0]["start"]) / 0.2) * ease((st[0]["end"] - t) / 0.2)
                    out_s.stdin.write((cv2.GaussianBlur(d, (3, 3), 0) * a).astype(np.uint8).tobytes())
                else:
                    out_s.stdin.write(zero.tobytes())
            if out_o:
                ol = active(t, {"outline"})
                if ol and M is not None:
                    e = ol[0]
                    gap = e.get("gap", 22)
                    d = cv2.dilate((M > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * gap + 1,) * 2))
                    cs, _ = cv2.findContours(d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                    canvas = np.zeros((H, W), np.uint8)
                    boil = int(t * 10)  # redraw jitter 10x per second = "boil"
                    r2 = np.random.default_rng(boil)
                    for c in cs:
                        if cv2.contourArea(c) < 4000:
                            continue
                        pts = c[::14, 0, :].astype(np.float32)
                        if len(pts) < 8:
                            continue
                        jit = r2.normal(0, 3.2, pts.shape).astype(np.float32)
                        jit = cv2.GaussianBlur(jit.reshape(-1, 1, 2), (1, 5), 0).reshape(-1, 2)
                        pts = (pts + jit).astype(np.int32)
                        cv2.polylines(canvas, [pts], True, 255, e.get("width", 7), cv2.LINE_AA)
                    p = ease((t - e["start"]) / 0.25)
                    # draw-on: reveal the outline progressively in the first 0.25 s
                    if p < 1:
                        yy = int(H * p)
                        canvas[yy:, :] = 0
                    out_o.stdin.write(canvas.tobytes())
                else:
                    out_o.stdin.write(zero.tobytes())

    for w in (out_bg, out_p, out_m, out_s, out_o):
        if w:
            w.stdin.close(); w.wait()
    json.dump({"person": need_cut, "sticker": use_sticker, "outline": use_outline},
              open(os.path.join(work, "fx_flags.json"), "w"))
    print(f"fx: {n_frames} frames; cut-out={'yes' if need_cut else 'no'}, sticker={use_sticker}, outline={use_outline}")


if __name__ == "__main__":
    main()
