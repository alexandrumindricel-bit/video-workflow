#!/usr/bin/env python3
"""Synthesize the short SFX library used on transitions and graphic entries.

All sounds are generated procedurally (no downloads), 48 kHz mono WAV, peak ~ -3 dBFS.
To use your own sounds instead, drop a WAV with the same name into sfx/ and run with
--keep-existing (setup.sh does this), so your files are never overwritten.
"""
import argparse, os, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def env(n, attack=0.005, release=None, curve=4.0):
    t = np.linspace(0, 1, n)
    a = max(1, int(attack * SR))
    e = np.exp(-curve * t)
    e[:a] *= np.linspace(0, 1, a)
    return e


def bandpass_noise(n, lo, hi):
    x = rng.standard_normal(n)
    f = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, n)


def sweep_noise(dur, f0, f1, bw=0.6):
    """Noise whose band center sweeps f0->f1 (block-wise STFT filtering)."""
    n = int(dur * SR)
    out = np.zeros(n)
    blk = 1024
    win = np.hanning(blk * 2)
    for i in range(0, n, blk):
        c = f0 * (f1 / f0) ** (i / n)
        seg = bandpass_noise(blk * 2, c * (1 - bw / 2), c * (1 + bw / 2)) * win
        out[i:i + blk * 2] += seg[: len(out[i:i + blk * 2])]
    return out


def norm(x, peak_db=-3.0):
    x = x - np.mean(x)
    m = np.max(np.abs(x)) or 1
    return x / m * 10 ** (peak_db / 20)


def whoosh(dur=0.45, f0=300, f1=4500):
    n = int(dur * SR)
    x = sweep_noise(dur, f0, f1)[:n]
    t = np.linspace(0, 1, n)
    e = np.sin(np.pi * t ** 0.7) ** 2
    return norm(x * e, -4)


def swoosh_down():
    return whoosh(0.4, 5000, 400)


def pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 35) + 300
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, curve=9)
    return norm(x, -5)


def click():
    n = int(0.03 * SR)
    x = bandpass_noise(n, 2000, 9000) * env(n, 0.0005, curve=14)
    return norm(x, -6)


def tick():  # keyboard / typing tick
    n = int(0.025 * SR)
    x = bandpass_noise(n, 1500, 6000) * env(n, 0.0005, curve=16)
    t = np.arange(n) / SR
    x += 0.4 * np.sin(2 * np.pi * 2200 * t) * env(n, 0.0005, curve=20)
    return norm(x, -10)


def shutter():
    a = click()
    gap = np.zeros(int(0.06 * SR))
    b = bandpass_noise(int(0.05 * SR), 1200, 7000) * env(int(0.05 * SR), 0.001, curve=10)
    return norm(np.concatenate([a, gap, norm(b, -6)]), -4)


def impact():  # bass hit / boom
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 6) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    hit = bandpass_noise(n, 80, 3000) * np.exp(-t * 30) * 0.5
    x = np.tanh((body + hit) * 2.2)
    return norm(x, -2)


def riser(dur=1.0):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = sweep_noise(dur, 400, 7000, bw=0.4)[:n] * t ** 2
    f = 200 + 900 * t ** 2
    x += 0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * t ** 2
    return norm(x, -5)


def glitch():
    parts = []
    for _ in range(7):
        n = int(rng.uniform(0.012, 0.035) * SR)
        if rng.random() < 0.5:
            t = np.arange(n) / SR
            seg = np.sign(np.sin(2 * np.pi * rng.uniform(200, 1800) * t))
        else:
            seg = bandpass_noise(n, 500, 8000)
        parts.append(seg * rng.uniform(0.4, 1))
    return norm(np.concatenate(parts) * env(sum(len(p) for p in parts), 0.001, curve=2), -6)


def ding():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(1318, 1), (2637, 0.4), (3951, 0.15)])
    return norm(x * np.exp(-t * 7) * env(n, 0.002, curve=0), -8)


def paper():
    n = int(0.35 * SR)
    x = np.zeros(n)
    for _ in range(40):
        p = int(rng.uniform(0, n - 600))
        m = int(rng.uniform(80, 500))
        x[p:p + m] += bandpass_noise(m, 1500, 10000) * rng.uniform(0.2, 1)
    t = np.linspace(0, 1, n)
    return norm(x * np.sin(np.pi * t) ** 0.5, -6)


# ---- sound set modelled on the "Essential SFX" reference (synthesized from scratch, not copied) ----
def pop2():          # quick pitch-drop pop, ~0.35 s (850 Hz -> 45 Hz)
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 805 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    x[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return norm(np.tanh(x * 1.5), -3)


def deep_bass():     # sub boom ~30-40 Hz, 1.1 s
    n = int(1.1 * SR); t = np.arange(n) / SR
    f = 32 + 60 * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    click = bandpass_noise(n, 1500, 6000) * np.exp(-t * 80) * 0.25
    return norm(np.tanh((body + click) * 2.5), -1.5)


def charge():        # rising high whine, 1 s (4 -> 6.5 kHz) + soft noise bed
    n = int(1.0 * SR); t = np.linspace(0, 1, n)
    f = 3800 + 2700 * t ** 1.5
    x = 0.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.4 + 0.6 * np.sin(2 * np.pi * 9 * t) ** 2)
    x += 0.25 * sweep_noise(1.0, 2500, 7000, bw=0.3)[:n]
    return norm(x * t ** 1.2 * (1 - np.clip((t - 0.93) / 0.07, 0, 1)), -7)


