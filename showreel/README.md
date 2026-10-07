# Claude — Motion Showreel '26

A 15-second, 1080p60 motion-design showreel. Every frame and every sound is generated from code: no stock footage, no samples, no keyframe editor.

**Watch:** [`showreel.mp4`](showreel.mp4)

| Bar | Time | Chapter | Technique |
|---|---|---|---|
| 1 | 0.00s | Intro | dot → line → slit reveal, masked type, circle wipe |
| 2 | 1.88s | Kinetic type | `I / MAKE / THINGS / MOVE●`, skew wipes, squash and stretch, a dive into the full stop |
| 3 | 3.75s | Systems | 144-cell morphing grid, radial wave, tips into an extruded isometric view |
| 4 | 5.63s | Particles | 2,600 particles in 3D: burst → Fibonacci sphere → (2,3) torus knot → implode |
| 5 | 7.50s | Fluids | real metaballs with topographic contours and a node-graph overlay |
| 6 | 9.38s | Editorial | half-beat cuts, a graph-editor bezier, an EQ, an RGB-split glitch, a stripe wipe |
| 7 | 11.25s | Build | accelerating tunnel, speed lines, counter, 16th-note strobe |
| 8 | 13.13s | End card | spark mark, tracking settle, typed subtitle |

Craft details: 6-sample 180° motion blur on every frame, beat-locked camera shake, a difference-blended HUD (timecode, chapter roller, beat tick), film grain, and a vignette. The score is a 128 BPM track synthesized in numpy (kick, clap, hats, sidechained bass and pad, risers, glitch stutters, and a drop), with hits locked to the picture.

## Rebuild

```sh
node render.mjs              # renders showreel_video.mp4 (headless Chromium + ffmpeg)
python3 score.py             # synthesizes showreel_audio.wav
ffmpeg -i showreel_video.mp4 -i showreel_audio.wav -c:v copy -c:a aac -b:a 256k -shortest showreel.mp4
```

Open `reel.html` in a browser to watch a real-time preview, without motion blur.
