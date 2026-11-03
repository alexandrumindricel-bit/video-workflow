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
| 09 | **zoom-through cut** | transition `{kind: "zoom_through", at}` (zoom + radial blur through the cut) | section change, time skip, "and then…" | whoosh |
| 10 | **chart grow** | element `chart` (`values`, `labels`, `tag: "SCALE ↗"`) | growth, numbers over time, results | riser |
| 11 | **pull-back reveal** | effect `pull_back` (video shrinks into a window) + element `app`/`card` above it | "this video was made in…", showing the tool behind the scenes | swoosh down |
| 12 | **green screen** | element `backdrop` (`kind: app/image/gradient`) - back layer, person cut out | "imagine…", talking about a page/product/app, a scene change | whoosh |
| 13 | **paper cut** | `backdrop` `kind: paper` + effect `sticker` + elements `tiles` ("100%") / `doodle` | playful/creative moments, stats, scrapbook energy | paper + clicks |
| 14 | **doodle boil** | effect `outline` (boiling outline around the person) + element `doodle` (`shapes`) | fun, casual, "creative" lines; pointing at something | paper |
| 15 | **vertigo** | effect `vertigo` (`amount` 0.15-0.25; background dolly-zooms, person stays) | dramatic realization, "this changes everything", tension | riser |
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
