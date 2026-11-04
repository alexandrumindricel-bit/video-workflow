#!/usr/bin/env python3
"""Fetch a product from mindricel.ro and cut it out for the 3D product presentation.

  product.py catalog                     -> products/catalog.json (all products: name, url, price, image)
  product.py fetch <url-or-slug> [WORK]  -> products/<slug>/{meta.json, view_0.png, view_1.png, ...}
                                            (and copies meta into WORK/products/<slug> if WORK is given)

Data comes from the product page's schema.org JSON-LD (name, price, currency, sizes, category, description,
images). Each image is cut out (background removed); product photos that show several angles side by side
are split into one transparent PNG per angle ("views") - the 3D element turns between them like a turntable.
www.mindricel.ro is rewritten to mindricel.ro (same site; the www host may be blocked by the network policy).
"""
import json, os, re, sys, urllib.request
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "products")
BASE = "https://mindricel.ro"
UA = {"User-Agent": "video-workflow/1.0 (product presentation)"}


def get(url, binary=False):
    url = re.sub(r"^https?://(www\.)?mindricel\.ro", BASE, url)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def jsonld_product(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        for item in (d if isinstance(d, list) else [d]):
            if item.get("@type") == "Product":
                return item
    return None


def slug_of(u):
    m = re.search(r"/produs/([^/?#]+)", u)
    return m.group(1) if m else u.strip("/").split("/")[-1]


# ---------------------------------------------------------------- cut-out
def cutout(img_bgr):
    """Return (alpha float32 0..1, quality 'good'|'low', notes)."""
    H, W = img_bgr.shape[:2]
    s = 900 / max(H, W)
    small = cv2.resize(img_bgr, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
    h, w = small.shape[:2]
    b = max(4, int(min(h, w) * 0.02))
    border = np.concatenate([small[:b].reshape(-1, 3), small[-b:].reshape(-1, 3),
                             small[:, :b].reshape(-1, 3), small[:, -b:].reshape(-1, 3)]).astype(np.float32)
    bg = np.median(border, 0)
    # "flat" background = most border pixels close to the median colour (shadows touching the edge are fine)
    flat = float(np.mean(np.linalg.norm(border - bg, axis=1) < 22)) > 0.8
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB).astype(np.float32)
    bg_lab = cv2.cvtColor(bg.reshape(1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(3).astype(np.float32)
    # chroma differences count more than lightness ones (soft grey shadows differ mostly in lightness)
    d = np.sqrt(0.35 * (lab[..., 0] - bg_lab[0]) ** 2 + (lab[..., 1] - bg_lab[1]) ** 2 + (lab[..., 2] - bg_lab[2]) ** 2)
    notes = []
    gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    if flat:
        dL = bg_lab[0] - lab[..., 0]                                   # >0 = darker than the background
        dc = np.sqrt((lab[..., 1] - bg_lab[1]) ** 2 + (lab[..., 2] - bg_lab[2]) ** 2)
        gc[d > 14] = cv2.GC_PR_FGD
        gc[(dc > 18) | (dL > 95)] = cv2.GC_FGD                        # clearly coloured or very dark = product
        # soft grey shadow: neutral and only somewhat darker -> probably background
        shadow = (dc < 7) & (dL > 0) & (dL < 60)
        # ...unless it has texture/edges (grey products are textured, shadows are smooth)
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        tex = cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3)), (0, 0), 3)
        gc[shadow & (tex < 6)] = cv2.GC_PR_BGD
        gc[d < 5] = cv2.GC_BGD
    else:
        notes.append("non-uniform background")
        m = int(min(h, w) * 0.04)
        gc[:] = cv2.GC_BGD
        gc[m:h - m, m:w - m] = cv2.GC_PR_FGD
        gc[d > 60] = np.where(gc[d > 60] == cv2.GC_BGD, cv2.GC_BGD, cv2.GC_PR_FGD)
    gc[:b], gc[-b:], gc[:, :b], gc[:, -b:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
    bgm, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(small, gc, None, bgm, fgm, 6, cv2.GC_INIT_WITH_MASK)
    except cv2.error:
        notes.append("grabcut failed")
    mask = np.isin(gc, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    # reconnect thin parts (goggle frames, straps) that the colour test broke apart
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(5, int(0.025 * max(h, w))) | 1,) * 2)
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kc)
    # fill enclosed holes unless they are real background (plain + background colour, e.g. a key-ring hole);
    # reflective / silver parts (mirror lenses) differ from the background or have texture -> part of the product
    cs, hier = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is not None:
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
        for i, c in enumerate(cs):
            if hier[0][i][3] < 0:
                continue
            hole = np.zeros((h, w), np.uint8); cv2.drawContours(hole, cs, i, 255, -1)
            sel = hole > 0
            if not sel.any():
                continue
            real_bg = float(d[sel].mean()) < 12          # close to the background colour -> a real hole (key-ring)
            if cv2.contourArea(c) < 0.002 * h * w or not real_bg:
                fill = (hole > 0) & (closed == 0) | (hole > 0) & (mask == 0)
                mask[fill] = 255                         # add only the hole, never the closing's bridge pixels
    frac = mask.mean() / 255
    quality = "good" if flat and 0.03 < frac < 0.85 else "low"
    if not flat:
        notes.append("cut-out may include background - check it, or use the photo-card mode")
    alpha = cv2.resize(mask, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)
    return alpha, quality, notes