def flash():         # camera-flash burst: bright crack -> darker thump, 1.1 s
    n = int(1.1 * SR); t = np.arange(n) / SR
    crack = bandpass_noise(n, 3000, 12000) * np.exp(-t * 25)
    whine = 0.3 * np.sin(2 * np.pi * np.cumsum(9000 - 7000 * np.clip(t * 3, 0, 1)) / SR) * np.exp(-t * 8)
    thump = np.sin(2 * np.pi * np.cumsum(70 + 80 * np.exp(-t * 20)) / SR) * np.exp(-t * 5) * 0.8
    return norm(np.tanh((crack + whine + thump) * 1.8), -2)


def whoosh2():       # mid air whoosh, ~1 s, swells then fades
    n = int(0.95 * SR); t = np.linspace(0, 1, n)
    x = sweep_noise(0.95, 500, 2600, bw=0.7)[:n]
    return norm(x * np.sin(np.pi * t ** 0.8) ** 2.2, -3)


def swoosh2():       # bright -> dark descending swoosh, 1.2 s
    n = int(1.2 * SR); t = np.linspace(0, 1, n)
    x = sweep_noise(1.2, 6000, 300, bw=0.6)[:n]
    return norm(x * np.exp(-((t - 0.3) / 0.22) ** 2), -3)


def snap():          # finger-snap style click with a short body around 2.3 kHz
    n = int(0.25 * SR); t = np.arange(n) / SR
    x = bandpass_noise(n, 1800, 9000) * np.exp(-t * 90)
    x += 0.5 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 60)
    return norm(x, -4)


def rewind():        # tape rewind: warbling, accelerating pitch rise, 1.5 s
    n = int(1.5 * SR); t = np.linspace(0, 1, n)
    f = 160 + 140 * t ** 2 + 60 * np.sin(2 * np.pi * (6 + 30 * t) * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + sweep_noise(1.5, 800, 4000, bw=0.5)[:n] * 0.5
    return norm(x * np.sin(np.pi * t) ** 0.6, -8)


def metallic_hit():  # inharmonic metal ring, 2.2 s, bright -> dark
    n = int(2.2 * SR); t = np.arange(n) / SR
    partials = [(523, 1), (1187, .7), (1999, .5), (2873, .35), (4210, .25), (6011, .15)]
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * (1.6 + f / 900)) for f, a in partials)
    x += bandpass_noise(n, 2000, 10000) * np.exp(-t * 60) * 0.6
    return norm(x, -4)


def synth_hit():     # saw-chord stab with filter-like decay, 1 s
    n = int(1.0 * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (110, 164.8, 220, 277.2):
        ph = (f * t) % 1
        saw = 2 * ph - 1
        x += saw * np.exp(-t * (3 + f / 110))
    sub = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 4)
    x = np.convolve(x, np.ones(12) / 12, mode="same") + sub
    return norm(np.tanh(x * 1.4), -2)


def gear():          # mechanical ratchet: 9 clicks slowing down, bright -> dark
    out = np.zeros(int(1.0 * SR))
    pos = 0.0
    for k in range(9):
        n = int(0.03 * SR); t = np.arange(n) / SR
        c = bandpass_noise(n, 2500 - k * 200, 9000 - k * 600) * np.exp(-t * 140) + 0.4 * np.sin(2 * np.pi * (1400 - 90 * k) * t) * np.exp(-t * 120)
        i = int(pos * SR); out[i:i + n] += c[: len(out[i:i + n])] * (1 - k * 0.06)
        pos += 0.06 + k * 0.012
    return norm(out, -5)


def gunshot():       # crack + low body + reverb-ish tail, 0.9 s (use rarely)
    n = int(0.9 * SR); t = np.arange(n) / SR
    crack = bandpass_noise(n, 1000, 12000) * np.exp(-t * 45)
    body = np.sin(2 * np.pi * np.cumsum(90 + 120 * np.exp(-t * 30)) / SR) * np.exp(-t * 9)
    tail = bandpass_noise(n, 300, 5000) * np.exp(-t * 5) * 0.25
    return norm(np.tanh((crack + body + tail) * 2), -2)


SOUNDS = {
    "whoosh": whoosh, "swoosh_down": swoosh_down, "pop": pop, "click": click,
    "tick": tick, "shutter": shutter, "impact": impact, "riser": riser,
    "glitch": glitch, "ding": ding, "paper": paper,
    # "Essential SFX" reference set (pop/whoosh/swoosh replaced by the new versions)
    "pop": pop2, "whoosh": whoosh2, "swoosh": swoosh2, "deep_bass": deep_bass, "charge": charge, "flash": flash,
    "snap": snap, "rewind": rewind, "metallic_hit": metallic_hit, "synth_hit": synth_hit, "gear": gear, "gunshot": gunshot,
}


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "sfx"))
    ap.add_argument("--keep-existing", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, fn in SOUNDS.items():
        p = os.path.join(a.out, name + ".wav")
        if a.keep_existing and os.path.exists(p):
            continue
        write(p, fn())
    print("SFX ready in", os.path.abspath(a.out), ":", ", ".join(SOUNDS))
