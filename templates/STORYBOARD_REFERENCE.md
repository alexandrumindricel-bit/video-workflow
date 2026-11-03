# storyboard.json reference

All times are seconds on the **cut** timeline (`words.json`). `start`/`end` are required on every element.

```jsonc
{
  "style": "editorial",            // "editorial" (green/cream) | "depth" (blue 3D) | "bold" (white + yellow keyword)
  "captions": {
    "keywords": ["word", ...],     // case/punctuation-insensitive; highlighted (gold italic / blue 3D hero)
    "keyword_ids": [12, 40],       // or exact word indices (field "i" in words.json)
    "max_words": 4,                // per caption chunk (default 4 editorial, 3 depth)
    "mode": "karaoke",             // "karaoke" (all words shown, spoken ones lit) | "pop" (words appear one by one)
    "y": 1420,                     // optional center y; default from layout.json
    "enabled": true
  },
  "elements": [ ... ],
  "transitions": [ {"at": 4.2, "kind": "zoom_through|flash|glitch|leak|whoosh|impact|paper", "dur": 0.2, "sfx": "auto|name|null"} ],
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
| `tiles` | `text` ("100%"), `stagger` | typewriter tiles, alternating dark/cream, one per character | front |
| `glass` | `text`, `size` | giant translucent glass letters with a light sweep | back |
| `cover` | `text`, `size`, `issue`, `y`, `lines: []`, `lines_y` | magazine masthead, letters drop in | back |

| `product3d` | `product` (slug from `products/catalog.json`), `pos: side\|hero\|top`, `side: left\|right`, `mode: cutout\|card`, `views: [i…]`, `depth` 14, `glow`, `name`, `price: false`, `price_text`, `info: false`, `info_at`, `site_text`, `box: {x,y,w,h}` | mindricel.ro product: extruded cut-out turns between its photo angles (turntable), floats, glow, shadow, reflection, light sweep; info card with name, price, sizes; card mode = 3D-tilted photo card | front |

`layer: "front" | "back"` overrides the default on any element. Back-layer elements automatically turn the
person cut-out on while they are visible.

### Camera / compositing effects (`effects[]`, rendered by scripts/fx.py)
| kind | fields | result |
|---|---|---|
| `punch` | `scale` 1.06-1.12 | constant punch-in (same as `zooms`) |
| `push` | `from`, `to` | smooth digital zoom over the effect duration |
| `vertigo` | `amount` 0.15-0.25 | dolly zoom: background zooms, person stays the same size |
| `frame_break` | `rect: [x,y,w,h]`, `color`, `radius`, `border` | video shown inside a frame on a dark blurred canvas; the person extends out of it |
| `pull_back` | `scale` 0.5-0.65, `y` (center of the window), `bg` (hex or "blur") | video shrinks into a floating rounded window; put an `app`/`card` above it |
| `sticker` | `width` 16 | white sticker border around the person (use with a `backdrop`) |
| `outline` | `gap` 22, `width` 7, `color` | boiling hand-drawn outline around the person |
| `cutout` | - | force the cut-out (rarely needed) |
Transition `zoom_through` (`at`, `dur` 0.36): zoom + radial blur into and out of a cut.

`flash` / `leak` can also be used as elements, but prefer `transitions`.
