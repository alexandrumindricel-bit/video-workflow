# video-workflow

Turns a raw talking-head video into a finished vertical short (1080x1920 MP4) in a fixed editing style:
transcription, lip-sync-safe removal of silences and mistakes, a storyboard, word-by-word captions with highlighted
keywords, motion graphics, sound effects and the final render.

- `SKILL.md`: the step-by-step workflow (also a Claude Code skill: link this folder into `~/.claude/skills/edit-video`)
- `STYLE_GUIDE.md`: the editing style it follows
- `vw.sh`: `setup` · `prep RAW WORK` · `cut WORK` · `render WORK OUT.mp4`
- `templates/`: storyboard reference and example

Requirements: ffmpeg, Python 3 (`faster-whisper`, `opencv-python-headless<5`, `numpy`), Node with Playwright + Chromium.
Transcription downloads a Whisper model on first use: allow huggingface.co and *.hf.co (CDN) in the network policy.
