#!/usr/bin/env python3
"""Step 2: word-level transcription with faster-whisper.

Writes WORKDIR/transcript.json:
  {"language": "en", "words": [{"i":0,"w":"Hello","start":0.12,"end":0.41,"p":0.98}, ...]}

Usage: transcribe.py WORKDIR [--model small|medium|large-v3] [--language en|ro|...]
Needs the Whisper model, downloaded once from huggingface.co (must be allowed by the
environment's network policy) or pre-placed in models/ (pass --model /path/to/model).
"""
import argparse, json, os

# Prompts that make Whisper keep disfluencies ("um", "uh", restarts) instead of silently
# cleaning them up - we need to SEE mistakes to cut them.
DISFLUENT_PROMPTS = {
    "en": "Umm, so, uh, I mean, like, you know... I- I think, hmm, let me, uh, let me start again.",
    "ro": "Ăăă, deci, îîî, adică, practic... Eu- eu cred că, hmm, stai, iau de la capăt.",
}


# names Whisper tends to mishear ("Claude" -> "cloud") - biased towards these spellings
BRAND_WORDS = "Claude, Mindricel, mindricel.ro, ATV, enduro, motocross, CapCut, comment"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default=None, help="ISO code; auto-detect if omitted")
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--hotwords", default="", help="extra words/names to favour, comma separated")
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    model_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    model = WhisperModel(a.model, device="cpu", compute_type="int8",
                         cpu_threads=a.threads, download_root=model_dir)
    # load the 16 kHz mono WAV ourselves (faster-whisper's PyAV decoder breaks with some PyAV versions)
    import wave
    import numpy as np
    with wave.open(os.path.join(a.work, "audio16k.wav")) as wf:
        audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

    lang = a.language
    if lang is None:
        _, info = model.transcribe(audio, beam_size=1, without_timestamps=True)
        lang = info.language
        print(f"Detected language: {lang} (p={info.language_probability:.2f})")

    segments, info = model.transcribe(
        audio, language=lang, beam_size=5, word_timestamps=True,
        vad_filter=False, condition_on_previous_text=False,
        initial_prompt=DISFLUENT_PROMPTS.get(lang),
        hotwords=", ".join(filter(None, [BRAND_WORDS, a.hotwords])),
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"i": len(words), "w": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3), "p": round(w.probability, 3)})
    out = {"language": lang, "model": a.model, "words": words}
    json.dump(out, open(os.path.join(a.work, "transcript.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} words transcribed ->", os.path.join(a.work, "transcript.json"))
    print(" ".join(w["w"] for w in words))


if __name__ == "__main__":
    main()
