#!/usr/bin/env python3
"""Step 4: cut silences and mistakes - frame-accurate, lip-sync safe.

How lip sync is protected:
  * every cut point is snapped to the 30 fps frame grid, so each kept segment has exactly
    N video frames and exactly N*1600 audio samples (48 kHz) -> zero drift, however many cuts
  * video and audio are trimmed with the SAME timestamps in one filter graph
  * cut points are moved into the quietest nearby spot (never mid-word) and get 8 ms audio
    fades, so there are no clicks and no clipped consonants
  * a final check compares output audio vs video duration (must be within 1 frame)

Outputs: WORKDIR/cut.mp4, WORKDIR/words.json (kept words on the NEW timeline),
         WORKDIR/segments.json (source ranges kept + where each lands in the output)
Usage: cut.py WORKDIR
"""
import json, os, subprocess, sys, wave
import numpy as np

FPS = 30
SR = 48000


def load_rms(path, hop=0.01):
    with wave.open(path) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    h = int(sr * hop)
    n = len(x) // h
    rms = np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms), hop


def snap_quiet(t, db, hop, lo, hi, thresh):
    """Move t within [lo,hi] to the quietest 10ms frame (prefer staying close)."""
    a, b = int(max(lo, 0) / hop), int(min(hi, len(db) * hop) / hop)
    if b <= a:
        return t
    seg = db[a:b]
    cand = np.where(seg < thresh)[0]
    if len(cand):
        k = cand[np.argmin(np.abs((a + cand) * hop - t))]
    else:
        k = int(np.argmin(seg))
    return (a + k) * hop


def main():
    work = sys.argv[1]
    words = json.load(open(os.path.join(work, "transcript.json")))["words"]
    edit = json.load(open(os.path.join(work, "edit.json")))
    P = edit["params"]
    removed = set()
    for r in edit["remove"]:
        removed.update(range(r["from"], r["to"] + 1))
    removed -= set(edit.get("keep", []))
    kept = [w for w in words if w["i"] not in removed and w["end"] > w["start"]]
    if not kept:
        sys.exit("Nothing left to keep.")

    db, hop = load_rms(os.path.join(work, "audio16k.wav"))
    floor = np.percentile(db, 10)
    thresh = floor + 8  # "silence" = within 8 dB of the noise floor
    dur = len(db) * hop

    # Whisper often stretches a word over preceding silence (typically the first word starts at 0.00).
    # Move long word starts to the real voice onset, and long word ends back to where the voice stops.
    loud = np.percentile(db, 90)
    on_th = max(thresh + 4, loud - 22)
    for w in kept:
        if w["end"] - w["start"] > 0.35:
            a, b = int(w["start"] / hop), int(w["end"] / hop)
            voiced = np.where(db[a:b] > on_th)[0]
            if len(voiced):
                ns = (a + voiced[0]) * hop - 0.03
                ne = (a + voiced[-1] + 1) * hop + 0.03
                if ns - w["start"] > 0.12:
                    w["start"] = round(ns, 3)
                if w["end"] - ne > 0.25:
                    w["end"] = round(ne, 3)

    # group kept words into continuous runs (consecutive indices and short gaps)
    runs = []
    for w in kept:
        if runs and w["i"] == runs[-1][-1]["i"] + 1 and w["start"] - runs[-1][-1]["end"] <= P["max_gap"]:
            runs[-1].append(w)
        else:
            runs.append([w])

    segs = []
    for r in runs:
        s, e = r[0]["start"] - P["pad_before"], r[-1]["end"] + P["pad_after"]
        if P.get("snap_to_silence", True):
            s = snap_quiet(s, db, hop, s - 0.12, r[0]["start"] - 0.01, thresh)
            e = snap_quiet(e, db, hop, r[-1]["end"] + 0.02, e + 0.15, thresh)
        s, e = max(0.0, s), min(dur, e)
        segs.append([s, e, r])

    # tail: keep some picture after the last spoken word so the last caption can be read (only for the final clip
    # of a multi-clip video - set "tail": 0 on the others)
    tail = P.get("tail", 0.0)
    freeze = 0.0
    if tail and segs:
        want = segs[-1][1] + tail
        segs[-1][1] = min(dur, want)
        freeze = max(0.0, want - dur - 0.02)   # footage ends too soon -> hold the last frame (silence) for the rest

    # resolve overlaps (adjacent runs whose padding overlaps -> merge)
    merged = []
    for s, e, r in segs:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
            merged[-1][2] = merged[-1][2] + r
        else:
            merged.append([s, e, r])

    # snap to frame grid
    out_segments, words_out, t_out = [], [], 0.0
    for s, e, r in merged:
        fs, fe = int(round(s * FPS)), int(round(e * FPS))
        if fe <= fs:
            fe = fs + 1
        S, E = fs / FPS, fe / FPS
        out_segments.append({"src_start": S, "src_end": E, "out_start": t_out,
                             "out_end": t_out + (E - S), "first_word": r[0]["i"], "last_word": r[-1]["i"]})
        for w in r:
            words_out.append({"i": w["i"], "w": w["w"], "start": round(max(0, w["start"] - S) + t_out, 3),
                              "end": round(min(E, w["end"]) - S + t_out, 3), "p": w["p"]})
        t_out += E - S

    # ffmpeg graph
    src = os.path.join(work, "source.mov")
    parts, labels = [], []
    for k, sg in enumerate(out_segments):
        S, E = sg["src_start"], sg["src_end"]
        d = E - S
        fade = min(0.008, d / 4)
        parts.append(f"[0:v]trim=start={S:.6f}:end={E:.6f},setpts=PTS-STARTPTS[v{k}]")
        parts.append(f"[0:a]atrim=start={S:.6f}:end={E:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade:.4f},afade=t=out:st={d - fade:.6f}:d={fade:.4f}[a{k}]")
        labels.append(f"[v{k}][a{k}]")
    if freeze >= 1.0 / FPS:
        fz = round(freeze * FPS) / FPS
        parts.append("".join(labels) + f"concat=n={len(out_segments)}:v=1:a=1[vc][ac]")
        parts.append(f"[vc]tpad=stop_mode=clone:stop_duration={fz:.4f}[v]")
        parts.append(f"[ac]apad=pad_dur={fz:.4f}[a]")
        t_out += fz
    else:
        parts.append("".join(labels) + f"concat=n={len(out_segments)}:v=1:a=1[v][a]")
    graph_path = os.path.join(work, "cut_graph.txt")
    open(graph_path, "w").write(";\n".join(parts))
    out = os.path.join(work, "cut.mov")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-filter_complex_script", graph_path,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                    "-r", str(FPS), "-c:a", "pcm_s16le", out], check=True)

    # sync check
    def dur_of(stream):
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                            "stream=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout
        return float(o.strip() or 0)
    dv, da = dur_of("v:0"), dur_of("a:0")
    ok = abs(dv - da) <= 1.0 / FPS + 1e-3
    json.dump(words_out, open(os.path.join(work, "words.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"segments": out_segments, "duration": t_out, "source_duration": dur,
               "sync_check": {"video": dv, "audio": da, "ok": ok}},
              open(os.path.join(work, "segments.json"), "w"), indent=1)
    print(f"{len(out_segments)} segments kept: {dur:.1f}s -> {t_out:.1f}s "
          f"({100 * (1 - t_out / dur):.0f}% removed). Sync check: video {dv:.3f}s / audio {da:.3f}s -> "
          f"{'OK' if ok else 'MISMATCH'}")
    if not ok:
        sys.exit("ERROR: audio/video duration mismatch after cutting")


if __name__ == "__main__":
    main()
