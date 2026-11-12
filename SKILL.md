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
- "Washed" SDR footage (iPhone HDR re-encoded by a compressor app without tone mapping: milky blacks, dim
  whites - e.g. *_compressed.mp4) is detected (black point above Y45, or white point below Y203 - dim whites next to
  tone-mapped .mov clips of the same set) and its levels are restored in prepare.py
  (luma stretch to Y34..~215, chroma x1.08), matching the approved natural look of tone-mapped HDR (Mindri-Box-v3).
- **NO COLOUR EFFECTS (user rule, latest - overrides everything older about filters/looks)**: the video keeps the
  footage's colours EXACTLY as filmed. No colour filter, no look matching, no level restore, no saturation change:
  storyboard `"grade": {"preset": "none"}` always; prepare.py's `look_match` / `washed_levels` are OFF (only with
  `VW_COLOR_FIX=1`, i.e. only if the user explicitly asks again). The only colour step left is the technical HDR→SDR
  conversion of iPhone .mov clips below (without it they look milky on every phone). User: "Se vede oribil! Adu
  videourile la normal, fără niciun efect."
- HDR phone footage (iPhone: HLG/PQ, BT.2020, 10-bit, Dolby Vision) is tone-mapped to SDR BT.709 automatically
  (zscale + hable, 100 nits) - without it everything looks pale and milky. The output is tagged BT.709.
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

**"Edited" reference rules (`EFFECTS.md`, bottom) - mandatory in every video**: always a colour `grade`
(`"preset": "none"` - NO colour effect, footage exactly as filmed; any look only if the user asks), face `track`ing 1-3 times per 30 s, internet `photos` for concrete
things that are named (`scripts/images.py`, look at them first, credits in the reply), `combo` titles for the hook
and section headers, `numcards` for enumerations.

