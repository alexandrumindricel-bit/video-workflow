#!/usr/bin/env python3
"""Fetch illustrative images from the internet for what is said in the video (free / CC licensed only).

  images.py WORK "search words" --name NAME [--n 3] [--source auto|openverse|wikimedia]

Sources (no API keys):
  * Openverse  (api.openverse.org)  - CC / public-domain images; thumbnails are served by api.openverse.org itself
  * Wikimedia Commons (commons.wikimedia.org + upload.wikimedia.org) - fallback
Only licences that allow commercial use and modification are requested. Each image is center-cropped to a
4:5 card (540x675) -> WORK/images/NAME_k.jpg, and author/licence/source go to WORK/images/credits.json and
credits.txt (put the credits in the post description when a licence requires attribution, e.g. CC BY).
ALWAYS look at the downloaded images before using them (relevance, no watermarks/faces of strangers/logos misuse).
"""
import argparse, io, json, os, re, sys, urllib.parse, urllib.request

UA = {"User-Agent": "video-workflow/1.0 (short-form video editor; contact via repo)"}


def get(url, binary=False, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        d = r.read()
    return d if binary else json.loads(d.decode("utf-8"))


def openverse(q, n):
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "license_type": "commercial,modification", "page_size": max(10, n * 4), "mature": "false"})
    out = []
    for r in get(url).get("results", []):
        if (r.get("width") or 0) < 400:
            continue
        out.append({"thumb": f"https://api.openverse.org/v1/images/{r['id']}/thumb/", "full": r.get("url"),
                    "title": r.get("title"), "creator": r.get("creator"), "license": f"{r.get('license', '').upper()} {r.get('license_version') or ''}".strip(),
                    "source": r.get("foreign_landing_url"), "provider": "Openverse/" + str(r.get("source"))})
    return out


def wikimedia(q, n):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": f"filetype:bitmap {q}", "gsrnamespace": 6,
        "gsrlimit": max(10, n * 4), "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 800, "format": "json"})
    out = []
    for p in (get(url).get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if not re.search(r"(CC0|Public domain|CC BY|CC-BY)", lic, re.I) or re.search(r"NC|ND", lic):
            continue
        artist = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
        out.append({"thumb": ii.get("thumburl"), "full": ii.get("url"), "title": p.get("title"), "creator": artist,
                    "license": lic, "source": ii.get("descriptionurl"), "provider": "Wikimedia Commons"})
    return out


def card(raw, path):
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    W, H = 540, 675
    sc = max(W / im.width, H / im.height)
    im = im.resize((max(W, int(im.width * sc)), max(H, int(im.height * sc))), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 3
    im.crop((x, y, x + W, y + H)).save(path, quality=90)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work"); ap.add_argument("query")
    ap.add_argument("--name", required=True); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--source", default="auto")
    a = ap.parse_args()
    d = os.path.join(a.work, "images"); os.makedirs(d, exist_ok=True)
    cands, errors = [], []
    for src in (["openverse", "wikimedia"] if a.source == "auto" else [a.source]):
        try:
            cands = (openverse if src == "openverse" else wikimedia)(a.query, a.n)
            if cands:
                break
        except Exception as e:
            errors.append(f"{src}: {e}")
    if not cands:
        sys.exit("No images. " + ("; ".join(errors) if errors else "") +
                 "\nIf the network blocks it, allow api.openverse.org (or commons.wikimedia.org + upload.wikimedia.org).")
    credits_p = os.path.join(d, "credits.json")
    credits = json.load(open(credits_p)) if os.path.exists(credits_p) else []
    saved = []
    for c in cands:
        if len(saved) >= a.n:
            break
        try:
            raw = get(c["thumb"], binary=True)
            path = os.path.join(d, f"{a.name}_{len(saved)}.jpg")
            card(raw, path)
        except Exception as e:
            errors.append(str(e)); continue
        saved.append(path)
        credits.append({**c, "file": os.path.basename(path), "query": a.query})
    json.dump(credits, open(credits_p, "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(d, "credits.txt"), "w") as f:
        for c in credits:
            f.write(f"{c['file']}: \"{c.get('title') or ''}\" by {c.get('creator') or 'unknown'} - {c.get('license')} - {c.get('source')}\n")
    print(json.dumps({"saved": saved, "errors": errors[:3]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
