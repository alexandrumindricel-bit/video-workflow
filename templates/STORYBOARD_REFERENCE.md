# storyboard.json reference

All times are seconds on the **cut** timeline (`words.json`). `start`/`end` are required on every element.

```jsonc
{
  "style": "depth",                // "editorial" (green/cream) | "depth" (3D gradient) | "bold" (white + yellow keyword)
  "palette": "mindricel",          // brand theme for ALL graphics (orange #FF6600, ink #0A0A0A, white)
  "captions": {
    "style": "lockup",             // caption style: "lockup" (default) | "clean" | "depth" | "bold" | "editorial"
    "motion": "whip",              // lockup: "whip" (default) | "fade" (calm topics)
    "semantic": true,              // lockup: green numbers/money, red negative words (false for calm topics)
    "min_contrast": 0.42,          // lockup: word vs background brightness; below -> white / charcoal
    "lead": 0.25, "hold": 1.2,     // lockup: show phrase this early / keep the last one this long
    "min_phrase": 1.0,             // lockup: shorter phrases merge with a neighbour
    "behind_share": 0.4,           // lockup: share of phrases slightly behind the head (depth); behind_max_hidden 0.25
    "headline_hold": 1.1,          // clean: seconds a headline stays after its keyword; headline_accent "alt"|"all"|"none"
    "palette": "scene",            // caption colours: "scene" (from the RAW footage, default) | "mindricel" (brand)
    "behind": "auto",              // some keywords behind the person (auto | [word indices] | false); behind_max_hidden 0.25
    "keywords": ["word", ...],     // case/punctuation-insensitive; highlighted (gold italic / blue 3D hero)
    "keyword_ids": [12, 40],       // or exact word indices (field "i" in words.json)
    "max_words": 4,                // per caption chunk (default 4 editorial, 3 depth)
    "mode": "karaoke",             // "karaoke" (all words shown, spoken ones lit) | "pop" (words appear one by one)
    "y": 1420,                     // optional center y; default from layout.json
    "enabled": true
  },
  "elements": [ ... ],
  "transitions": [ {"at": 4.2, "kind": "flash_blur|pixelate|zoom_through|flash|glitch|leak|whoosh|swoosh|impact|rewind|paper", "dur": 0.5, "sfx": "auto|name|null"} ],
  "effects": [ {"kind": "push|punch|vertigo|frame_break|pull_back|sticker|outline|cutout", "start": 1.0, "end": 2.0, ...} ],
  "zooms": [ {"start": 1.1, "end": 2.2, "scale": 1.1} ],   // punch-ins, piecewise constant, 1.06-1.12
  "sfx": [ {"at": 3.0, "name": "ding", "gain_db": -12} ],  // extra manual SFX
  "sfx_gain_db": 0,                                         // global SFX offset
  "music": {"file": "/path/track.mp3", "gain_db": -18}      // optional, auto-ducked
}
```

## Common element fields
`pos`: `"top"` (default, above the head) · `"lower"` (chest, above captions) · `"center"` (avoid - covers face)
`y`/`h`: explicit placement in px instead of `pos` · `scale`: extra size factor · `in`/`out`: fade times
`sfx`: `"auto"` (default) · a sound name · `null` · `hide_captions`: true hides subtitles while shown

