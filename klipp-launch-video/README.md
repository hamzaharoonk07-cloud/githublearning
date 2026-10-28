# Klipp launch film

`klipp-launch.mp4`: 31 s, 1080×1920 (9:16), 30 fps, H.264 + AAC. It has sound effects only and no music.

| Time | Scene |
|---|---|
| 0–3 s | The Clip Stack logo builds itself, then the klipp lockup |
| 3–7.5 s | "Free to edit. Pay to export?" Paywall chips get sliced in two, then "Klipp it." |
| 7.5–11 s | Every editing tool. **Free.** Forever. |
| 11–18 s | The editor: Roman Urdu captions word by word, then Urdu Nastaliq, then bilingual |
| 18–22.5 s | All of it, free: six promises get checked off |
| 22.5–26 s | One tap. 4K. Export, then "No watermark, ever." |
| 26–31 s | End card: tagline, Urdu line, "Coming soon to Android" |

## Rebuild

```sh
node render.mjs        # frames/ + cues.json (Playwright + Chromium)
python3 sfx.py         # sfx.wav, synthesized from cues.json (numpy + scipy)
ffmpeg -framerate 30 -i frames/%05d.jpg -i sfx.wav -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart klipp-launch.mp4
```

Open `index.html` in a browser for a live, looping preview. All timing lives in `index.html`. Each sound cue is declared next to the animation it belongs to, so picture and sound stay in sync when you retime anything.

Fonts are Bricolage Grotesque, Plus Jakarta Sans, JetBrains Mono and Noto Nastaliq Urdu, all under the OFL and stored in `fonts/`.
