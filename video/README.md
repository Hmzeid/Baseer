# Baseer by Veebase — walkthrough video (HyperFrames)

The 90 s walkthrough at `docs/media/baseer-walkthrough.mp4` is built from this
project. Everything on screen is the real console, captured from a mock-mode
instance seeded by `backend/demo_seed.py`. See `SPEC.md` for the shot list and
`STORYLINES.md` for the two alternative films.

```bash
cd video
npx hyperframes preview          # edit in the browser preview / HyperFrames desktop app
npx hyperframes check            # lint, layout, contrast and craft checks
npx hyperframes render --quality looks -o ../docs/media/baseer-walkthrough.mp4
```

- **Not in git** (rebuilt locally): `assets/shots/`, `assets/voice/`, `assets/bgm/`, the
  footage/photo derived from `demo/` and the rendered MP4. Recreate them with the steps below.
- `assets/shots/*.jpg`: 3840×2160 captures of the UI. `assets/boxes.json` holds
  the on-screen boxes of every button the cursor clicks, measured at capture time.
- `compositions/*.html`: one scene each (hook, upload, report, chat, case, live,
  records, arabic, end). Captions are plain text in each file; edit them freely.
- **Sound** (all made on this Mac, no accounts): narration by the local Kokoro
  voice `af_heart` (`assets/voice/`, normalized to -16 LUFS in `assets/voice/norm/`,
  script in `NARRATION.md`); music bed from local MusicGen (`assets/bgm/bed-loop.wav`,
  a 28 s seed crossfade-looped to 106 s, volume 0.12 under the voice); cursor clicks
  from the bundled SFX (`assets/sfx/`). The mix measures -15.6 LUFS, true peak -2.9 dB.
  Tools live in `~/.venvs/hyperframes-audio` (`HYPERFRAMES_PYTHON` points at it).
- **Rebuild**: `python3 tools/gen_video.py` rewrites `index.html` and `compositions/`
  (scene timing, captions, voice cue points, click times all live in that script).
- To re-capture after UI changes, run the seeded dev server and re-run
  `tools/capture.cjs` (Puppeteer) (the shot names in `compositions/` must match).

---
*Baseer is a Veebase product. © 2026 Veebase.*