## Element types
| type | fields | look / animation | auto SFX |
|---|---|---|---|
| `title` | `lines: [{text, font, size?, gold?, boxed?}]`, `anim: rise\|drop\|pop` | giant type; fonts: `serif` (condensed caps), `heavy` (Inter Black caps), `italic` (serif italic), `mono` (small label), `depth`, `depth-white` | whoosh |
| `card` | `icon` (emoji/text) or `image`, `title`, `subtitle` | app-style card: icon tile + bold title + mono subtitle | pop |
| `prompt` | `label`, `text`, `cps` | chat input that types the text, send button | pop + typing ticks |
| `strike` | `text`, `strike_at`, `size` | big word, red line strikes through it | swoosh + click |
| `counter` | `from`, `to`, `label`, `format: "clock"`, `prefix`, `suffix`, `count_end` | big number counting | pop |
| `stat` | `value`, `label` | huge figure + caption | pop |
| `step` | `n`, `text` | numbered badge + label | click |
| `list` | `items: ["a", {"text": "b", "at": 5.1}]`, `stagger` | checklist, items slide in | click per item |
| `comment` | `cta`, `text`, `reply`, `reply_at` | CTA label + comment typing + reply bubble | pop + ticks |
| `follow` | `handle`, `tagline`, `button`, `avatar` | profile/follow card | ding |
| `image` | `src` (absolute path or file:// URL) | framed screenshot/logo | pop |
| `label` | `text` | small mono label | - |
| `frame` | - | thin cream magazine border | - |

### Effect elements (see EFFECTS.md for when to use them)
| type | fields | look / animation | default layer |
|---|---|---|---|
| `orbit` | `items: [{icon,text,image}]`, `rx` 430, `ry` 110, `dy` 200, `speed` 0.12, `card_scale` | cards circle the speaker; far side passes behind them | both |
| `wall` | `items: ["text" or {text,image,head}]`, `kind: paper\|screen`, `stagger` | taped notes / screenshot cards pop onto the wall, skipping the face | back |
| `app` | `title`, `tiles: ["Raw 1" or {text,image}]`, `chip`, `chip_at`, `input`, `cps` | app window: tiles pop in, chip stamps, input types | front |
| `phone` | `title`, `messages: [{from: me\|them, text, at}]`, `button`, `side`, `y`, `scale` | phone slides in from the side, bubbles pop | front |
| `checklist` | `title`, `items: ["a" or {text,at}]`, `stagger` | dark card, items tick green one by one, "1 of 3" | front |
| `chart` | `title`, `values`, `labels`, `tag`, `grow`, `color` | line chart draws itself, tag pops at the end | front |
| `backdrop` | `kind: app\|paper\|image\|gradient\|color`; app: `label`, `title`, `timer` (s), `items`; image: `src` | full background replacement (wipes in) | back |
| `doodle` | `shapes: [{shape, x, y, size, color, width}]` - star, sparkle, circle, spiral, arrow, underline, scribble, x, heart, clapper | hand-drawn strokes draw on, then "boil" (jitter 10x/s) | front |
| `tiles` | `text` ("400-600"), `unit` ("cm³"), `count` 0.7, `look: "classic"` | modern: dark rounded pill, big digits counting up, unit in orange (classic = old squares) | front |
| `glass` | `text`, `size` | giant translucent glass letters with a light sweep | back |
| `cover` | `text`, `size`, `issue`, `y`, `lines: []`, `lines_y` | magazine masthead, letters drop in | back |

| `product3d` | `product` (slug from `products/catalog.json`), `pos: side\|hero\|top`, `side: left\|right`, `mode: cutout\|card`, `views: [i…]`, `depth` 14, `glow`, `name`, `price: false`, `price_text`, `info: false`, `info_at`, `site_text`, `box: {x,y,w,h}` | mindricel.ro product: extruded cut-out turns between its photo angles (turntable), floats, glow, shadow, reflection, light sweep; info card with name, price, sizes; card mode = 3D-tilted photo card | front |

| `combo` | `top` (lead-in words), `hero`, `accent`, `bottom`, `font: cond\|tall\|heavy`, `look: solid\|grad\|neon`, `size` 300, `y`, `accent_x/accent_y/accent_size`, `pixels` 9, `neon_color`, `hide_captions` | reference "edited" title: spaced small words, huge word blurring/scaling in, handwritten accent written on with swoosh, pixel squares | front |
| `photos` | `items: [{src, caption, at}]` (src = WORK-relative path from images.py), `side`, `x`, `y`, `stagger` | white-bordered rounded photo cards fanned beside the person, glow flash entry, slow drift | front |
| `numcards` | `items: [{n, label, at}]`, `stagger` | white folded-corner paper cards with big italic numbers + labels | front |

`grade` (top level): default `{"preset": "natural", "strength": 1.0, "subject_pop": false}`; presets natural | warm_rich | simple | cinematic | warm | olive | clean | mindricel; or `{"preset": ..., "clips": [...], "strength": 0.85, "subject_pop": true}` - see EFFECTS.md.
Effect `track`: `{"kind": "track", "start", "end", "scale": 1.3, "smooth": 0.88}` - face-following zoomed crop.

`layer: "front" | "back"` overrides the default on any element. Back-layer elements automatically turn the
person cut-out on while they are visible.

### Camera / compositing effects (`effects[]`, rendered by scripts/fx.py)
| kind | fields | result |
|---|---|---|
| `punch` | `scale` 1.06-1.12 | constant punch-in (same as `zooms`) |
| `push` | `from`, `to` | smooth digital zoom over the effect duration |
| `vertigo` | `amount` 0.08-0.14 | dolly-zoom feel: the cut-out person grows, background stays sharp (no smear) |
| `frame_break` | `rect: [x,y,w,h]`, `color`, `radius`, `border` | video shown inside a frame on a dark blurred canvas; the person extends out of it |
| `pull_back` | `scale` 0.5-0.65, `y` (center of the window), `bg` (hex or "blur") | video shrinks into a floating rounded window; put an `app`/`card` above it |
| `sticker` | `width` 16 | white sticker border around the person (use with a `backdrop`) |
| `outline` | `gap` 22, `width` 7, `color` | boiling hand-drawn outline around the person |
| `cutout` | - | force the cut-out (rarely needed) |
Transition `zoom_through` (`at`, `dur` 0.36): zoom + radial blur into and out of a cut.

`flash` / `leak` can also be used as elements, but prefer `transitions`.
