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
}
TRANSITION_SFX = {"flash": ("shutter", -8), "leak": ("whoosh", -9), "glitch": ("glitch", -10),
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
    for s in sb.get("sfx", []):
        ev.append((s["at"], s["name"], s.get("gain_db", -10) + off))
    return sorted(ev)


def zoom_pieces(sb, dur):
    """Piecewise-constant zoom levels (punch-in jump cuts)."""
    zs = sorted(sb.get("zooms", []), key=lambda z: z["start"])
    pieces, t = [], 0.0
    for z in zs:
        s, e = max(t, z["start"]), min(dur, z["end"])
        if e <= s:
            continue
        if s > t:
            pieces.append((t, s, 1.0))
        pieces.append((s, e, z.get("scale", 1.1)))
        t = e
    if t < dur:
        pieces.append((t, dur, 1.0))
    # snap to frames
    return [(round(a * FPS) / FPS, round(b * FPS) / FPS, sc) for a, b, sc in pieces if round(b * FPS) > round(a * FPS)]


def main():
    work, out = sys.argv[1], sys.argv[2]
    sb = json.load(open(os.path.join(work, "storyboard.json")))
    seg = json.load(open(os.path.join(work, "segments.json")))
    layout = json.load(open(os.path.join(work, "layout.json")))
    dur = seg["duration"]
    face = layout.get("face")
    cx = (face["x"] + face["w"] / 2) if face else W / 2
    cy = (face["y"] + face["h"] / 2) if face else H * 0.4

    inputs = ["-i", os.path.join(work, "cut.mov"), "-i", os.path.join(work, "overlay.mov")]
    f = []
    # --- video: zoom pieces
    pieces = zoom_pieces(sb, dur)
    f.append(f"[0:v]split={len(pieces)}" + "".join(f"[zs{i}]" for i in range(len(pieces))))
    for i, (a, b, sc) in enumerate(pieces):
        cw, ch = int(W / sc) // 2 * 2, int(H / sc) // 2 * 2
        x = int(min(max(cx - cw / 2, 0), W - cw))
        y = int(min(max(cy - ch * 0.42, 0), H - ch))  # keep face slightly above center
        f.append(f"[zs{i}]trim=start={a:.6f}:end={b:.6f},setpts=PTS-STARTPTS,"
                 f"crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos,setsar=1[zp{i}]")
    f.append("".join(f"[zp{i}]" for i in range(len(pieces))) + f"concat=n={len(pieces)}:v=1:a=0[base0]")
    # --- glitch transitions
    v = "base0"
    for k, tr in enumerate([t for t in sb.get("transitions", []) if t["kind"] == "glitch"]):
        a, b = tr["at"] - 0.05, tr["at"] + tr.get("dur", 0.2)
        f.append(f"[{v}]rgbashift=rh=-16:bh=16:gv=4:enable='between(t,{a:.3f},{b:.3f})',"
                 f"noise=alls=28:allf=t:enable='between(t,{a:.3f},{b:.3f})'[g{k}]")
        v = f"g{k}"
    f.append(f"[{v}][1:v]overlay=0:0:format=auto:eof_action=pass,format=yuv420p[vout]")

    # --- audio
    f.append("[0:a]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2[voice]")
    mix = ["[voice]"]
    n_in = 2
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
          f"{len(events)} SFX, {len(pieces)} zoom pieces")


if __name__ == "__main__":
    main()
