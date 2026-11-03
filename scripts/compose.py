#!/usr/bin/env python3
"""Step 7: compose the final vertical video.

  cut.mov  --(punch-in zooms, glitch transitions)--> base
  base + overlay.mov (captions + graphics, alpha)  --> picture
  voice (cleaned) + SFX (auto + manual) + optional ducked music --> loudnorm -14 LUFS
  --> OUTPUT.mp4  (H.264 High, 1080x1920, 30 fps, AAC 192k, faststart)
Also writes WORKDIR/qa_sheet.jpg (one frame per second) for visual QA.

Usage: compose.py WORKDIR OUTPUT.mp4
"""
import json, os, subprocess, sys

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(HERE, "..", "sfx")

# default sound for each element type / transition kind  (name, gain dB)
AUTO_SFX = {
    "title": ("whoosh", -12), "card": ("pop", -10), "prompt": ("pop", -12), "strike": ("swoosh_down", -12),
    "counter": ("pop", -10), "step": ("click", -8), "list": ("click", -10), "stat": ("pop", -9),
    "comment": ("pop", -10), "follow": ("ding", -14), "image": ("pop", -10), "label": None, "frame": None,
    "flash": ("shutter", -8), "leak": ("whoosh", -10),
    "orbit": ("riser", -14), "wall": ("paper", -11), "app": ("pop", -10), "phone": ("pop", -10),
    "chart": ("riser", -14), "backdrop": ("whoosh", -11), "doodle": ("paper", -14), "tiles": ("click", -9),
    "glass": ("whoosh", -11), "cover": ("impact", -12), "checklist": ("pop", -10), "product3d": ("riser", -12),
    "combo": ("whoosh", -10), "photos": None, "numcards": None,
}
TRANSITION_SFX = {"zoom_through": ("whoosh", -7), "flash": ("shutter", -8), "leak": ("whoosh", -9), "glitch": ("glitch", -10),
                  "punch": None, "whoosh": ("whoosh", -9), "impact": ("impact", -8), "paper": ("paper", -8)}


def sfx_events(sb):
    ev = []
    off = sb.get("sfx_gain_db", 0)
    for el in sb.get("elements", []):
        spec = el.get("sfx", "auto")
        if spec is None or spec is False:
            continue
        if spec == "auto":
            d = AUTO_SFX.get(el["type"])
            if not d:
                continue
            name, g = d
        else:
            name, g = spec, -10
        ev.append((el["start"], name, g + off))
        if el["type"] == "product3d" and el.get("info", True) is not False:
            ev.append((el["start"] + el.get("info_at", 0.45), "ding", -15 + off))
            ev.append((el["start"] + 0.05, "whoosh", -12 + off))
        if el["type"] == "combo":
            ev.append((el["start"] + 0.08, "glitch", -16 + off))          # pixel squares
            if el.get("accent"):
                ev.append((el["start"] + 0.35, "swoosh_down", -15 + off))  # handwritten accent
        if el["type"] in ("photos", "numcards"):
            for j, it in enumerate(el.get("items", [])):
                at = it.get("at") if isinstance(it, dict) else None
                t0 = at if at is not None else el["start"] + j * el.get("stagger", 0.22 if el["type"] == "photos" else 0.3)
                ev.append((t0, "shutter" if el["type"] == "photos" else "click", (-12 if el["type"] == "photos" else -9) + off))
        if el["type"] == "strike":
            ev.append((el["start"] + el.get("strike_at", 0.45), "click", -12 + off))
        if el["type"] == "list":
            for j, it in enumerate(el["items"]):
                at = it.get("at") if isinstance(it, dict) else None
                ev.append((at if at is not None else el["start"] + j * el.get("stagger", 0.6), "click", -11 + off))
        if el["type"] in ("prompt", "comment") and el.get("typing_sfx", True):
            cps = el.get("cps", 24) if el["type"] == "prompt" else 12
            delay = 0.25 if el["type"] == "prompt" else 0.5
            n = len(el.get("text", ""))
            k = 0
            while k < n:
                t = el["start"] + delay + k / cps
                if t >= el["end"]:
                    break
                ev.append((t, "tick", -16 + off))
                k += 3
    for tr in sb.get("transitions", []):
        spec = tr.get("sfx", "auto")
        d = TRANSITION_SFX.get(tr["kind"]) if spec == "auto" else ((spec, -9) if spec else None)
        if d:
            ev.append((tr["at"], d[0], d[1] + off))
    EFFECT_SFX = {"pull_back": ("swoosh_down", -10), "frame_break": ("whoosh", -10), "vertigo": ("riser", -12),
                  "sticker": ("paper", -9), "outline": ("tick", -12), "push": None, "punch": None, "cutout": None}
    for e in sb.get("effects", []):
        spec = e.get("sfx", "auto")
        d = EFFECT_SFX.get(e["kind"]) if spec == "auto" else ((spec, -10) if spec else None)
        if d:
            ev.append((e["start"], d[0], d[1] + off))
    for s in sb.get("sfx", []):
        ev.append((s["at"], s["name"], s.get("gain_db", -10) + off))
    return sorted(ev)


