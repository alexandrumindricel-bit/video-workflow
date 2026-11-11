import cv2, numpy as np, sys
rng = np.random.default_rng(7)
D = sys.argv[1]
im = cv2.imread(f'{D}/hero.jpg').astype(np.float32)
H, W = im.shape[:2]

def poly_mask(pts, dil=0):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 255)
    if dil: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*dil+1, 2*dil+1)))
    return m > 0

def bez(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return ((1-t)**3*np.array(p0) + 3*(1-t)**2*t*np.array(p1) + 3*(1-t)*t**2*np.array(p2) + t**3*np.array(p3)).tolist()

# --- helmet (traced by hand) ---
helmet = poly_mask([[0,912],[60,890],[150,867],[280,858],[420,872],[500,902],[545,935],[565,985],[580,1060],[586,1150],[588,1232],[574,1272],[548,1292],[528,1300],[540,1340],[548,1462],[0,1462]], dil=7)

# --- hat geometry (same coords as hat2.html) ---
brim_top = bez([48,1222],[200,1188],[400,1182],[556,1196])
brim_bot = bez([560,1292],[400,1312],[200,1322],[44,1306])
brim = poly_mask(brim_top + brim_bot)
red = cv2.imread(f'{D}/red.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
red_a = red[..., 3:] / 255.0
pom_c, pom_r = (92, 1158), 58
pom = np.zeros((H, W), np.uint8); cv2.circle(pom, pom_c, pom_r, 255, -1); pom = pom > 0
hat = (red_a[..., 0] > 0.02) | brim | pom

# below the brim: real hood/neck exists on the right (x>345); mirror it to the left -> neck + left shoulder
yy, xx = np.mgrid[0:H, 0:W]
bot = np.interp(xx, [p[0] for p in brim_bot[::-1]], [p[1] for p in brim_bot[::-1]])
below = helmet & ~hat & (yy > bot - 25)
shoulder = poly_mask([[120,1280],[560,1280],[560,1470],[0,1470],[0,1372],[60,1352],[128,1336]])
hood = below & shoulder
gap = helmet & ~hat & ~hood                 # background to rebuild
out = im.copy()

# hood/neck: mirror about x=345 (continuous with the real hood), darken a bit, soft shadow under the brim
MX = 690
src_x = np.clip(MX - xx, 0, W - 1)
mir = im[yy, src_x]
mir = cv2.GaussianBlur(mir, (0, 0), 1.0)
out[hood] = mir[hood] * 0.92
sh = np.zeros((H, W), np.float32); cv2.fillPoly(sh, [np.array(brim_bot + [[560,1335],[44,1350]], np.int32)], 1.0)
sh = cv2.GaussianBlur(sh, (0, 0), 12)[..., None]
out = np.where(hood[..., None], out * (1 - 0.55 * sh), out)

# background: per row, mirror about the helmet's right edge (continuous seam) for the band above/right of the hat;
# left strip (left of the hat) copies the river right of the helmet
R = np.array([(np.where(helmet[y])[0].max() if helmet[y].any() else 0) for y in range(H)])
for y in range(H):
    xs = np.where(gap[y])[0]
    if not len(xs): continue
    for sgm in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1):
        if sgm[-1] >= R[y] - 2 or sgm[0] > 200:      # touches right edge, or above the hat
            src = 2 * (R[y] + 1) - sgm
        else:                                        # left strip
            src = sgm + R[y] + 14
        out[y, sgm] = im[y, np.clip(src, 0, W - 1)]
# small leftovers below the brim on the far left (rack bar would be copied there): inpaint
left_low = gap & (yy > 1290)
if left_low.any():
    out8 = np.clip(out, 0, 255).astype(np.uint8)
    out = cv2.inpaint(out8, left_low.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32)
# feather the rebuilt area into the original
fm = cv2.GaussianBlur((gap | hood).astype(np.float32), (0, 0), 2.0)
bandb = np.clip((yy - 1440) / 30.0, 0, 1) * (xx < 560)
fm = (fm * (1 - bandb))[..., None]
out = im * (1 - fm) + out * fm

# --- red fleece ---
rgb = red[..., :3]
# fleece micro-texture
n1 = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.0)
n2 = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 6.0)
tex = 1 + 0.06 * n1 / n1.std() + 0.035 * n2 / n2.std()
rgb = rgb * tex[..., None]
out = out * (1 - red_a) + rgb * red_a

