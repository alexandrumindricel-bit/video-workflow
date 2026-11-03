---
name: edit-video
description: Edit a raw talking-head video into a finished vertical short in the user's reference style (STYLE_GUIDE.md) - transcribe, cut silences and mistakes lip-sync safe, storyboard, word-by-word captions with highlighted keywords, motion graphics that illustrate the speech, SFX on transitions, render 1080x1920 MP4. Use whenever the user sends/uploads a raw video to edit.
---

# Edit-video workflow

Follow these steps **every time** the user sends a raw video. Tool root: `/home/user/video-workflow`
(`VW=/home/user/video-workflow`). Use a fresh work dir per video in the scratchpad, e.g. `$SCRATCH/<name>/work`.
Read `STYLE_GUIDE.md` (the style), `EFFECTS.md` (the 17-effect library - use several in EVERY video) and
`templates/STORYBOARD_REFERENCE.md` (syntax) before step 4.

## 0. Setup (once per container)
`$VW/vw.sh setup`. If it warns that huggingface.co is blocked, tell the user transcription can't run until they allow
`huggingface.co` (and `*.hf.co`) in the environment's network settings; do not invent a transcript.

## 1. Prepare + transcribe + propose cuts
```
$VW/vw.sh prep RAW.mp4 WORK [--language ro|en] [--model small|medium]
```
- Normalizes to 30 fps CFR, 1080x1920 (cover-crop), detects the face (MediaPipe full-range) and measures the
  title-zone brightness → `layout.json` (safe zones; bright zones make titles boxed and glass text tinted).
- Transcribes with word timestamps (keeps "um"/restarts visible) → `transcript.json`.
- Auto-flags fillers, stutters, cut-off words and restarts → `edit.json` + `review.txt`.
- Use `--model medium` for Romanian or noisy audio; auto language detection otherwise.
- If the source was landscape (warning printed), tell the user it was center-cropped.

## 1b. Several raw clips (one story)
When the user sends several clips, transcribe each one first and work out the order from what is said
(usually the filming order). Run steps 1-2 and `cut` **per clip** (`WORK_k`), then join them:
`python3 $VW/scripts/merge_clips.py WORK WORK_1 WORK_2 …` → one timeline; `layout.json` keeps each clip's own
framing (`clips[]`), and the renderer and effects use the framing of whichever clip is on screen. Fix caption text
in the merged `words.json`, then continue at step 4 on `WORK`. Put a transition (`zoom_through`, `flash`,
`glitch`) on every clip boundary.

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

**Effects library (`EFFECTS.md`) - mandatory in every video**: about one effect moment every 4-6 s of final video
(30 s → 5-7, 60 s → 9-12), each matched to what is being said, no repeat within ~15 s, mixing camera, cut-out and UI
families. Put one in the hook. Example with all of them: `templates/storyboard.effects-example.json`.

**CTA / ending** (if the user said what they want): `comment` (keyword CTA) and/or `follow` card in the last 4-6 s.

