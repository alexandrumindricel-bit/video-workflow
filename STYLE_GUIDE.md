# Short-Form Editing Style Guide
*Distilled from 3 reference videos (vertical 9:16, 13s / 35s / 58s)*

| Ref | Creator handle on screen | Length | What it is | Core visual idea |
|---|---|---|---|---|
| **A** | @viewcci | 13s | SFX / transition pack showcase | Dark moody desk shot; the transitions themselves are the content |
| **B** | @socialcontentking | 35s | "Text behind subject" tutorial | Big blue gradient 3D words living *behind* the speaker |
| **C** | @justyn.ai | 58s | "Claude edited this video" | Editorial / magazine look: forest green + cream, serif titles |

The three share one DNA: **vertical talking head + typography as the main graphic + a constant flow of UI-style overlays + a cut or visual change every 2–3 seconds.** Below, each element shows the common rule first, then the variants you can choose from.

---

## 1. Cut rhythm & pacing

**Measured cut points (scene detection):**
- **A:** 0.2 · 2.1 · 4.3 · 6.8 · 9.0s. One beat about every **2.2s**, very regular, like a metronome.
- **B:** 2.9 · 5.3 · 8.2 · 9.9 · (tutorial 9.9→24.9) · 24.9 · 27.7 · 30.8s. A-roll cuts every **2.5–3s**. The screen-recording section runs ~15s but changes step every 3–5s.
- **C:** 0.2 · 2.1 · 2.4 · 2.9 · 6.4 · 7.8 · 15.1 · 16.8 · 22.3 · 24.4 · 27.1 · 28.5 · 31.9 · 33 · 40.4 · 43.5 · 54s. Median **~2.5s**, but **4 visual changes in the first 3 seconds**.

**Rules**
1. **Hook = fastest section.** Change something (cut, title, background, graphic) every **0.5–1s** for the first 3s.
2. **Body = 2–3s rhythm.** Hold any shot no longer than ~3s unless something is moving inside it: a caption change, a punch-in, a graphic entering.
3. **Something on screen changes at least every ~1s**, even with no cut (new caption chunk, a word highlight, a UI card typing).
4. **Jump-cut out every breath, "um" and pause.** Words butt against each other, and there's zero dead air in the speech.
5. **Structure:** Hook (0–3s) → Promise/context (3–10s) → Proof/demo section with a different visual mode (screen recording, UI mockups) → Payoff back on face → CTA card → Outro card.
6. **Mode switch every 10–15s** (talking head → screen-recording frame → talking head with heavy graphics), so the video "resets" attention.

---

## 2. Captions & typography

Two caption layers run at once in B and C:
- **Layer 1, subtitles:** the spoken words, small and consistent, always readable.
- **Layer 2, keyword titles:** 1–3 words blown up huge, designed like a poster.

