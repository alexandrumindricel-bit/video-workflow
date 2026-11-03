#!/usr/bin/env python3
"""Join several separately cut clips into one work dir (multi-clip videos).

Each input is a clip work dir that already went through prepare -> transcribe -> (review) -> cut.
Output work dir gets: cut.mov (all clips in order), words.json and transcript.json (times offset, word
indices renumbered, "clip" field), segments.json (total duration), and layout.json whose "clips" list keeps
each clip's own face/zones - the renderer and fx.py use the framing of the clip that is on screen.

Usage: merge_clips.py OUT_WORK CLIP_WORK1 CLIP_WORK2 ...
"""
import json, os, subprocess, sys


def main():
    out, clips = sys.argv[1], sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    words, tw, segs, lay_clips = [], [], [], []
    t = 0.0
    inputs, parts = [], []
    for k, c in enumerate(clips):
        seg = json.load(open(os.path.join(c, "segments.json")))
        lay = json.load(open(os.path.join(c, "layout.json")))
        if not seg.get("sync_check", {}).get("ok"):
            sys.exit(f"{c}: cut sync check not OK - fix before merging")
        for w in json.load(open(os.path.join(c, "words.json"))):
            words.append({**w, "i": len(words), "src_i": w["i"], "clip": k,
                          "start": round(w["start"] + t, 3), "end": round(w["end"] + t, 3)})
        for w in json.load(open(os.path.join(c, "transcript.json")))["words"]:
            tw.append({**w, "clip": k})
        for g in seg["segments"]:
            segs.append({**g, "clip": k, "out_start": g["out_start"] + t, "out_end": g["out_end"] + t})
        lay_clips.append({"start": round(t, 4), "end": round(t + seg["duration"], 4), "src": os.path.basename(os.path.normpath(c)),
                          "face": lay.get("face"), "zones": lay["zones"]})
        inputs += ["-i", os.path.join(c, "cut.mov")]
        parts.append(f"[{k}:v][{k}:a]")
        t += seg["duration"]
    # concat filter (re-encode) - every clip is already 30 fps CFR / 48 kHz, frame-exact lengths
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex",
                    "".join(parts) + f"concat=n={len(clips)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-r", "30", "-c:a", "pcm_s16le",
                    os.path.join(out, "cut.mov")], check=True)
    base = json.load(open(os.path.join(clips[0], "layout.json")))
    base["clips"] = lay_clips
    json.dump(base, open(os.path.join(out, "layout.json"), "w"), indent=1)
    json.dump(words, open(os.path.join(out, "words.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"language": "multi", "words": tw}, open(os.path.join(out, "transcript.json"), "w"), ensure_ascii=False, indent=1)
    dv = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                               "-of", "csv=p=0", os.path.join(out, "cut.mov")], capture_output=True, text=True).stdout.strip() or 0)
    da = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration",
                               "-of", "csv=p=0", os.path.join(out, "cut.mov")], capture_output=True, text=True).stdout.strip() or 0)
    ok = abs(dv - da) <= 1 / 30 + 1e-3 and abs(dv - t) <= 2 / 30
    json.dump({"segments": segs, "duration": t, "sync_check": {"video": dv, "audio": da, "ok": ok}, "clips": lay_clips},
              open(os.path.join(out, "segments.json"), "w"), indent=1)
    print(f"merged {len(clips)} clips -> {t:.2f}s; clip starts: {[c['start'] for c in lay_clips]}; "
          f"sync video {dv:.3f}/audio {da:.3f} -> {'OK' if ok else 'MISMATCH'}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
