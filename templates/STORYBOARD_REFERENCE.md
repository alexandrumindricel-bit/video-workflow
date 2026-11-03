# storyboard.json reference

All times are seconds on the **cut** timeline (`words.json`). `start`/`end` are required on every element.

```jsonc
{
  "style": "editorial",            // or "depth"
  "captions": {
    "keywords": ["word", ...],     // case/punctuation-insensitive; highlighted (gold italic / blue 3D hero)
    "keyword_ids": [12, 40],       // or exact word indices (field "i" in words.json)
    "max_words": 4,                // per caption chunk (default 4 editorial, 3 depth)
    "mode": "karaoke",             // "karaoke" (all words shown, spoken ones lit) | "pop" (words appear one by one)
    "y": 1420,                     // optional center y; default from layout.json
    "enabled": true
  },
  "elements": [ ... ],
  "transitions": [ {"at": 4.2, "kind": "flash|glitch|leak|whoosh|impact|paper|punch", "dur": 0.2, "sfx": "auto|name|null"} ],
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

`flash` / `leak` can also be used as elements, but prefer `transitions`.
