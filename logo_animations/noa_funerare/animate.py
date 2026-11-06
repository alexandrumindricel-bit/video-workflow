#!/usr/bin/env python3
"""NOA Funerare logo animation.

The dove flies in from the right, flapping, glides down and lands on the letter "A" (its pose in the logo);
the letters appear in a calm memorial style: N, O, A rise slowly out of a soft blur, FUNERARE fades in letter by
letter while its spacing gently closes, a pale light sweeps across the logo, dust motes drift in the dark.

All shapes are cut out of the original logo (logo.jpg), so the final frame is the logo itself.

  python3 animate.py [--format landscape|vertical|square] [--fps 60] [--out noa_funerare.mp4]

Needs: numpy, scipy, opencv-python-headless, Pillow, ffmpeg.
"""
import argparse
import math
import os
import subprocess

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
FORMATS = {"landscape": (1920, 1080, 1.12), "vertical": (1080, 1920, 0.86), "square": (1080, 1080, 0.86)}
DURATION = 11.0

INK = np.array([0.955, 0.945, 0.925], np.float32)       # soft ivory white for the lettering
SHEEN = np.array([1.0, 0.90, 0.72], np.float32)        # pale gold of the light sweep
BG_CENTER = np.array([0.098, 0.096, 0.094], np.float32)
BG_EDGE = np.array([0.028, 0.027, 0.027], np.float32)


# ---------------------------------------------------------------- easing
def clamp01(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x, p=3.0):
    return 1 - (1 - clamp01(x)) ** p