def split_views(img, alpha, min_frac=0.06):
    """Split the cut-out into separate objects (e.g. 3 angles of one helmet), ordered left->right, top->bottom."""
    H, W = alpha.shape
    bin_ = (alpha > 0.5).astype(np.uint8)
    # drop small separate fragments (model-code labels like "C47", logos, specks): islands < min_frac of the
    # product area, measured after a light dilation so pieces of the same object stay together
    near = cv2.dilate(bin_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * max(3, int(0.008 * max(H, W))) + 1,) * 2))
    nI, isl = cv2.connectedComponents(near)
    tot0 = max(1, bin_.sum())
    for i in range(1, nI):
        m = isl == i
        if bin_[m].sum() / tot0 < min_frac:
            bin_[m] = 0
            alpha = alpha * (~m)
    total = bin_.sum()
    # seeds = the mask eroded until touching objects come apart; then a watershed on the photo assigns every
    # product pixel to the nearest seed along the strongest image edges
    r = max(7, int(0.018 * max(H, W)))
    seeds_bin = cv2.erode(bin_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    n0, seeds = cv2.connectedComponentsWithStats(seeds_bin)[:2]
    keep = [i for i in range(1, n0) if (seeds == i).sum() > 0.02 * total]
    markers = np.zeros((H, W), np.int32)
    for j, i in enumerate(keep, start=1):
        markers[seeds == i] = j
    markers[alpha < 0.1] = len(keep) + 1  # background
    if len(keep) > 1:
        cv2.watershed(img, markers)
        lbl = np.where(bin_ > 0, markers, 0)
        lbl[lbl == len(keep) + 1] = 0
        lbl[lbl < 0] = 0
    else:
        lbl = bin_.astype(np.int32)
    n = (len(keep) if len(keep) > 1 else 1) + 1
    stats = np.zeros((n, 5), np.int64)
    for i in range(1, n):
        ys, xs = np.nonzero(lbl == i)
        if len(xs):
            stats[i] = [xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, len(xs)]
    comps = [i for i in range(1, n) if stats[i][4] / max(1, total) > min_frac]
    # safety: thin parts (cables, straps) can be flooded by the background seed - if the split views no longer
    # cover the product, fall back to plain connected components of the full mask (nothing gets lost)
    if sum(stats[i][4] for i in comps) < 0.85 * total:
        n, lbl, stats, _ = cv2.connectedComponentsWithStats(bin_)
        comps = [i for i in range(1, n) if stats[i][4] / max(1, total) > min_frac]
    comps.sort(key=lambda i: (round(stats[i][1] / (H / 3)), stats[i][0]))
    views = []
    for i in comps:
        x, y, w, h = stats[i][:4]
        p = int(0.03 * max(w, h))
        x0, y0, x1, y1 = max(0, x - p), max(0, y - p), min(W, x + w + p), min(H, y + h + p)
        a = alpha[y0:y1, x0:x1] * (lbl[y0:y1, x0:x1] == i)
        rgba = np.dstack([img[y0:y1, x0:x1], (a * 255).astype(np.uint8)])
        sc = 1000 / max(rgba.shape[:2])
        if sc < 1:
            rgba = cv2.resize(rgba, (int(rgba.shape[1] * sc), int(rgba.shape[0] * sc)), interpolation=cv2.INTER_AREA)
        views.append(rgba)
    return views


def fetch(target, work=None):
    url = target if target.startswith("http") else f"{BASE}/produs/{target}"
    slug = slug_of(url)
    html = get(url)
    p = jsonld_product(html)
    if not p:
        sys.exit(f"No product data found on {url}")
    out = os.path.join(ROOT, slug)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):  # clear outputs of a previous fetch
        if re.match(r"(view_\d+\.png|photo_\d+\.jpg|source_\d+\.img|qa_cutout\.jpg)$", f):
            os.remove(os.path.join(out, f))
    offers = p.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0]
    meta = {"slug": slug, "url": re.sub(r"^https?://(www\.)?", "https://", url), "name": p.get("name", "").strip(),
            "description": p.get("description", ""), "category": p.get("category"),
            "brand": (p.get("brand") or {}).get("name") if isinstance(p.get("brand"), dict) else p.get("brand"),
            "price": offers.get("price"), "currency": offers.get("priceCurrency", "RON"),
            "in_stock": "InStock" in str(offers.get("availability", "")),
            "sizes": p.get("size") or [], "images": [], "views": [], "quality": "good", "notes": []}
    imgs = p.get("image") or []
    imgs = [imgs] if isinstance(imgs, str) else imgs
    for k, iu in enumerate(imgs):
        raw = get(iu if iu.startswith("http") else BASE + iu, binary=True)
        src = os.path.join(out, f"source_{k}.img")
        open(src, "wb").write(raw)
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            meta["notes"].append(f"could not decode {iu}")
            continue
        cv2.imwrite(os.path.join(out, f"photo_{k}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        meta["images"].append(f"photo_{k}.jpg")
        alpha, q, notes = cutout(img)
        meta["notes"] += notes
        if q == "low":
            meta["quality"] = "low"
        for v in split_views(img, alpha):
            name = f"view_{len(meta['views'])}.png"
            cv2.imwrite(os.path.join(out, name), v)
            meta["views"].append(name)
    if not meta["views"]:
        meta["quality"] = "low"
        meta["notes"].append("no object found - use the photo-card mode")
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), ensure_ascii=False, indent=1)
    # contact sheet of the cut-outs on a checkerboard, for QA
    tiles = []
    for v in meta["views"]:
        im = cv2.imread(os.path.join(out, v), cv2.IMREAD_UNCHANGED)
        sc = 360 / im.shape[0]
        im = cv2.resize(im, (max(1, int(im.shape[1] * sc)), 360))
        yy, xx = np.mgrid[:360, :im.shape[1]]
        chk = np.where(((yy // 20 + xx // 20) % 2)[..., None] == 0, 200, 140).astype(np.uint8).repeat(3, 2)
        a = im[..., 3:4].astype(np.float32) / 255
        tiles.append((im[..., :3] * a + chk * (1 - a)).astype(np.uint8))
    if tiles:
        cv2.imwrite(os.path.join(out, "qa_cutout.jpg"), cv2.hconcat(tiles))
    if work:
        dst = os.path.join(work, "products")
        os.makedirs(dst, exist_ok=True)
        link = os.path.join(dst, slug)
        if not os.path.exists(link):
            os.symlink(os.path.abspath(out), link)
    print(json.dumps({k: meta[k] for k in ("name", "price", "currency", "sizes", "views", "quality", "notes")}, ensure_ascii=False))
    print("QA sheet:", os.path.join(out, "qa_cutout.jpg"))
    return meta


def catalog():
    xml = get(BASE + "/sitemap.xml")
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", xml) if "/produs/" in u]
    items = []
    for u in urls:
        try:
            p = jsonld_product(get(u))
        except Exception as e:
            print("skip", u, e)
            continue
        if not p:
            continue
        offers = p.get("offers") or {}
        items.append({"slug": slug_of(u), "url": u, "name": p.get("name", "").strip(), "category": p.get("category"),
                      "price": offers.get("price") if isinstance(offers, dict) else None})
    os.makedirs(ROOT, exist_ok=True)
    json.dump(items, open(os.path.join(ROOT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    for it in items:
        print(f"{it['slug']:55s} {it['price']!s:>6} | {it['name']}")
    print(len(items), "products ->", os.path.join(ROOT, "catalog.json"))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "catalog":
        catalog()
    elif len(sys.argv) >= 3 and sys.argv[1] == "fetch":
        fetch(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
        sys.exit(1)