# --- fur (brim + pompom): thousands of short strands ---
snow = np.array([238, 236, 232], np.float32)  # BGR, close to the photo's lit snow
def fur(mask, shade, n, lmin, lmax, radial=None, spill=7):
    layer = np.zeros((H, W, 3), np.float32); alpha = np.zeros((H, W), np.float32)
    base = cv2.erode(mask.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    sm = shade[..., None] * snow
    pts = np.argwhere(cv2.dilate(mask.astype(np.uint8), np.ones((2*spill+1,)*2, np.uint8)) > 0)
    pick = pts[rng.integers(0, len(pts), n)]
    for (y, x) in pick:
        if radial is not None:
            ang = np.arctan2(y - radial[1], x - radial[0]) + rng.normal(0, 0.6)
        else:
            ang = rng.uniform(0, 2*np.pi)
        L = rng.uniform(lmin, lmax)
        x2, y2 = int(x + L*np.cos(ang)), int(y + L*np.sin(ang))
        yc, xc = min(max(y, 0), H-1), min(max(x, 0), W-1)
        v = sm[yc, xc] * rng.uniform(0.72, 1.06)
        cv2.line(layer, (x, y), (x2, y2), tuple(float(c) for c in v), 1, cv2.LINE_AA)
        cv2.line(alpha[..., None] if False else alpha, (x, y), (x2, y2), 1.0, 1, cv2.LINE_AA)
    # dense underlayer
    bl = cv2.GaussianBlur(base.astype(np.float32), (0, 0), 2.5)
    under = sm * (0.9 + 0.1 * n1[..., None])
    a = np.clip(alpha, 0, 1)
    col = np.where(a[..., None] > 0, layer / np.maximum(a[..., None], 1e-3), under)
    A = np.clip(np.maximum(bl, a * 0.9), 0, 1)
    col = cv2.GaussianBlur(col, (0, 0), 0.6)
    return col, cv2.GaussianBlur(A, (0, 0), 0.7)

# brim shading: lit from above, darker underside and toward the edges, lumpy
top = np.interp(xx, [p[0] for p in brim_top], [p[1] for p in brim_top])
t = np.clip((yy - top) / np.maximum(bot - top, 1), 0, 1)
lump = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 9); lump /= lump.std()
side = 1 - 0.25 * np.clip((180 - xx) / 180, 0, 1) - 0.12 * np.clip((xx - 470) / 90, 0, 1)
lump2 = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 4); lump2 /= lump2.std()
shade_b = (1.02 - 0.42 * t**1.5) * side * (1 + 0.10 * lump + 0.06 * lump2)
col, A = fur(brim, shade_b.astype(np.float32), 70000, 5, 15)
out = out * (1 - A[..., None]) + col * A[..., None]

# pompom: soft shadow on the hat, radial strands
ps = np.zeros((H, W), np.float32); cv2.circle(ps, (pom_c[0] + 14, pom_c[1] + 20), pom_r, 1.0, -1)
ps = cv2.GaussianBlur(ps, (0, 0), 16)
out = out * (1 - 0.45 * ps[..., None] * (hat & ~pom)[..., None])
d = np.sqrt((xx - pom_c[0] + 18)**2 + (yy - pom_c[1] + 22)**2) / (pom_r * 1.7)
shade_p = np.clip(1.02 - 0.55 * d**1.5, 0.35, 1) * (1 + 0.06 * lump)
col, A = fur(pom, shade_p.astype(np.float32), 16000, 4, 11, radial=pom_c, spill=6)
out = out * (1 - A[..., None]) + col * A[..., None]

# --- match the phone camera: slight softness + its grain, on everything we touched ---
touched = cv2.dilate((helmet | hat).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
soft = cv2.GaussianBlur(out, (0, 0), 0.7)
grain = rng.normal(0, 3.2, (H, W, 1)).astype(np.float32) + rng.normal(0, 1.2, (H, W, 3)).astype(np.float32)
res = im.copy()
res[touched] = np.clip(soft + grain, 0, 255)[touched]
cv2.imwrite(f'{D}/hero-santa.jpg', res.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
cv2.imwrite(f'{D}/hatcrop.jpg', res[700:1600, 0:1000].astype(np.uint8))
