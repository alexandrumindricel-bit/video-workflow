---
name: edit-video
description: Edit a raw talking-head video into a finished vertical short in the user's reference style (STYLE_GUIDE.md) - transcribe, cut silences and mistakes lip-sync safe, storyboard, word-by-word captions with highlighted keywords, motion graphics that illustrate the speech, SFX on transitions, render 1080x1920 MP4. Use whenever the user sends/uploads a raw video to edit.
---

# Edit-video workflow

Follow these steps **every time** the user sends a raw video. Tool root: `/home/user/video-workflow`
(`VW=/home/user/video-workflow`). Use a fresh work dir per video in the scratchpad, e.g. `$SCRATCH/<name>/work`.
Read `STYLE_GUIDE.md` (the style) and `templates/STORYBOARD_REFERENCE.md` (element syntax) before step 4.

## 0. Setup (once per container)
`$VW/vw.sh setup`. If it warns that huggingface.co is blocked, tell the user transcription can't run until they allow
`huggingface.co` (and `*.hf.co`) in the environment's network settings; do not invent a transcript.

## 1. Prepare + transcribe + propose cuts
```
$VW/vw.sh prep RAW.mp4 WORK [--language ro|en] [--model small|medium]
```
- Normalizes to 30 fps CFR, 1080x1920 (cover-crop), detects the face → `layout.json` (safe zones).
- Transcribes with word timestamps (keeps "um"/restarts visible) → `transcript.json`.
- Auto-flags fillers, stutters, cut-off words and restarts → `edit.json` + `review.txt`.
- Use `--model medium` for Romanian or noisy audio; auto language detection otherwise.
- If the source was landscape (warning printed), tell the user it was center-cropped.

## 2. Review the edit (judgment step - do not skip)
Read `WORK/review.txt` top to bottom like an editor and fix `WORK/edit.json`:
- **Remove**: failed takes / restarts the detector missed (keep the LAST good take), fluffed sentences,
  "wait, let me redo that", off-topic asides, dead intro ("hey guys", "so, um, today…") - the video must start on the hook line.
- **Keep** (`"keep": [idx…]`): words the detector wrongly removed (deliberate repetition, "very very", lists).
- Low-confidence words `(?)`: check context; a misheard word is a caption problem (fix the text in `transcript.json`,
  keep the timing), not a cut.
- Pacing params: `max_gap` 0.20 s (tight, guide style); raise `pad_after` to 0.14 if word endings sound clipped.
Then:
```
$VW/vw.sh cut WORK
```
It must print `Sync check: … OK`. If MISMATCH → stop and investigate (never ship). Cut points are frame-snapped and
placed in silence, so lip sync is exact. Re-read `WORK/words.json` (new timeline) - all later timings use it.

## 3. Fix caption text
In `words.json` correct misspellings, brand names, numbers ("ten" → "10" when it reads better), and keep the
user's language and diacritics (ă â î ș ț). Do not change timings.

## 4. Storyboard (judgment step)
Write `WORK/storyboard.json` (syntax: `templates/STORYBOARD_REFERENCE.md`, example: `templates/storyboard.example.json`).
First write a short plan as a table (time · what is said · visual · transition · SFX) and show it to the user in the
reply at the end. Rules from the style guide:

**Hook (0-3 s)** - the strongest claim as giant `title` elements, one per phrase, **3+ visual changes in 3 s**
(title swap / font swap / flash / punch-in). Mix title fonts (serif → heavy → italic gold). No intro.

**Body** - something changes on screen **every ~1-3 s**:
- Illustrate what is said, timed to the exact word that mentions it (element `start` = that word's `start`):
  tools/apps → `strike` (when rejected) or `card`; instructions/prompts → `prompt` (typing); numbers → `counter`/`stat`;
  steps → `step` badges; enumerations → `list`; a key phrase → `title`; a screenshot/logo the user provided → `image`/`card`.
- One **hero keyword per sentence** in `captions.keywords` (the word that carries the meaning, not filler).
- **Punch-in zooms** (`zooms`, scale 1.06-1.12, never more) on emphasis lines, alternating with 1.0 - this keeps
  the speaker at normal framing while hiding jump cuts.
- **Stylized transitions only at section changes / payoff**, max one every 5-10 s: `flash`, `glitch`, `leak`, `whoosh`, `impact`.
- Every 10-15 s change mode (e.g. a run of UI cards, then a big-title moment, then a stat).

**Speaker always visible**: graphics go in `pos: "top"` (above the head, auto-fitted to the free zone from
`layout.json`) or `"lower"` (chest area, above captions). Never `center` over the face. Titles may overlap the top
of the head slightly (that is the look), never the eyes/mouth.

**CTA / ending** (if the user said what they want): `comment` (keyword CTA) and/or `follow` card in the last 4-6 s.

**Style preset**: `"style": "editorial"` (default - forest green/cream boxed karaoke captions, serif titles) or
`"depth"` (blue gradient 3D hero words, white pop-in words) when the user asks for the blue look.

**SFX** are automatic: whoosh on titles, pop on cards, typing ticks on prompts, click on steps/list items,
shutter on flash, glitch sound on glitch, etc. Override per element with `"sfx": "name"` or `"sfx": null`.
Optional `music: {file, gain_db}` only if the user supplies a track (it is ducked under the voice).

## 5. Render
```
$VW/vw.sh render WORK OUT.mp4
```
→ transparent captions/graphics layer (Chromium, deterministic frames) → punch-ins, glitches, overlay, voice cleanup,
SFX mix, loudness -14 LUFS → H.264 1080x1920 30 fps + `WORK/qa_sheet.jpg`.

## 6. QA (before delivering)
- Look at `WORK/qa_sheet.jpg` and extract 4-6 full frames at hook/graphic/transition moments
  (`ffmpeg -ss T -i OUT.mp4 -frames:v 1 f.jpg`) and actually view them: face never covered, text inside the safe area
  (nothing important in bottom 18 % / right 12 %), no text overflowing, keywords highlighted, hook has 3+ changes.
- Confirm output is 1080x1920, 30 fps, audio present (compose prints it), sync check was OK.
- Fix storyboard → re-run render (cut is not re-run unless the edit changes).

## 7. Deliver
Send the MP4 with SendUserFile and reply briefly: length before → after, what was cut (count of fillers/retakes),
the storyboard table, and anything to double-check (low-confidence words, landscape crop). Offer quick revisions
("more zoom", "less graphics", "depth style", different hook title).

## Notes / limits
- Text-behind-the-speaker masking (ref B) is not implemented: it needs a segmentation model.
- The SFX library is synthesized (`scripts/make_sfx.py`). The user's own WAVs dropped into `sfx/` with the same names
  (whoosh, pop, click, tick, shutter, impact, riser, glitch, ding, paper, swoosh_down) replace them.
- Long videos: overlay render ≈ 3 s per second of video; compose ≈ 2 s per second.
