# Baseer — بصير · Arabic Field Inspection Copilot

**The AI that sees, understands, and acts — in Arabic.**

Baseer turns a short phone video or photo set from a worksite into a finished
inspection report — then opens a corrective-action case for what it found,
and verifies the fix on re-inspection, with a human approving every closure. **SAM 3.1** segments the scene — equipment, workers, PPE,
vehicles, visible hazards — and **Muse Spark** reasons over those segments
together with the inspector's Arabic voice or text notes. **Live note
(Oct 26): SAM 3.1 is per-team gated and this team is gated (404), so the
live path currently uses Muse's own multimodal vision on the frames
instead — same report schema, but no bounding-box overlays, only frame
indices and regions described in words. The report records
`segmentation_source` so the difference is always visible.** The output is a
structured report in Arabic (with an English summary): every finding carries a
severity, the exact frame as evidence, and a recommended corrective action.

Built for the **Meta Global AI Developer Hackathon** (Startup track ·
*Build for Your World*), Oct 26 – Nov 4, 2026.

## Prior work — hackathon disclosure
Per the event's new-work rule: the scaffold in this repo (FastAPI backend,
mock pipeline, bilingual frontend, eval scorer, build plan) was authored
Oct 21, 2026, before the event, as preparation. All event-week work — live
Meta Model API integration (SAM 3.1 + Muse), video path, live-camera wiring,
voice notes, the evaluation run, and the demo video — starts Oct 26, 2026
and is the work submitted for judging. Demo media note: the `demo/` text
files document footage sources; large video/photo files are not stored in
this repo and are re-fetched from the sources listed in `demo/SOURCES.md`
(Pexels License).

## Input modes
1. **Upload inspection** — a photo or short video goes in, the inspection
   starts immediately, and the report lands in ~30 seconds.
2. **Live camera** — a camera connected to the system streams frames;
   Baseer samples and segments them as they arrive, raises an alert the
   moment a violation appears, and finishing the session produces the
   full report — same pipeline, same cases, same chat and analytics.
   Use cases: factories (flagship demo), construction sites, farms —
   with real footage: staged on site, openly licensed, or a live camera.

## Why
Across the Middle East, safety and quality inspections on factory floors,
construction sites, and farms are still documented with phone photos and
handwritten Arabic notes, then typed up hours later — slow, inconsistent, and
easy to miss a missing guard rail or a worker without PPE. Baseer makes the
report a by-product of the walkthrough itself.

## Run it (prep build — mock mode)
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
# open http://localhost:8000
```
Mock mode runs the full pipeline with synthetic segmentation/reasoning
outputs — no API key needed. For live mode, copy `.env.example` to `.env`,
set `BASEER_MODE=live`, and fill the Meta Model API values.

## Scope
Core = the inspection (capture → structured report in ~30 seconds).
Two layers hang off the completed report, never before it:
- **Evidence chat** — ask Baseer about an inspection ("why is finding 1
  high?", "draft the contractor notice"); answers grounded strictly in the
  report's findings and frames, Arabic or English.
- **Analytics (light)** — the safety manager's view across reports: totals,
  severity mix, most frequent hazards, recent activity.
Integrations (WhatsApp/PDF share, VeeSign, VeeArchive, CMMS) are a stretch /
roadmap item — see BUILD_PLAN.md.

## Layout
- `backend/` — FastAPI service: pipeline (`pipeline.py`), Meta Model API
  adapter (`meta_client.py`, mock/live), prompts (`prompts.py` — inspection
  reasoning draft v1 + evidence-chat prompt), analytics (`analytics.py`),
  live-camera sessions (`live.py`)
- `frontend/` — bilingual EN/AR app (single file): capture form, report,
  evidence chat, analytics strip
- `BUILD_PLAN.md` — day-by-day build plan and submission checklist
- `demo/` — demo footage plan (staged/public material only)

## Evaluation benchmark (run Oct 26, 2026 — live vision path, muse-spark-1.3)
24 labeled scenes from the same staged/public Pexels footage as the demo
(`demo/SOURCES.md`; binaries re-fetched via `eval/fetch_media.py`, never
committed). The set was fixed in `eval/scenes.json` before the run and
covers positives, compliant negatives, and uncertain-by-design scenes
(poor light, face out of frame, a note contradicting the image).
Method: up to 3 evenly spaced frames per scene through the live vision
pipeline (`eval/run_live.py`), finding titles mapped to hazard labels by a
fixed keyword map; unmapped titles count as their own label so surprises
are scored, never dropped. Scored with `eval/score.py`.

Result: precision 0.128, recall 0.75, F1 0.218 (TP 6, FP 41, FN 2;
36 false alarms on 18 negative scenes). Exact scene matches: 3/24
(flagship factory, scaffold helmet, one compliant crew photo).

What works: core hazards are found — worker without helmet 3/4
(F1 0.75), ladder violations 2/2 (F1 0.8), unmarked forklift path 1/1.
Uncertainty honesty holds: 5 of 6 uncertain-by-design scenes carry an
"uncertain" determination.

Failures (published, not tuned away):
- Over-eager observations: 11 of 12 clean negatives drew flags — mostly
  cautious "unable to verify X" wordings, but also genuine hallucinations
  (bare hands on gloved hands, a hanging mask on a masked textile worker).
- The welder with a raised hood (true `missing_eye_protection`) was missed
  while that same label fired 5 times elsewhere.
- The contradiction scene (note claims full compliance, frame shows a
  helmet in hand) produced an "unconfirmed" slug instead of the exact
  `worker_without_helmet` label.
- Compliant scenes rarely come back exactly empty (1/12); the model hedges
  with `uncertain=True` on ~22/24 scenes while still emitting findings.

Takeaway for production: recall first is the right bias for safety, but
the prompt must stop minting "unable to verify" findings and the label
space needs constraining before precision is acceptable. Re-run with
`muse-wonder-1.0` (locked for final reports) is open.