**Captions (user's standing choice)**: `"captions": {"style": "depth", "palette": "mindricel", "mode": "pop"}` -
font and look of the depth reference (Montserrat: white words popping in one by one, ONE big 3D keyword per
sentence), in the mindricel.ro palette (#FF6600 orange gradient, black edge), **no background box**. Keep about one
keyword per sentence (not every important word).

**Style preset** (titles/graphics): `"style": "editorial"` (default - forest green/cream boxed karaoke captions, serif titles),
`"bold"` (white heavy words + big yellow keyword, like the effects reference) or `"depth"` (blue gradient 3D hero words).
Pick per user request; otherwise editorial.

**SFX** are automatic: whoosh on titles, pop on cards, typing ticks on prompts, click on steps/list items,
shutter on flash, glitch sound on glitch, etc. Override per element with `"sfx": "name"` or `"sfx": null`.
Optional `music: {file, gain_db}` only if the user supplies a track (it is ducked under the voice).

## 4b. Products from mindricel.ro → 3D product (mandatory whenever one is presented)
Whenever the speaker presents, names, holds up or recommends a product sold on **mindricel.ro** (helmets / căști,
goggles / ochelari, gear / echipament, backpacks / rucsac, balaclavas / cagulă, beanie / fes, keyring / breloc,
cables, phone/GPS mounts, extinguisher mounts…), show it as a **3D product** taken from the site:
1. `python3 $VW/scripts/product.py catalog` - fresh list of all products (prices change: always re-fetch per video).
2. Match what is said (and what is held in the frames - colour!) to the exact product/variant. If several variants
   fit and neither the speech nor the footage decides it, ask the user which one - never guess a colour.
3. `python3 $VW/scripts/product.py fetch <slug> WORK` → name, price, sizes, images from the page's schema.org data;
   cut-out per angle (`view_N.png`) + `qa_cutout.jpg`. **Look at `qa_cutout.jpg`**: if a view is bad, pick good
   ones with `"views": [0, 2]`, or use `"mode": "card"` (3D photo card) - `quality: "low"` defaults to card.
4. Storyboard element `product3d` from the word that names the product, 2.5-5 s:
   `{"type": "product3d", "product": "<slug>", "start": …, "end": …, "pos": "side"|"hero"|"top"}`
   - `side` (default): next to the head, turntable through the angles; info card (name, price, sizes, mindricel.ro) above it.
   - `hero`: the big reveal - below the chin, captions hidden; use once per product, on the main mention.
   - Price/sizes/name come only from the site (never invent or round them); `price: false` hides the price.
5. Add a `zoom_through` or `flash` into the hero reveal, and a closing CTA naming **mindricel.ro** if the video sells.
Never recolour or alter the product image. If mindricel.ro is unreachable, tell the user and skip (no stand-ins).

## 5. Render
```
$VW/vw.sh render WORK OUT.mp4
```
→ `fx.py` camera effects + person cut-out (MediaPipe selfie segmentation) → front/back graphics layers (Chromium,
deterministic frames) → stack: background · back layer · sticker · person · outline · front layer → glitches, voice
cleanup, SFX mix, loudness -14 LUFS → H.264 1080x1920 30 fps + `WORK/qa_sheet.jpg`.

## 6. QA (before delivering)
- Look at `WORK/qa_sheet.jpg` and extract 4-6 full frames at hook/graphic/transition moments
  (`ffmpeg -ss T -i OUT.mp4 -frames:v 1 f.jpg`) and actually view them: face never covered, text inside the safe area
  (nothing important in bottom 18 % / right 12 %), no text overflowing, keywords highlighted, hook has 3+ changes.
- For every cut-out effect, view a frame: edges clean (no halo/missing hair or hands)? If the cut-out is poor for this
  footage, swap that effect for a UI one.
- Confirm output is 1080x1920, 30 fps, audio present (compose prints it), sync check was OK.
- Fix storyboard → re-run render (cut is not re-run unless the edit changes).

## 7. Deliver
Send the MP4 with SendUserFile and reply briefly: length before → after, what was cut (count of fillers/retakes),
the storyboard table, and anything to double-check (low-confidence words, landscape crop). Offer quick revisions
("more zoom", "less graphics", "depth style", different hook title).

## Notes / limits
- Person cut-out uses MediaPipe 0.10.14 in `/opt/vw-seg` (Python 3.12 venv, model bundled in the wheel): soft edges,
  best for head-and-shoulders/medium shots. Text behind the speaker = any element on the back layer.
- The SFX library is synthesized (`scripts/make_sfx.py`). The user's own WAVs dropped into `sfx/` with the same names
  (whoosh, pop, click, tick, shutter, impact, riser, glitch, ding, paper, swoosh_down) replace them.
- Speed: about 10-12 s of rendering per second of final video when back-layer and cut-out effects are used.