def ease_in_out(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def window(t, a, b):
    return clamp01((t - a) / (b - a))


# ---------------------------------------------------------------- logo cut-out
def load_logo():
    g = np.array(Image.open(os.path.join(HERE, "logo.jpg")).convert("L")).astype(np.float32)
    alpha = np.clip((g - 32) / (235 - 32), 0, 1)
    solid = g > 100
    solid[:, :8] = solid[:, -8:] = False                  # thin frame of the source image
    solid[:4] = solid[-4:] = False
    lab, n = nd.label(solid, structure=np.ones((3, 3)))
    # every anti-aliased edge pixel belongs to its nearest component
    _, (iy, ix) = nd.distance_transform_edt(lab == 0, return_indices=True)
    near = lab[iy, ix]
    dist = nd.distance_transform_edt(lab == 0)
    near[dist > 3] = 0
    alpha[near == 0] = 0

    groups = {"N": [], "O": [], "A": [], "dove": [], "funerare": []}
    for i, s in enumerate(nd.find_objects(lab), start=1):
        if (lab[s] == i).sum() < 30:
            continue
        y0, y1, x0, x1 = s[0].start, s[0].stop, s[1].start, s[1].stop
        cx = (x0 + x1) / 2
        if y0 < 430:
            groups["dove"].append(i)
        elif 600 < y0 < 620 and y1 < 665:
            groups["funerare"].append((cx, i))
        elif cx < 420:
            groups["N"].append(i)
        elif cx < 772:
            groups["O"].append(i)
        else:
            groups["A"].append(i)
    groups["funerare"] = [i for _, i in sorted(groups["funerare"])]

    def mask_of(ids):
        return np.isin(near, ids)

    layers = {k: alpha * mask_of(groups[k]) for k in ("N", "O", "A")}
    letters = [alpha * (near == i) for i in groups["funerare"]]
    dove_line = alpha * mask_of(groups["dove"])
    dove_fill = nd.binary_fill_holes(nd.binary_closing(dove_line > 0.35, iterations=2)).astype(np.float32)
    dove_fill = cv2.GaussianBlur(dove_fill, (0, 0), 0.8)
    return layers, letters, dove_line, dove_fill


# wing polygon (source pixels): both wings above the shoulder, cut along the back
WING_POLY = np.array([(952, 70), (1225, 70), (1225, 330), (1150, 392), (1000, 378), (978, 300), (952, 262)], np.int32)
WING_PIVOT = (985.0, 300.0)
DOVE_BOX = (690, 70, 1220, 545)  # x0, y0, x1, y1 in source pixels
CONTENT_BOX = (105, 72, 1215, 805)


class Sprite:
    """A cropped float layer placed on the canvas at integer offset (x, y)."""

    def __init__(self, img, x, y):
        self.img, self.x, self.y = img, x, y


def to_canvas(src, scale, origin, pad=40):
    """Scale a full-size source layer and crop it to its content."""
    ys, xs = np.nonzero(src > 0.002)
    x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
    crop = src[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    big = np.clip(big, 0, 1)
    big = cv2.copyMakeBorder(big, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    return Sprite(big, int(round(origin[0] + x0 * scale)) - pad, int(round(origin[1] + y0 * scale)) - pad)


def blit_max(dst, img, x, y, k=1.0):
    """Paste an alpha layer onto dst with 'max' (lettering never overlaps itself)."""
    H, W = dst.shape
    h, w = img.shape
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x] * k
    np.maximum(dst[y0:y1, x0:x1], sub, out=dst[y0:y1, x0:x1])


# ---------------------------------------------------------------- the dove
class Dove:
    def __init__(self, line, fill, scale, origin):
        x0, y0, x1, y1 = DOVE_BOX
        self.scale = scale
        wing = np.zeros(line.shape, np.uint8)
        cv2.fillPoly(wing, [WING_POLY], 1)
        wing = cv2.GaussianBlur(wing.astype(np.float32), (0, 0), 1.2)
        crop = lambda a: cv2.resize(a[y0:y1, x0:x1], None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        self.body_line, self.body_fill = crop(line * (1 - wing)), crop(fill * (1 - wing))
        self.wing_line, self.wing_fill = crop(line * wing), crop(fill * wing)
        self.pivot = ((WING_PIVOT[0] - x0) * scale, (WING_PIVOT[1] - y0) * scale)
        h, w = self.body_line.shape
        self.size = (w, h)
        self.rest = (origin[0] + x0 * scale, origin[1] + y0 * scale)   # canvas position of the crop at rest
        self.anchor = (w * 0.55, h * 0.62)                             # body centre: tilt and zoom pivot

    def render(self, W, H, dx, dy, tilt, zoom, wing_deg):
        # 1. flap: rotate the wings about the shoulder (positive = wing tips go down), with foreshortening
        w, h = self.size
        k = wing_deg / 75.0
        M = cv2.getRotationMatrix2D(self.pivot, -wing_deg, 1.0 - 0.22 * max(k, 0))
        wl = cv2.warpAffine(self.wing_line, M, (w, h), flags=cv2.INTER_LINEAR)
        wf = cv2.warpAffine(self.wing_fill, M, (w, h), flags=cv2.INTER_LINEAR)
        line = np.maximum(self.body_line, wl)
        fill = np.maximum(self.body_fill, wf)
        # 2. place on the canvas: zoom + tilt about the body, then move along the flight path
        ax, ay = self.anchor
        G = cv2.getRotationMatrix2D((ax, ay), tilt, zoom)
        G[0, 2] += self.rest[0] + dx
        G[1, 2] += self.rest[1] + dy
        return (cv2.warpAffine(line, G, (W, H), flags=cv2.INTER_LINEAR),
                cv2.warpAffine(fill, G, (W, H), flags=cv2.INTER_LINEAR))


def bezier(p, u):
    a, b, c, d = p
    m = 1 - u
    return m ** 3 * a + 3 * m * m * u * b + 3 * m * u * u * c + u ** 3 * d


# flight timeline (seconds)
FLY_START, GLIDE_START, BRAKE_START, LAND, SETTLED = 3.0, 6.0, 6.75, 7.45, 8.1


def dove_state(t, W, H):
    """Offset from the resting pose, tilt (deg, positive = counter-clockwise), zoom and wing angle."""
    unit = max(W, H) / 1920
    path = [np.array(p, np.float64) * unit for p in ((1250, -760), (650, -820), (330, -150), (0, 0))]
    u_lin = window(t, FLY_START, LAND)
    u = 1 - (1 - u_lin) ** 1.9                     # arrives slowly, like a bird braking
    pos = bezier(path, u)
    ahead = bezier(path, min(1.0, u + 0.01))
    vx, vy = ahead - pos if u < 0.995 else (np.array([-1.0, 0.0]))
    descent = math.degrees(math.atan2(vy, abs(vx) + 1e-6))
    tilt = max(-6, min(16, 0.45 * descent))            # head slightly down while descending
    brake = smooth(window(t, BRAKE_START, LAND)) * (1 - smooth(window(t, LAND, SETTLED)))
    tilt = tilt * (1 - smooth(window(t, BRAKE_START - 0.2, BRAKE_START + 0.3))) - 11 * brake
    zoom = 0.62 + 0.38 * ease_out(u_lin, 2.2)
    # touch-down: a tiny dip on landing, then still
    if t > LAND:
        s = t - LAND
        pos = pos + np.array([0.0, 7 * unit * math.sin(min(s, 0.6) / 0.6 * math.pi) * math.exp(-3 * s)])
    return pos[0], pos[1], tilt, zoom, wing_angle(t)


def wing_angle(t):
    if t < FLY_START:
        return 0.0
    # integrate flap phase: steady flight 2.1 Hz, glide (wings held open), quick braking beats, fold to rest pose
    phase, dt, s = 0.0, 1 / 240, FLY_START
    while s < t:
        phase += 2 * math.pi * (2.1 if s < GLIDE_START else 3.2) * dt
        s += dt
    flap = 72 * (0.5 - 0.5 * math.cos(phase))
    glide = 34.0
    g_in = smooth(window(t, GLIDE_START - 0.15, GLIDE_START + 0.25))
    b_in = smooth(window(t, BRAKE_START - 0.1, BRAKE_START + 0.15))
    brake_flap = 58 * (0.5 - 0.5 * math.cos(phase)) * (1 - 0.5 * window(t, BRAKE_START, LAND))
    a = flap * (1 - g_in) + glide * g_in
    a = a * (1 - b_in) + brake_flap * b_in
    return a * (1 - smooth(window(t, LAND - 0.05, SETTLED)))


# ---------------------------------------------------------------- background & atmosphere
def make_background(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.5, H * 0.47
    r = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    k = np.clip(r, 0, 1.25) / 1.25
    k = k * k * (3 - 2 * k)
    return BG_CENTER * (1 - k[..., None]) + BG_EDGE * k[..., None]


class Motes:
    def __init__(self, W, H, n, rng):
        self.W, self.H = W, H
        self.p = rng.uniform([0, 0], [W, H], (n, 2))
        self.v = rng.uniform([-6, -18], [6, -5], (n, 2)) * (max(W, H) / 1920)
        self.size = rng.uniform(0.8, 2.4, n)
        self.bright = rng.uniform(0.15, 0.55, n)
        self.tw = rng.uniform(0.3, 1.1, n)
        self.ph = rng.uniform(0, 2 * math.pi, n)

    def render(self, t):
        layer = np.zeros((self.H // 2, self.W // 2), np.float32)
        pos = self.p + self.v * t
        pos[:, 0] %= self.W
        pos[:, 1] %= self.H
        a = self.bright * (0.55 + 0.45 * np.sin(self.ph + t * self.tw * 2 * math.pi))
        for (x, y), s, b in zip(pos, self.size, a):
            cv2.circle(layer, (int(x * 8), int(y * 8)), int(s * 8), float(b), -1, cv2.LINE_AA, shift=4)
        return cv2.GaussianBlur(cv2.resize(layer, (self.W, self.H)), (0, 0), 1.6)


# ---------------------------------------------------------------- main render
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=FORMATS, default="landscape")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--out")
    ap.add_argument("--still", type=float, help="write one PNG frame at this time instead of the video")
    args = ap.parse_args()
    W, H, rel = FORMATS[args.format]
    out = args.out or os.path.join(HERE, "out", f"noa_funerare_{args.format}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    layers, letters, dove_line, dove_fill = load_logo()
    cx0, cy0, cx1, cy1 = CONTENT_BOX
    scale = rel
    origin = (W / 2 - (cx0 + cx1) / 2 * scale, H / 2 - (cy0 + cy1) / 2 * scale)

    big = {k: to_canvas(v, scale, origin) for k, v in layers.items()}
    funer = [to_canvas(v, scale, origin, pad=10) for v in letters]
    fun_cx = sum(s.x + s.img.shape[1] / 2 for s in funer) / len(funer)
    dove = Dove(dove_line, dove_fill, scale, origin)
    bg = make_background(W, H)
    motes = Motes(W, H, 70 if W * H > 1.5e6 else 55, np.random.default_rng(7))
    grain_rng = np.random.default_rng(3)
    unit = max(W, H) / 1920
    a_box = big["A"]
    a_glow_c = (a_box.x + a_box.img.shape[1] / 2, a_box.y + a_box.img.shape[0] * 0.25)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    def frame(t):
        ink = np.zeros((H, W), np.float32)
        # N, O, A: rise slowly out of a soft blur, one after another
        for i, k in enumerate(("N", "O", "A")):
            p = window(t, 0.7 + 0.5 * i, 2.6 + 0.5 * i)
            if p <= 0:
                continue
            s = big[k]
            e = ease_in_out(p)
            img = s.img
            sigma = 16 * (1 - ease_out(p, 2)) * unit
            if sigma > 0.3:
                img = cv2.GaussianBlur(img, (0, 0), sigma)
            blit_max(ink, img, s.x, s.y + int(round(22 * unit * (1 - ease_out(p, 2.5)))), e)
        # FUNERARE: letter by letter, the spacing gently closes in
        for i, s in enumerate(funer):
            p = window(t, 2.9 + 0.17 * i, 4.3 + 0.17 * i)
            if p <= 0:
                continue
            spread = 1 + 0.16 * (1 - ease_out(window(t, 2.9, 5.6), 2.2))
            lx = s.x + s.img.shape[1] / 2
            x = int(round(fun_cx + (lx - fun_cx) * spread - s.img.shape[1] / 2))
            img = s.img
            sigma = 5 * (1 - p) * unit
            if sigma > 0.3:
                img = cv2.GaussianBlur(img, (0, 0), sigma)
            blit_max(ink, img, x, s.y, smooth(p))

        dx, dy, tilt, zoom, wdeg = dove_state(t, W, H)
        d_line, d_fill = (dove.render(W, H, dx, dy, tilt, zoom, wdeg) if t >= FLY_START
                          else (np.zeros((H, W), np.float32),) * 2)
        # the dove fades in as it enters (it comes out of the darkness), lines always over its own dark body
        d_vis = smooth(window(t, FLY_START, FLY_START + 0.9))
        d_line *= d_vis
        d_fill *= d_vis

        # light sweep: a slow pale-gold band crossing the lettering (twice: after the reveal and after landing)
        sheen = np.zeros((H, W), np.float32)
        for t0, dur, strength in ((3.4, 2.4, 0.55), (8.3, 2.3, 0.75)):
            q = window(t, t0, t0 + dur)
            if 0 < q < 1:
                band_c = -0.25 * W + ease_in_out(q) * 1.5 * W
                d = (xx + 0.45 * yy) - band_c - 0.2 * H
                sheen += strength * np.exp(-(d / (0.07 * W)) ** 2) * math.sin(math.pi * q)

        img = bg.copy()
        img += motes.render(t)[..., None] * np.array([0.85, 0.82, 0.76], np.float32) * smooth(window(t, 0, 2.0))
        # soft halo behind the A when the dove lands
        h = smooth(window(t, LAND - 0.3, LAND + 0.9)) * (0.75 + 0.25 * math.cos(max(0, t - LAND) * 1.3))
        if h > 0:
            r2 = ((xx - a_glow_c[0]) ** 2 + (yy - a_glow_c[1]) ** 2) / (0.22 * W) ** 2
            img += (h * 0.055 * np.exp(-r2))[..., None] * np.array([1.0, 0.93, 0.8], np.float32)
        ink_col = INK * (1 - np.clip(sheen, 0, 1)[..., None]) + SHEEN * np.clip(sheen, 0, 1)[..., None]
        img = img * (1 - ink[..., None]) + ink_col * ink[..., None]
        # dove: its dark body hides what is behind it, then its white outline
        img = img * (1 - d_fill[..., None]) + bg * d_fill[..., None]
        img = img * (1 - d_line[..., None]) + ink_col * d_line[..., None]
        # bloom
        lum = np.maximum(ink, d_line)
        small = cv2.resize(lum, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bloom = cv2.resize(cv2.GaussianBlur(small, (0, 0), 6), (W, H))
        img += bloom[..., None] * np.array([0.16, 0.15, 0.13], np.float32)
        # fade from black, film grain
        img *= smooth(window(t, 0, 1.2))
        img += grain_rng.normal(0, 0.006, (H, W, 1)).astype(np.float32)
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

    if args.still is not None:
        Image.fromarray(frame(args.still)).save(out.replace(".mp4", f"_{args.still:.2f}.png"))
        return

    n = int(DURATION * args.fps)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(args.fps), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / args.fps).tobytes())
        if i % args.fps == 0:
            print(f"  {i / args.fps:4.1f}s / {DURATION:.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    print(out)


if __name__ == "__main__":
    main()