**Effects library (`EFFECTS.md`, the user's 17 effects with their Romanian names; #01 Orbită and #15 Vertigo are REMOVED) - mandatory in every video**: about one effect moment every 4-6 s of final video
(30 s → 5-7, 60 s → 9-12), each matched to what is being said, no repeat within ~15 s, mixing camera, cut-out and UI
families. Put one in the hook. Example with all of them: `templates/storyboard.effects-example.json`.

**CTA / ending** (if the user said what they want): `comment` (keyword CTA) and/or `follow` card in the last 4-6 s.

**Brand theme (user's standing choice) - everything on screen**: storyboard `"style": "depth", "palette": "mindricel"`
→ titles, cards, steps, tiles/numbers, charts, checklists, notes, glass text and products all use the
depth-reference look in the mindricel.ro palette (orange #FF6600 gradient, ink #0A0A0A panels, white text, fine dark
outlines). Editorial font names in title lines are mapped automatically; use orange (#FF6600/#FF8533) or white for
doodles. Never mix in the green/cream editorial colours.

**Captions (user's standing choice - "lockup" reference, copied 1:1)**: `"captions": {"style": "lockup", "palette":
"scene"}` (no keyword list needed; roles are automatic).
- Each spoken phrase (2-5 words) is ONE typographic composition: content words are BIG (Montserrat ExtraBold, ~170 px,
  tight -0.045em, as spoken - mostly lowercase), function words are SMALL (Montserrat SemiBold, 1/3 size, white with a
  fine dark contour) tucked into the big words' corners - before a big word: above-left, after it: below-right
  ("over $10,000 a month"). One big word per line, lines stacked tightly and staggered left/right.
- Fills per big word: numbers/money → green gradient, negative words (nu, fără, stop, greșeli, scump...) → red
  gradient, others → gradients from THAT clip's footage colours (`body_profile.py` palette) or white; automatically
  deeper/saturated on bright scenes and light on dark scenes so it always reads.
- Position rotates head / chest / head / above-head; while titles or graphics occupy the top, phrases stay on the
  chest. A phrase in FRONT never covers the face (hair to chin): it moves to the chest or above the head instead.
- DEPTH (user rule, EVERY video): about 40% of phrases (`behind_share` 0.4) sit slightly BEHIND the head (back
  layer + cut-out). The search covers heights from "lower edge grazing the hair" down to mid-face and shifts up to
  ±240 px sideways. A spot is valid only if the head really overlaps a word (`behind_min_overlap` 5%), each big word
  is at most 25% hidden (short words ~4% per letter, e.g. max 16% for 4 letters), and the top part of the first/last
  letters stays visible. Uses the worst-case silhouette over the clip (`occ_max`), scaled by any zoom active at that
  moment. Never 3 behind in a row, never while graphics occupy the top. Check those frames in QA.
- Readability: every big word has a fine contour (dark on dark areas, light on bright areas) + soft shadow; small
  words have a dark contour. Fill colours are chosen from the brightness EXACTLY under the phrase (`lum` map from
  body_profile.py): light tints over dark areas, deep tints over bright areas - the palette stays the footage's.
- QA: check that no front phrase touches the face and that behind phrases read clearly (open frames at each one).
- Motion: the phrase whips in sideways with motion-blur ghosts, words appear as they are spoken (quick blur-in), and
  it whips out in the opposite direction when the next phrase starts (no gaps between phrases).
- Reading time: a phrase appears `lead` 0.25 s before it is spoken (its words slightly ahead of the voice), phrases
  shorter than `min_phrase` 1.0 s merge with the next/previous one (max 7 words / 34 chars), the last phrase holds
  `hold` 1.2 s. The video keeps `tail` 0.8 s of picture after the last word (`edit.json` params; if the footage ends
  sooner, the last frame is held). Multi-clip: `"tail": 0` on every clip except the LAST one.
- Mixed backgrounds (e.g. white T-shirt over a dark backdrop, brightness spread > 0.17 under the phrase): a vivid mid
  tone of the video's own colour with the dark contour (see "Caption colours" below).
- Contrast guard: if a word's colour is too close in brightness to what is behind it (`min_contrast` 0.42), the same
  colour gets its maximum-contrast tint + the fine contour - it never turns white (user rule).
- Sensitive / serious topics (funerals, illness, loss, apologies...): keep the lockup look but `"motion": "fade"`
  (gentle fade-in, no whips), `"semantic": false` (no green/red word colours), no glitch/pixel/frame-break,
  no punchy SFX (none at all is fine), slow push-ins and gentle tracking only, grade strength ~0.6, and no
  mindricel orange theme unless it is the user's own brand. Tell the user the tone was adapted and offer the
  energetic version.
- Older caption styles (`clean` headlines, `depth`, `bold`, `editorial`) only on request.

**Numbers**: `tiles` now render as ONE dark rounded pill with big clean digits counting up and an optional `unit`
in orange (e.g. `{"type": "tiles", "text": "400-600", "unit": "cm³"}`); the old squares only with `"look": "classic"`.

**Transitions (real-estate reference)**: on clip changes / section changes use `flash_blur` (overexposed defocus),
`pixelate` (pixel dissolve, also good when an element/image leaves), `zoom_through`, and zoom-jump cuts (`punch`
alternating 1.0 / 1.1-1.15 on jump cuts). Keep `glitch` rare.

**Sounds (user's SFX reference video, extracted - the ONLY library; the old synthesized one was deleted on request)**:
10 WAVs in `sfx/` (peak -3 dBFS): `loading` (digital ticking 0.9 s), `click`, `air` (short airy swish), `tap` (soft pop),
`marker` (highlighter stroke), `tick` (tiny UI tick), `blur_hit` (punchy impact + tail), `swish`, `sub_boom` (sub-bass
drop), `logo_hit` (big reveal hit). Mapped automatically (compose.py): flash_blur → blur_hit, zoom_through/leak/
whoosh/swoosh transitions → swish, flash → air, pixelate/glitch/rewind → loading, impact → sub_boom, punch → click;
title/stat/combo → blur_hit (first combo + sub_boom), strike/doodle/wall/accent → marker, cards/app/image/product info → tap,
products → air + swish, steps/lists/checklists/numcards → click, counters/tiles/charts → loading, glass/cover → sub_boom,
follow card → logo_hit, typing → tick. Old names (pop, whoosh, deep_bass, ding, ...) still work via `SFX_ALIAS`.
**SFX density (user: "use sound effects more often")** - default `"sfx_density": "high"`: on top of the element and
transition sounds, compose.py adds quiet extra sounds (-15..-19 dB) on caption phrase changes (air when the phrase goes
behind the head, tap on numbers/prices, alternating swish / tick otherwise; from `WORK/caption_events.json`), on every
jump cut (click), when a top graphic leaves (air) and on push/track camera moves. Every extra sound keeps >= 0.3 s from
the others (~1 sound per second). Calm topics: `"sfx_density": "normal"` (automatic when captions `motion: "fade"`).

**FEWER CAPTIONS (user rule, every video)**: captions on every phrase are tiring - only ~60% of phrases get a caption
(`captions.density` 0.6 = 40% fewer). The renderer keeps the most meaningful phrases (content words, numbers/prices,
negatives, names, questions/exclamations; fillers like bă/mă/băi/deci score down), always the first and last phrase,
and never 4 phrases in a row without one. Nothing is on screen during a skipped phrase. Do not override upward unless
the user asks.

**NO TEXT ON THE FACE (user rule, every video, all text)**: front phrases avoid a face zone that is wider than the face
(head movement) and scaled by any zoom active during the phrase (punch/push/track); if no spot is free they go below
the zone on the chest. Behind phrases never cross the face (forehead to chin), only hair / top of the head / the sides.
Titles, cards and products stay in the top zone or beside the head. Close-ups: a phrase that would only fit over a
top graphic or over the face is dropped (no caption for it) rather than overlap. `combo` handwritten accents (+ swoosh) are
moved off the face automatically (below the hero → above it → dropped if there is no free spot). QA: open frames at every phrase near the head.

**CAPTIONS ARE WHITE OR BLACK - NO COLOURED TEXT (user rule, latest - overrides the palette rule below)**: white words
with a fine dark contour on dark / mid / mixed backgrounds, black words with a fine light contour on bright
backgrounds; the soft shadow has an orange tint (#FF6600). No scene-palette colours and no green/red semantic words
(`captions.mono` true by default; the old colour rules below apply only if the user asks for coloured captions again).
Other brands / calm topics (e.g. NOA Funerare): neutral shadow `"captions": {"shadow": "rgba(0,0,0,.55)"}` - the orange
tint is mindricel's.

**(Old, inactive unless asked) Caption colours follow each video's palette** (user rule): lockup words take the RAW clip's own accent colours
(`body_profile.py` palette, e.g. the orange backdrop + gold) keeping their hue; only the lightness moves - light tints
on dark areas, deep shades on bright areas, a vivid mid tone with the dark contour on mixed backgrounds (white shirt
over a dark backdrop). The contrast guard keeps the same colour at maximum contrast with the contour - it never
turns white. QA: `window.lockupQA[].fills` lists each phrase's colours. No plain white phrases by default (`captions.neutral_share` 0); white only when the clip has no accent colours or
as the contrast guard's last resort.
Money/number green and negative red stay (`semantic`).

**Text behind the person must never cut into the head/face** (user feedback): fx.py's person matte grows at once and
shrinks slowly (no lag when the head moves), has a lower threshold for hair, and is merged with a solid head shape from
the per-frame face detector (limited to the segmentation, so no halo). overlay.html never puts a behind phrase across the
face itself (eyes to mouth) - only behind hair, the top of the forehead or the sides of the head.

**No blur on footage, no ghosting**: never smear, soften or double the image. **`orbit` and `vertigo` are REMOVED by the user ("Elimină efectul de orbită și efectul vertigo") - never
use them in any form;** the renderer ignores them if they appear in a storyboard. Other cut-out effects: QA every frame for doubled body parts. All zooms are
sharpened. Check QA frames for softness and ghosting.

**Style preset** (titles/graphics): `"style": "editorial"` (default - forest green/cream boxed karaoke captions, serif titles),
`"bold"` (white heavy words + big yellow keyword, like the effects reference) or `"depth"` (blue gradient 3D hero words).

Pick per user request; otherwise editorial.

**SFX** are automatic (see "Sounds" above): blur_hit on titles, tap on cards, typing ticks on prompts, click on
steps/list items, logo_hit on the follow card, etc. Override per element with `"sfx": "name"` or `"sfx": null`.
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
     If a checklist/card/list/tiles is already in the top zone at that moment, the info card is dropped automatically
     (no overlapping boxes) - put the price into the checklist item instead ("Extinctor + suport · 59 lei").
     Close-ups (no 300 px strip beside the face on either side): the renderer turns a `side` product into a `hero`
     reveal under the chin with captions hidden (user feedback: small products at caption height collided with captions).
     The product NEVER overlaps the face: it uses only the free strip beside the face; if that strip is < 300 px
     (centred close-ups) it goes under the chin / on the chest instead.
   - Several products named in a quick list: one `product3d` per item at the moment it is said (`info: false` so the
     box/bundle price is not confused with item prices); items without a clear variant → small `card` instead.
   - Prices and product names that are unclear in the audio: ASK the user (never guess a price).
   - Known variant names (confirmed by the user): "echipamentul verde, cu negru și crem" = `echipament-crem-negru`
     (the green is the neon accents); the Mîndri Box goggles are `ochelari-negrii-bronz-lentila-colorata` ("bronz").
   - "N culori / modele" said about a product with colour variants on the site → `photos` (the variants' site photos
     fanned beside the person) or a `checklist` of the colours - never `orbit` (removed).
- Restart detector false alarms: lists and repeated phrases ("o pereche de ochelari, o pereche de mănuși", "pe
  mindricel.ro ... pe mindricel.ro") are flagged as retakes - ALWAYS read review.txt and keep real lists. Words after a
  long final pause that last < 0.1 s are transcription artefacts - remove them.
   - `hero`: the big reveal - below the chin, captions hidden; use once per product, on the main mention.
   - Price/sizes/name come only from the site (never invent or round them); `price: false` hides the price.
5. Add a `zoom_through` or `flash` into the hero reveal, and a closing CTA naming **mindricel.ro** if the video sells.
Never recolour or alter the product image. If mindricel.ro is unreachable, tell the user and skip (no stand-ins).

## 4c. Approved element patterns (user: "add these elements to the workflow and use them when it fits")
Reusable patterns from the approved order / Black Friday videos. Pick the ones the speech calls for, timed to the word:
- **Several products / categories named in a row** ("avem ochelari, trusă de scule, mănuși, cagule"): `photos` with the
  site photos (`products/<slug>/photo_0.jpg` or `view_0.png`, fanned beside the person, one per word) or a `checklist` -
  NOT `orbit` (removed by the user).
- **"Box contents" checklist** - when the speaker lists what is in a package/Mîndri Box: `checklist` titled
  "În Mîndri Box" (or "În colet"), each item ticking at the word that names it; 1-2 matching `product3d` beside the head
  (`info: false`), the rest only as checklist items. Quick lists (< 1 s per item) = checklist only.
- **Delivery timeline checklist** - "gata azi / pleacă azi / ajunge mâine": `checklist` "Comanda ta" with those steps.
- **Day-log checklist** - behind-the-scenes ("am început, am luat o pauză, continuăm, așteptăm curierul"): `checklist`
  "Azi la mindricel.ro" with the steps as said.
- **Packing steps checklist** - "în ambalaj, folie cu bule, sigiliu" / "carton, folie de protecție": `checklist`.
- **Big hook combo** - the opening line's key word as `combo` hero (BLACK FRIDAY, COLET RETUR, 2:20, GATA!, MÎNDRI BOX,
  NU TOȚI, TETRIS) with the lead-in words on top; `hide_captions: true`. Also for a strong punchline mid-video.
- **Name-pair title** - wordplay on names ("Costinel / Mindricel"): `title` with two `heavy` lines, the second `gold`.
- **Thank-you card** - customer named: `card` 🧡 "Mulțumim, <Prenume>!" + a face `track`; never the family name.
- **Context cards** - 1-line `card` with an emoji for each situational fact: 📦 coletele din weekend, 🚚 livrare
  decalată / pleacă dimineața, 😴 2:20 noaptea, 🧾 factura, 🔒 sigilat, 🗑️ la gunoi, 🤐 fără nume de familie.
- **Price tiles** - every price spoken (or the known Mîndri Box price on "prețul bun"): `tiles` "199" + unit "lei".
- **Comment CTA** - "lasă-ne un comentariu / spune-ne ce părere ai": `comment` with the question typed + short reply.
- **Follow card** - always in the last 2.5-4 s: mindricel.ro, tagline from the speaker's sign-off, button "Comandă".
- **Transitions** - `zoom_through` / `flash_blur` / `pixelate` only on clip boundaries and section changes.

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
- The SFX library is the 10 sounds extracted from the user's SFX reference video (`sfx/*.wav`, committed). New WAVs the
  user sends can be added to `sfx/` and referenced by name (`"sfx": "name"`).
- Speed: about 10-12 s of rendering per second of final video when back-layer and cut-out effects are used.
