# Baseer — بصير · Arabic Field Inspection Copilot

**The AI that sees, understands, and acts — in Arabic.**

Baseer turns a short phone video or photo set from a worksite into a finished
inspection report — then opens a corrective-action case for what it found,
and verifies the fix on re-inspection, with a human approving every closure. **SAM 3.1** segments the scene — equipment, workers, PPE,
vehicles, visible hazards — and **Muse Spark** reasons over those segments
together with the inspector's Arabic voice or text notes. The output is a
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
