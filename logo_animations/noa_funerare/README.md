# NOA Funerare — animație logo

Porumbelul intră în cadru din dreapta, bate din aripi, planează și se așază pe litera „A”, exact în poziția din logo.
Literele apar în stil memorial: N, O, A se ridică lent din ceață (blur → clar), FUNERARE apare literă cu literă
iar spațierea se strânge ușor, o lumină palid-aurie trece de două ori peste logo, praf luminos plutește în întuneric,
iar la aterizare un halo discret apare în spatele lui „A”. Ultimul cadru este logo-ul original.

```
python3 animate.py                       # 1920x1080, 60 fps, 11 s -> out/noa_funerare_landscape.mp4
python3 animate.py --format vertical     # 1080x1920 (Reels / TikTok / Shorts)
python3 animate.py --format square       # 1080x1080
python3 animate.py --still 7.5           # un singur cadru PNG, pentru verificare
```

Toate formele sunt decupate din `logo.jpg`. Necesită: numpy, scipy, opencv-python-headless, Pillow, ffmpeg.
