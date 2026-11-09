# Effects library (17 effects from the reference "17 video effects")

Use these **in every video, chosen to fit what is being said**. Each row says how to build it in `storyboard.json`
(see `templates/STORYBOARD_REFERENCE.md` for every field) and when it fits.
"Cut-out" = the person is segmented and drawn over the back layer: anything on the back layer appears **behind** them.

| # | Efect (numele utilizatorului) | How (storyboard) | Use it when the speaker… | SFX (auto) |
|---|---|---|---|---|
| 01 | **Orbită** – literele se rotesc în 3D în jurul tău | element `orbit` with `ring: "TEXT"` (3D letter ring at chest height, near half in front, far half behind; `accent_word` orange, `size` 84, `rx` 400, `ry` 70, `speed` 0.16, `dy`). Card version: `items` (icons/photos) for lists of things | a slogan / brand / event name (BLACK FRIDAY, MÎNDRI BOX); card version for several products/categories | swish |
| 02 | **Galerie pe perete** – clipul tău în rame, pe un perete | effect `gallery` (`scale` 0.5, `wall` "#E8E1D5", `frame` "#1E1A17", `y`): camera pulls back, the live clip hangs in a picture frame between two small frames | "look at this", memories, a showcase moment, "behind the scenes", a pause in the story | swish |
| 03 | **Lumea din aplicație** – tu în mijlocul unei interfețe | element `backdrop` `kind: "app"` (`label`, `title`, `timer`, `items`) - person cut out in the middle of an app UI; or `app` window | ordering on the site, an app/website, "intrați pe mindricel.ro" | swish |
| 04 | **Ieși din ecran** – ieși din chenarul clipului | effect `frame_break` (`rect`) - video framed, person breaks out | a reveal, bold claim, "step out of the box" | swish |
| 05 | **Zoom digital** – apropiere bruscă pe față | effect `punch` (1.08-1.12) or `track` (face-following 1.3) | emphasis, punchline, reaction | click |
| 06 | **Desen pe telefon** – cercuri și săgeți desenate peste clip | element `doodle` with `shapes` circle / arrow / underline / x placed on the thing being shown (never on the face) | pointing at a product/detail ("uite", "aici"), highlighting | marker |
| 07 | **Listă bifată** – o listă care se bifează pe ecran | element `checklist` (items tick at the word) | steps, box contents, plans, delivery timeline | click |
| 08 | **Titluri de ziar** – cuvinte mari care cad pe ecran | element `title` `anim: "drop"` (heavy/serif lines) or `combo` (huge word blurring in) | hook, news-like statement, punchline | blur_hit |
| 09 | **Trecere prin zoom** – intri cu zoom în imagine și tai la alt cadru | transition `zoom_through` (also `flash_blur`, `pixelate`) | clip boundaries, section change, time skip | swish |
| 10 | **Grafic care crește** – bare și linie care urcă | element `chart` (`values`, `labels`, `tag`) | growth, more orders, numbers over time | loading |
| 11 | **Zoom înapoi** – camera se retrage și clipul devine mic | effect `pull_back` (video shrinks into a floating window) + `card`/`app` above | showing the bigger picture, "this video was made…", context | swish |
| 12 | **Fundal schimbat** – tu decupat pe alt fundal | element `backdrop` (`kind: image/gradient/color/paper`) - person cut out | "imagine…", a place/scene change, talking about a page | swish |
| 13 | **Decupaj din hârtie** – tu ca un sticker pe hârtie | `backdrop` `kind: paper` + effect `sticker` (+ `tiles`/`doodle`) | playful moments, stats, scrapbook energy | marker |
| 14 | **Desene pe video** – desene făcute de mână care se mișcă în jurul tău | effect `outline` (boiling outline) + element `doodle` (stars, sparkles, spirals around the person) | fun, casual lines, excitement | marker |
| 15 | **Efectul Vertigo** – fundalul se apropie, tu rămâi pe loc | effect `vertigo` (`amount` 0.2-0.3, 1.5-3 s): elastic zoom - zero movement on/near the person, the background zooms in smoothly towards the frame edges (no cut-out, no inpainting → no ghosts, works hand-held and with objects in front; only far straight edges bend slightly) | a realisation, "stai puțin…", a dramatic beat | sub_boom |
| 16 | **Copertă de revistă** – tu pe coperta unei reviste | element `cover` (masthead behind the head, `issue`, `lines`) | introducing a topic, "povestea…", hook | sub_boom |
| 17 | **Text de sticlă** – text transparent, ca din sticlă | element `glass` (giant translucent word with light sweep, back layer) | one huge keyword or number | sub_boom |

## Rules for choosing
- **Every video uses several of these effects**: ~1 effect moment every 4-6 s of final video
  (a 30 s video → 5-7 effects, a 60 s video → 9-12), on top of the normal captions/cards/punch-ins.
- **Match the meaning** (column "use it when"). Never use an effect just to fill time.
- **Hook (first 3 s)**: prefer `cover`, `glass`, `frame_break` or `zoom_through` combined with a big title.
- **Don't repeat the same effect within ~15 s**; vary families (camera: push/punch/track/vertigo/zoom-through/pull-back/gallery/frame-break ·
  cut-out: backdrop/cover/glass/wall/sticker/outline · UI: app/phone/checklist/chart/orbit).
- **Cut-out effects need a clearly visible person** (whole head + shoulders in frame, decent light). If the person is
  very small, moving fast, or partly out of frame, prefer UI effects. Check the cut-out edge in QA frames.
- Keep each effect 0.7-2.5 s, aligned to the words it illustrates (start = word start).
- Captions stay on; if an effect fills the caption area (orbit at chest, phone), move it (`dy`, `y`) or set `hide_captions`.
- Text the viewer must read stays on the front layer; back-layer elements are partly hidden by the person by design.


# "Edited" reference (raw vs edited) - apply in EVERY video

1. **Colour: `"grade": {"preset": "none"}` - NO colour effect (user's latest rule; see SKILL.md). Old notes below apply only if the user asks for a look again.** Previously: `"preset": "natural"` - the
   footage's own colours and white balance: no tint, no warmth, no extra saturation, no vignette, no background blur;
   only a very slight contrast lift and highlight protection. The user did NOT like the stylised looks (`warm_rich`,
   `simple`, `cinematic`, ...) - use them only if explicitly asked. `"grade"` in the storyboard (fx.py, footage only, graphics untouched):
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