def main():
    work, out = sys.argv[1], sys.argv[2]
    sb = json.load(open(os.path.join(work, "storyboard.json")))
    seg = json.load(open(os.path.join(work, "segments.json")))
    dur = seg["duration"]

    # video layers come from fx.py (camera effects + person cut-out) and render_overlay.cjs (back/front graphics)
    flags = json.load(open(os.path.join(work, "fx_flags.json")))
    inputs = ["-i", os.path.join(work, "cut.mov"), "-i", os.path.join(work, "fx_bg.mov"),
              "-i", os.path.join(work, "overlay.mov")]
    n_in = 3
    f = []
    v = "1:v"
    # --- glitch transitions (on the background plate)
    for k, tr in enumerate([t for t in sb.get("transitions", []) if t["kind"] == "glitch"]):
        a, b = tr["at"] - 0.05, tr["at"] + tr.get("dur", 0.2)
        f.append(f"[{v}]rgbashift=rh=-16:bh=16:gv=4:enable='between(t,{a:.3f},{b:.3f})',"
                 f"noise=alls=28:allf=t:enable='between(t,{a:.3f},{b:.3f})'[g{k}]")
        v = f"g{k}"
    f.append(f"[{v}]format=yuv444p[L0]"); v = "L0"
    if os.path.exists(os.path.join(work, "overlay_back.mov")):
        inputs += ["-i", os.path.join(work, "overlay_back.mov")]
        f.append(f"[{v}][{n_in}:v]overlay=0:0:format=auto:eof_action=pass[L1]"); v = "L1"; n_in += 1
    if flags.get("person"):
        if flags.get("sticker"):
            inputs += ["-i", os.path.join(work, "fx_sticker.mkv")]
            f.append(f"color=c=white:s={W}x{H}:r={FPS}:d={dur:.3f}[wst];[wst][{n_in}:v]alphamerge[stk]")
            f.append(f"[{v}][stk]overlay=0:0:format=auto[L2]"); v = "L2"; n_in += 1
        inputs += ["-i", os.path.join(work, "fx_person.mov"), "-i", os.path.join(work, "fx_matte.mkv")]
        f.append(f"[{n_in}:v][{n_in + 1}:v]alphamerge[per]")
        f.append(f"[{v}][per]overlay=0:0:format=auto[L3]"); v = "L3"; n_in += 2
        if flags.get("outline"):
            col = next((e.get("color", "white") for e in sb.get("effects", []) if e["kind"] == "outline"), "white")
            inputs += ["-i", os.path.join(work, "fx_outline.mkv")]
            f.append(f"color=c={col}:s={W}x{H}:r={FPS}:d={dur:.3f}[olc];[olc][{n_in}:v]alphamerge[oln]")
            f.append(f"[{v}][oln]overlay=0:0:format=auto[L4]"); v = "L4"; n_in += 1
    f.append(f"[{v}][2:v]overlay=0:0:format=auto:eof_action=pass,format=yuv420p[vout]")

    # --- audio
    f.append("[0:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2[voice]")
    mix = ["[voice]"]
    events = [e for e in sfx_events(sb) if 0 <= e[0] < dur]
    for k, (t, name, g) in enumerate(events):
        p = os.path.join(SFX_DIR, name + ".wav")
        if not os.path.exists(p):
            print(f"WARNING: missing SFX {name}.wav - skipped")
            continue
        inputs += ["-i", p]
        ms = int(t * 1000)
        f.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume={g}dB[s{k}]")
        mix.append(f"[s{k}]")
        n_in += 1
    music = sb.get("music")
    if music and music.get("file"):
        inputs += ["-stream_loop", "-1", "-i", music["file"]]
        f.append(f"[voice]asplit=2[vmix][vkey]")
        mix[0] = "[vmix]"
        f.append(f"[{n_in}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur:.3f},"
                 f"volume={music.get('gain_db', -18)}dB,afade=t=out:st={max(0, dur - 1.5):.3f}:d=1.5[mus]")
        f.append("[mus][vkey]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck]")
        mix.append("[duck]")
        n_in += 1
    f.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
             "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    graph = os.path.join(work, "compose_graph.txt")
    open(graph, "w").write(";\n".join(f))
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex_script", graph,
           "-map", "[vout]", "-map", "[aout]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "18", "-r", str(FPS),
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)

    # QA
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", out, "-vf",
                    "fps=1,scale=216:-2,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black,"
                    f"tile=8x{max(1, int(dur) // 8 + 1)}", "-frames:v", "1", os.path.join(work, "qa_sheet.jpg")], check=False)
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", out],
                                   capture_output=True, text=True).stdout)
    vs = next(s for s in pr["streams"] if s["codec_type"] == "video")
    au = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    print(f"DONE {out}: {vs['width']}x{vs['height']} {vs['codec_name']} {vs['r_frame_rate']} fps, "
          f"audio {au['codec_name']} {au['sample_rate']} Hz, {float(pr['format']['duration']):.2f}s, "
          f"{len(events)} SFX")


if __name__ == "__main__":
    main()
