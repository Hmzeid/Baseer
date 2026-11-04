# REVIEW — Baseer walkthrough (v1)

Checked with `npx hyperframes check` (0 errors), exact-frame snapshots at the SPEC QA times,
and `snapshot --review` (beats, 8 seams, phone width).

- Hook (0–7 s): real scaffold photo full-bleed at frame 0 with the first line readable;
  the photo carries into the upload thumbnail. Demo disclosure shown 2.1–5.0 s.
- Every cursor click lands on the real button (positions measured from the live DOM at capture).
- Live scene plays the real warehouse footage inside the captured stage; alerts land one by one.
- Seams are blur swaps on one stage, plus one carry-across (hook) and one iris from the theme
  toggle (Arabic → dark); no crossfades between worlds.
- Phone width: captions (40 px at 1080) stay legible at 360 px wide.

Known and accepted:
- `nested_media_start_basis_ambiguous`: `#live-feed` data-start 1.9 is scene-local on purpose.
- Findings, alerts and chat answers are mock-mode outputs; the film says so twice.

BANNED additions after this pass: none needed.

## v2 — voice and music
- Narration: local Kokoro `af_heart`, one line per scene, each placed so its key words
  land on the matching action (e.g. "approve the closure" over the approval dialog).
- Music: local MusicGen bed at 0.12, 0.4 s fade-in, 1.5 s fade-out under the end card.
- Clicks: 11, one per real cursor click, two alternating takes, peak one frame after the press.
- Measured (not heard): -15.6 LUFS integrated, true peak -2.9 dB, no clipping; click onsets
  confirmed within 0.1 s of every cursor click. Listen once before publishing.

## v3 — 3-minute Meta submission cut (live outputs)
- `check`: 0 errors; craft warnings resolved (dead stretches got purposeful camera moves, diagram
  text raised to 28 px, vision-path note shortened and held long enough). One accepted lint note:
  `#live-feed` data-start is scene-local.
- Snapshots at 28 instants across all 16 scenes reviewed; frame 0 shows all three real photos.
- Every on-screen/narrated claim traced: 3 high findings + 40 s (hero run), refusal text and
  acceptance text (verify calls), 2 live alerts, benchmark 6/8, 16/24, SAM precision 0.60 (README).
- Measured (not heard): -15.4 LUFS, true peak -1.7 dB, no clipping; 9/9 clicks within 0.15 s.
- History dates were back-dated for the deadline views; said so in the YouTube description.
