#!/usr/bin/env python3
"""Step 3: propose an edit decision list from the transcript.

Auto-detects:
  - filler words (um/uh/hmm, ăă/îî/deci-filler ...)
  - stutters and cut-off words ("I- I think" -> drops the first "I-")
  - restarts / retakes: when a phrase is started again shortly after, the EARLIER attempt
    is removed (the last take is usually the good one)
  - low-confidence words are flagged (not removed) for human/Claude review
Silences are not listed here - cut.py removes every gap between kept words.

Writes WORKDIR/edit.json (editable) and WORKDIR/review.txt (human-readable).
Usage: propose_cuts.py WORKDIR
"""
import json, os, re, sys

FILLERS = {
    "um", "umm", "uh", "uhh", "uhm", "erm", "er", "ah", "hmm", "hm", "mm", "mhm",
    "ă", "ăă", "ăăă", "î", "îî", "îîî", "â", "ââ", "ââă", "îm", "ăm", "hmmm",
}


def norm(w):
    return re.sub(r"[^\w']", "", w.lower())


def main():
    work = sys.argv[1]
    t = json.load(open(os.path.join(work, "transcript.json")))
    words = t["words"]
    n = len(words)
    remove = {}  # idx -> reason

    for i, w in enumerate(words):
        nw = norm(w["w"])
        if nw in FILLERS:
            remove[i] = "filler"
        elif w["w"].endswith("-") or w["w"].endswith("—"):
            remove[i] = "cut-off word"
        elif i + 1 < n and nw and nw == norm(words[i + 1]["w"]) and nw not in {"that", "had", "very", "foarte"}:
            remove[i] = "stutter"

    # restarts: phrase P (>=3 words) starting at j re-appears at i (j < i <= j+30)
    toks = [norm(w["w"]) for w in words]
    protected = set()  # words that belong to a confirmed "good" (later) take
    i = 0
    while i < n:
        found = 0
        for k in (5, 4, 3):
            if i + k > n:
                continue
            probe = toks[i:i + k]
            if not all(probe):
                continue
            for j in range(max(0, i - 30), i - k + 1):
                if toks[j:j + k] == probe and not any(x in protected for x in range(j, i)):
                    # remove the earlier attempt j .. i-1, keep the later take
                    for x in range(j, i):
                        if x not in protected:
                            remove.setdefault(x, "restart (earlier take)")
                    protected.update(range(i, i + k))
                    found = k
                    break
            if found:
                break
        i += found or 1

    edit = {
        "remove": [],
        "keep": [],
        "params": {"pad_before": 0.06, "pad_after": 0.10, "max_gap": 0.20, "tail": 0.8,
                   "snap_to_silence": True},
        "_help": "remove: list of {from,to,reason} word-index ranges (inclusive) to delete. "
                 "keep: word indices to force-keep even if inside a remove range. "
                 "Gaps between kept words longer than max_gap are cut down.",
    }
    # compress to ranges
    idx = sorted(remove)
    for x in idx:
        if edit["remove"] and edit["remove"][-1]["to"] == x - 1 and edit["remove"][-1]["reason"] == remove[x]:
            edit["remove"][-1]["to"] = x
        else:
            edit["remove"].append({"from": x, "to": x, "reason": remove[x]})
    json.dump(edit, open(os.path.join(work, "edit.json"), "w"), ensure_ascii=False, indent=1)

    lines = [f"# Transcript review ({t['language']}) - [x] = auto-removed, (?) = low confidence",
             "# idx  start-end   word"]
    prev_end = 0
    for i, w in enumerate(words):
        gap = w["start"] - prev_end
        if gap > 0.6:
            lines.append(f"      ---- pause {gap:.1f}s ----")
        mark = f"[x {remove[i]}]" if i in remove else ""
        conf = "(?)" if w["p"] < 0.5 else ""
        lines.append(f"{i:5d}  {w['start']:6.2f}-{w['end']:6.2f}  {w['w']} {conf} {mark}".rstrip())
        prev_end = w["end"]
    open(os.path.join(work, "review.txt"), "w").write("\n".join(lines) + "\n")
    kept = [w["w"] for i, w in enumerate(words) if i not in remove]
    print(f"{len(remove)} of {n} words auto-flagged for removal. Review: {work}/review.txt")
    print("KEPT TEXT:", " ".join(kept))


if __name__ == "__main__":
    main()
