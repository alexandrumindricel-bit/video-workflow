# Effects library (17 effects from the reference "17 video effects")

Use these **in every video, chosen to fit what is being said**. Each row says how to build it in `storyboard.json`
(see `templates/STORYBOARD_REFERENCE.md` for every field) and when it fits.
"Cut-out" = the person is segmented and drawn over the back layer: anything on the back layer appears **behind** them.

| # | Effect | How (storyboard) | Use it when the speaker… | SFX (auto) |
|---|---|---|---|---|
| 01 | **orbit** | element `orbit` with 4-6 `items` (icon/text/image) | lists tools, features, options ("all of these…") | riser |
| 02 | **couch wall** | element `wall`, `kind: "screen"` (screenshot cards, `image`/`head`) - back layer | references many posts, results, examples, social proof | paper |
| 03 | **ui world** | element `app` (window + clip tiles + chip + typed input) in `pos: top` | describes a workflow inside an app / prompting | pop |
| 04 | **frame break** | effect `frame_break` (`rect`) - video framed, person breaks out | a reveal, "step out of the box", a bold claim | whoosh |
| 05 | **digital zoom** | effect `push` (1.0→1.12-1.18) + caption keyword (big yellow/gold word) | emphasis line, punchline | - |
| 06 | **phone mockup** | element `phone` with `messages` (chat bubbles appear) | DMs, texts, "send me…", app on phone | pop |
| 07 | **checklist** | element `checklist` (items tick off, "1 of 3" counter) | steps, requirements, "all you need to do" | pop |
| 08 | **headline wall** | element `wall`, `kind: "paper"` (taped notes with headlines) - back layer | ideas, quotes, headlines, reactions, "people said…" | paper |
| 09 | **zoom-through cut** | transition `{kind: "zoom_through", at}` (zoom + radial blur through the cut); also `flash_blur` and `pixelate` | section change, time skip, "and then…" | whoosh |
| 10 | **chart grow** | element `chart` (`values`, `labels`, `tag: "SCALE ↗"`) | growth, numbers over time, results | riser |
| 11 | **pull-back reveal** | effect `pull_back` (video shrinks into a window) + element `app`/`card` above it | "this video was made in…", showing the tool behind the scenes | swoosh down |
| 12 | **green screen** | element `backdrop` (`kind: app/image/gradient`) - back layer, person cut out | "imagine…", talking about a page/product/app, a scene change | whoosh |
| 13 | **paper cut** | `backdrop` `kind: paper` + effect `sticker` + elements `tiles` ("100%") / `doodle` | playful/creative moments, stats, scrapbook energy | paper + clicks |
| 14 | **doodle boil** | effect `outline` (boiling outline around the person) + element `doodle` (`shapes`) | fun, casual, "creative" lines; pointing at something | paper |
| 15 | **vertigo** | effect `vertigo` (`amount` 0.08-0.14; person grows, background stays sharp) | dramatic realization, "this changes everything", tension | riser |
| 16 | **cover story** | element `cover` (magazine masthead **behind the head**, `issue` line, optional `lines`) | introducing a topic/title, "the story of…", hook | impact |
| 17 | **glass type** | element `glass` (giant translucent glass word with shine) - back layer | a single huge keyword or number ("26", "DESIGN") | whoosh |

## Rules for choosing
- **Every video uses several of these effects**: ~1 effect moment every 4-6 s of final video
  (a 30 s video → 5-7 effects, a 60 s video → 9-12), on top of the normal captions/cards/punch-ins.
- **Match the meaning** (column "use it when"). Never use an effect just to fill time.
- **Hook (first 3 s)**: prefer `cover`, `glass`, `frame_break` or `zoom_through` combined with a big title.
- **Don't repeat the same effect within ~15 s**; vary families (camera: push/vertigo/zoom-through/pull-back/frame-break ·
  cut-out: backdrop/cover/glass/wall/sticker/outline · UI: app/phone/checklist/chart/orbit).
- **Cut-out effects need a clearly visible person** (whole head + shoulders in frame, decent light). If the person is
  very small, moving fast, or partly out of frame, prefer UI effects. Check the cut-out edge in QA frames.
- Keep each effect 0.7-2.5 s, aligned to the words it illustrates (start = word start).
- Captions stay on; if an effect fills the caption area (orbit at chest, phone), move it (`dy`, `y`) or set `hide_captions`.
- Text the viewer must read stays on the front layer; back-layer elements are partly hidden by the person by design.


# "Edited" reference (raw vs edited) - apply in EVERY video

1. **Never deliver raw-looking footage - always grade. Default (user's choice): `"grade": {"preset": "simple",
   "strength": 1.0, "subject_pop": false}`** - Instagram-"simple"-like: natural colours, gentle contrast, slightly
   darker, touch of warmth, true blacks, NO vignette, NO background blur around the person. Use the stronger presets
   below only if the user asks for them. `"grade"` in the storyboard (fx.py, footage only, graphics untouched):
   `cinematic` (teal shadows / warm skin - outdoor, daylight, gym), `warm` (golden, deep blacks - night, indoor lamps),
   `olive` (grey studio), `clean` (white studio / high-key), `mindricel` (brand: warm highlights, teal-neutral shadows).
   Per clip: `{"preset": ..., "clips": [...], "strength": 0.85}`. Highlights roll off, skin tones are protected;
   `subject_pop: true` (darker/softer background) only on request - the user does not want it by default.
   Check graded QA frames: skin natural, no crushed faces, walls not grey-muddy. Lower `strength` (0.6) if it looks heavy.
2. **Face tracking sometimes** - effect `track` (`scale` 1.25-1.4, 2-4 s): a zoomed crop that follows the face.
   Use it when the person is small in frame (full-body / far shots), on emphasis lines, and to vary long static shots.
   1-3 times per 30 s; not during `frame_break` / `pull_back`.
3. **Images from the internet for what is said** - for concrete things the speaker names (places, objects, vehicles,
   terrain, food, brands as examples, "these gyms", "this formula"): `python3 scripts/images.py WORK "<english query>"
   --name <slug> --n 3`, LOOK at the downloaded cards (relevant? no watermark/text/strangers' faces?), then element
   `photos` at the word's time beside the person (white-bordered rounded cards, fanned, glow flash in, shutter SFX).
   2-4 image moments per 30 s. Credits (WORK/images/credits.txt) go in the delivery message for the post description.
4. **Text style** - section headers and the hook use `combo` (replaces captions while shown, `hide_captions: true`):
   small spoken lead-in words spread above (`top`), ONE huge word (`hero`, fonts `cond` Bebas / `tall` Anton / `heavy`
   Montserrat; looks `solid` cream, `grad` orange 3D, `neon` glow for dark scenes), optional handwritten `accent`
   (1-2 spoken words, Kaushan Script, orange, swoosh underline) and flickering pixel squares. All words must be spoken.
   `layer: "back"` puts the combo behind the person (like "LEG Day") when the head would cover only a little.
5. **Numbered cards** - `numcards` (`items: [{n, label, at}]`) for "3 ways / steps / reasons" enumerations.