### Variant B: "Depth captions" (blue 3D)
- **Keyword font:** heavy geometric sans, ExtraBold/Black (Montserrat Black, Gilroy Heavy, Poppins Black). ALL CAPS for keywords ("TEXT", "LIVING", "DEPTH", "DO IT").
- **Keyword color:** **blue vertical gradient**, light sky blue (#8FD3FF) on top → royal blue (#1E6FE0) at the bottom, with a subtle bevel/inner highlight and a soft dark drop shadow (blur 10–20px, ~40% opacity) so it reads as 3D.
- **Secondary words:** small white lowercase in the same family, bold, scattered *around* the keyword ("on" … "top of the" above "video"; "it / should / be" spaced across above "LIVING"). Second keyword line in **white/light-grey gradient** ("INSIDE IT").
- **Size:** keyword ≈ 70–85% of frame width; small words ≈ 15–20% of the keyword height.
- **Position:** chest height at first, later head height. Text is **masked behind the subject** (head/shoulders/mic cover letters), which is the signature move.
- **Animation:** words pop in one at a time, synced to speech: scale 80→100% with a slight blur-to-sharp and a fade in ~4–6 frames, holding for the phrase, then the next group replaces it. A big number counter ("00:10 seconds") ticks in real time as a hook device.
- **Special:** curved text on a circular path wrapped around the body ("wrapped around you"), with the part behind the body masked.

### Variant C: "Editorial magazine"
- **Palette:** deep forest green **#1F3B2D**, cream **#F1EBDD**, muted gold accent **#C9B37E**, and a dimmed green-grey **#7F9786** for not-yet-spoken words.
- **Title fonts (mixed on purpose, one style per phrase):**
  - Condensed high-contrast serif, caps ("I DIDN'T EDIT", "HUG", "NEVER") → Editorial New / Playfair Display Condensed / Ogg.
  - Ultra-heavy grotesk, caps, tight tracking ("A SINGLE SECOND", "BIGGER") → Druk / Inter Black / Neue Haas Black.
  - Italic serif, sentence case ("*Claude did.*", "*captions.*") → Playfair Italic / Editorial New Italic, sometimes in gold.
  - Monospace micro-labels: timecode "00:00:01:06", "TO CLAUDE", "NO. 01 · OCTOBER 2026 · EDIT" → JetBrains Mono / Space Mono, small, letter-spaced, low opacity.
- **Subtitles:** cream condensed serif (~5–6% of frame height) in a **solid dark-green rectangle**, tight padding, square corners. Placed **center, ~70% down the frame** (below the chin, over the chest/hands). **2–4 words per chunk.** **Karaoke highlight:** spoken words cream, upcoming words dimmed green-grey.
- **Emphasis captions:** occasionally a single word becomes much bigger in the same box style ("captions", "come in"), or each word gets its **own green box** in white heavy caps ("THAT'S | JUST | ONE | MORE"), popping in word by word.
- **Title animation:** letters slide/drop in individually (the "CLAUDE" masthead letters fall into place, some still mid-air and offset), words wipe up from a baseline mask ("A SINGLE / SECOND" rising), and the timecode runs live. Titles sit **in the top 35% of the frame** and often overlap the top of the head.

### Variant A: "Header label"
- Static header across the top for the whole video: **"With This"** (white, heavy sans) + **"Use This"** (same font but **outlined**/stroke only). Two columns, top 10–15% of the frame. No spoken subtitles; the text explains the format and the visuals carry it.

### Universal caption rules
- Never more than ~4 words per subtitle chunk.
- One **hero word** per sentence gets the big treatment.
- Keep the subtitle in a fixed spot, and let titles move around.
- Contrast: always a box, shadow, or the subject's dark clothing behind white text.
- Stay inside the safe zone: nothing important in the bottom ~18% (the platform UI covers it) or the right ~12% (buttons).

---

## 3. On-screen graphics & motion

Recurring overlay vocabulary, all styled like **clean app UI**:

| Element | Look | Seen in |
|---|---|---|
| **Glass cards** | Rounded 16–24px corners, translucent dark fill + background blur, thin 1px light border, soft glow in the accent color | A (effect preview cards with thumbnail, name "Matte Popshots · 0.7s", download icon), B (phone-frame screen recording) |
| **Sound-library pill** | Dark rounded pill, small icon square, title + "LEOPARD · 00:01" metadata line | A |
| **Chat / prompt bubble** | White rounded input bar, small mono label "TO CLAUDE", text typing in live, circular dark-green send button with ↑ arrow | C |
| **App icons with strike** | Real app icon + red diagonal strikethrough line drawing across ("No CapCut", "no Edits app") | C |
| **Magazine-cover frame** | Thin cream border inset around the frame, masthead title, issue line in mono | C |
| **Picture-in-picture** | Raw/behind-the-scenes clip in a thin white-bordered vertical rectangle top-right, with a label chip ("**1:16** of raw footage") and a speed badge ("▶▶ 2.3×") | C |
| **Circular face-cam** | Speaker in a circle with a blue ring at the bottom center over a screen recording | B |
| **Numbered step badges** | Blue outlined circle with number (①②③④), top-left | B |
| **Timers / counters** | Big digital "0:54" or "00:10 seconds" in a dark box or gradient, live counting | B, C |
| **Collage wall** | Grid of other people's thumbnails/posts to show social proof | C |
| **Comment UI** | Fake IG comment being typed ("EDIT") + reply bubble ("Sending it over.") | C |
| **Profile/follow card** | Avatar + handle + "Following" pill, bottom of frame | B, C |
| **Watermark** | Small IG glyph + @handle, right side at ~25% height, white, ~60% opacity | All |

**Motion rules**
- Elements **enter with ease-out** (fast start, soft landing), 6–10 frames, usually scale 90→100% + fade, or slide 20–40px + fade.
- Exit faster than they enter (3–5 frames) or get replaced on a cut.
- **Typing animations** for any text inside UI (prompts, comments).
- Graphics are **timed to the exact word** that mentions them ("No CapCut" → the CapCut icon appears on "CapCut").
- The speaker **points at the graphic** (A: a finger to the card on every beat). Leave space in the frame where the graphic will land, and gesture to it while filming.
- Subtle constant motion: slow punch-in (100→105%) across a shot, or a floating card drift.

---

## 4. Transitions

| Transition | How it looks | Where |
|---|---|---|
| **Hard jump cut** | Default: 80% of all cuts | All |
| **Punch-in jump cut** | Same angle, cut to a 110–130% zoom for emphasis | B, C |
| **Angle change cut** | Switch camera position (close selfie → medium → wide squat → low angle) | C |
| **Light leak / film burn** | Orange-red burn washing the whole frame, ~6–8 frames | A (opening) |
| **White flash** | 2–3 frames of pure white | A |
| **RGB glitch / chromatic split** | Red-cyan offset + stretch smear, ~4–6 frames | A |
| **Paper crumple / tear** | Paper texture balls up over the subject, then tears away to reveal the next shot | A |
| **Energy glow** | Purple/violet bloom flaring around the subject | B (payoff moment) |
| **Swirl blur into mockup** | A-roll spins/blurs into a dark abstract background holding the screen-recording frame | B |
| **Color-wipe reveal** | A thin horizontal line sweeps across, revealing a new grade (bright → moody) | C |
| **Background swap** | The room behind the cut-out subject wipes to a solid brand color (green) for title moments | C (hook) |

**Rule:** use **hard cuts** as the base, and save stylized transitions for **section changes and payoffs** (1 every 5–10s max), except in a showcase video like A, where every beat gets one.

---

## 5. Framing & camera

- **Format:** 9:16 vertical, 1080×1920 (or higher).
- **Subject:** centered horizontally, **eyes at ~35–40% from the top**. Headroom is left on purpose for titles, and titles often overlap the top of the head.
- **Shot size:**
  - A: medium shot at a desk (waist up, desk across the bottom third), static tripod.
  - B: medium-wide seated (knees up), holding a handheld mic as a prop.
  - C: **mixed angles.** A wide-lens close selfie (face fills the upper half), medium seated, wide full-body squatting, and a low "from the desk" angle. The camera is sometimes handheld/close for energy.
- **Lighting & set:** practical lights in the frame (warm lamps, glowing orb, LED strip), a dark or deep-colored background, warm skin tones. **Moody, low-key, warm highlights vs cool/dark shadows.**
- **Wardrobe:** solid or textured mid-to-dark tops so white captions pop. The patterned jacket in C works because captions sit in solid boxes.
- **Gestures:** big, constant hand movement; pointing up to graphics; holding a prop (mic, glasses) to fidget with.
- **Grade:** slightly crushed blacks, warm practicals, mild teal/green shadows (C leans green to match the brand palette).

---

## 6. Sound design

*What I could measure from the audio (I analyzed waveforms/spectra, so per-cut SFX are inferred, not confirmed by ear):*

- **A** has true digital silence between beats and bright, high-frequency bursts right on the transitions (0.0s, 2.0s, 4.3s, 6.6s). On-screen cards name the sounds: **"Click (camera shutter single)", "Camera burst shutter (9 shots)", "Paper bag rough", "Futuristic click puzzle robot"**. So: **one SFX per transition, matched to the visual** (shutter on flash, paper on paper-tear, glitch-click on RGB split).
- **B and C** keep a constant low-level bed under the voice (the noise floor never drops below ~−30 to −36 dB, even between words) → **background music ducked well under the voice**, roughly −20 dB relative to speech.
- **B** has a bright burst at the purple-glow payoff (~27.3s), so a **whoosh/shimmer on the big transition**.
- **All three outros** end with a loud, **bass-heavy sting** (energy concentrated around 400 Hz and below) under the IG logo card.

**Rules to reuse**
1. Voice is king: clean, compressed, around −14 LUFS overall, with music ducked ~−20 dB under it.
2. **SFX on every graphic entry:** soft pop/click for cards and captions, typing ticks for chat bubbles, a swoosh for slides, a camera shutter for flashes.
3. **Bigger SFX (whoosh, riser, impact) only on section changes** and the payoff.
4. Match the SFX to the visual material (paper sound for paper, glitch for glitch).
5. Bass hit/sting on the outro card.

---

## 7. The first 3 seconds (hook formula)

**A:** frame 1 is already mid-transition (orange film burn) with the "With This / Use This" header visible. The format is understood instantly, the speaker points at the card, and the first SFX hits at 0.0s. **Hook = show the payoff immediately, explain nothing.**

**B:** first word on screen = giant blue "**TEXT**" over the chest. The spoken line is a contrarian statement ("your text should not be on top of the video… it should be LIVING INSIDE IT"), and **the hook demonstrates itself**: the captions are already doing the effect being taught. A countdown ("00:10 seconds") promises speed.

**C:** a bold, slightly provocative claim in 3 title treatments in 3 seconds: "**I DIDN'T EDIT**" (serif, background wipes to green) → "**A SINGLE SECOND**" (heavy grotesk + running timecode) → "*Claude did.*" (italic serif). The subject cut-out sits in front of a solid brand color. There's a cut/visual change every ~0.5s, and the speaker smiles into the lens, close up.

**Hook formula**
1. **Frame 1 must already be "in motion"**: a title animating, a transition mid-way, or the speaker mid-sentence. No fade from black, no "hey guys".
2. **Say a bold or contrarian claim in ≤ 7 words**, and put it on screen as a **huge title**, not just a subtitle.
3. **Make the hook demonstrate the thing** (the edit style *is* the proof).
4. **3+ visual changes in 3 seconds** (title swap, background swap, cut, graphic pop).
5. **Direct eye contact + an expressive face + a gesture** toward the text.
6. Add an **open loop**: a timer, a "here's how", or a number of steps.

---

## 8. CTA & outro

- **CTA overlay** (~6–8s before the end): a comment-bait card ("Comment "EDIT" and I'll send you the walkthrough") as a white rounded label top-center, then an animated IG comment being typed + a reply bubble.
- **Follow card** at the bottom: avatar, handle, tagline ("Daily AI tips"), and a "Following" pill.
- **Outro card (3–4s):** the video dims to ~30% brightness, a centered IG logo animates white → gradient → white, the @handle sits under it in small caps, and a bass sting plays.

---

## 9. Quick production checklist

- [ ] 9:16, eyes at ~35–40% from the top, headroom left for titles
- [ ] Moody set with warm practical lights, dark/solid wardrobe
- [ ] Hook: bold claim as a giant title, 3+ visual changes in 3s, no intro
- [ ] Jump-cut every pause; cut or punch-in every 2–3s
- [ ] Subtitles: 2–4 words, fixed position ~70% down, karaoke highlight, boxed or shadowed
- [ ] One hero word per sentence gets the big title treatment (pick one style family: **blue 3D depth** *or* **green/cream editorial**)
- [ ] Text-behind-subject masking on 2–3 key moments
- [ ] UI-style overlays (cards, chat bubbles, PiP, counters) timed to the exact spoken word
- [ ] Mode switch every 10–15s (talking head ↔ screen/mockup section)
- [ ] Stylized transitions only at section changes/payoff, each with a matching SFX
- [ ] Music bed ducked under the voice; pop/click SFX on every graphic
- [ ] Comment-keyword CTA + follow card + 3s logo outro with a bass sting
