# Baseer — بصير · Arabic Field Inspection Copilot

**The AI that sees, understands, and acts — in Arabic.**

Baseer turns a short phone video or photo set from a worksite into a finished
inspection report — then opens a corrective-action case for what it found,
and verifies the fix on re-inspection, with a human approving every closure. **SAM 3.1** segments the scene — equipment, workers, PPE,
vehicles, visible hazards — and **Muse Spark** reasons over those segments
together with the inspector's Arabic voice or text notes. **Live note
(Oct 27): SAM 3.1 answers via the Responses API — the Oct 26 404 was the
Chat Completions surface, not a team gate. The live path uses SAM in auto
mode and falls back to Muse's own multimodal vision on the frames when SAM
is unreachable — same report schema either way. The report records
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

## Production (on-site deployment)
Sign-in is required: accounts carry one of the Safety Supervisor, Site
Manager, Contractor, or Admin roles, and every case action is stamped
`username (role)` in the audit log. State is durable — inspections, cases,
users, and the audit trail live in `data/baseer.db` (SQLite, git-ignored)
with original uploads under `data/evidence/`; only in-flight live-camera
sessions are lost on a restart. First boot creates the `admin` user (set
`BASEER_ADMIN_PASSWORD`, otherwise a one-time password prints to the
server log). Run it as a service with `ops/com.veebase.baseer.plist`
(launchd, auto-restart, never port 8000), back up with `sh ops/backup.sh`,
and follow `ops/RUNBOOK.md` for restarts, key rotation, and staff changes.

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

## Evaluation benchmark (fixed 24-scene set, vision + SAM paths)
Demo filmed on the vision path (Muse multimodal reasoning); the SAM 3.1
segmentation path is evaluated alongside it — precision 0.600, recall
0.375 — see the SAM numbers below.
24 labeled scenes from the same staged/public Pexels footage as the demo
(`demo/SOURCES.md`; binaries re-fetched via `eval/fetch_media.py`, never
committed). The set was fixed in `eval/scenes.json` before any run and
covers positives, compliant negatives, and uncertain-by-design scenes
(poor light, face out of frame, a note contradicting the image).
Method: up to 3 evenly spaced frames per scene through the live vision
pipeline (`eval/run_live.py`), finding titles mapped to hazard labels by a
fixed keyword map; unmapped titles count as their own label so surprises
are scored, never dropped. Scored with `eval/score.py`. Both runs below
used the identical set, harness, and map; per-model evidence lives in
`eval/runs-spark/` and `eval/runs-wonder/`.

Spark 1.3 (dev default, Oct 26): precision 0.128, recall 0.75, F1 0.218
(TP 6, FP 41, FN 2; 36 false alarms on 18 negative scenes). Exact scene
matches: 3/24 (flagship factory, scaffold helmet, one compliant crew
photo). Core hazards found — helmet 3/4 (F1 0.75), ladder 2/2 (F1 0.8),
unmarked forklift path 1/1. Uncertainty honesty: 5 of 6
uncertain-by-design scenes carry an "uncertain" determination.

Wonder 1.0 (final-report model, Oct 26, prompt v1.2): precision 0.096,
recall 0.875, F1 0.173 (TP 7, FP 66, FN 1; 58 false alarms on 18 negative
scenes). Exact scene matches: 1/24. Recall is better — helmets 4/4,
ladders 2/2, path 1/1, contradiction scene nailed with the exact
`worker_without_helmet` label — but verbosity nearly doubles the false
alarms (66 vs 41): Wonder narrates far more "unable to verify"
observations as findings, and still missed the raised-hood welder (true
`missing_eye_protection`) while firing that label 9 times elsewhere.
Uncertainty honesty holds 6/6, but the model hedges on 23/24 scenes
while emitting findings anyway.

Wonder 1.0 re-run (Oct 27, prompt v1.3 finding-economy rule, same fixed
set/harness/map; evidence in `eval/runs-v13w/`, `eval/predictions-v13w.json`):
precision 0.412, recall 0.875, F1 0.560 (TP 7, FP 10, FN 1; 8 false alarms
on 18 negative scenes). Exact scene matches: 15/24. Recall fully preserved
(helmets 4/4, ladders 2/2, path 1/1, flagship exact) while false alarms
fell 58 → 8. 11 of 18 negative scenes come back exactly empty —
including every compliant crew/platform scene and both farm scenes.
Remaining failures, published: the raised-hood welder is STILL missed
(`missing_eye_protection` FN, fired once elsewhere on a spark close-up);
grinding/spark close-ups still draw 4 flags (disc guard, bare hands, one-hand
operation, eye protection on faceless frames); plus one flag each on the
dusk-ladder silhouette, the textile mask, and the lathe chuck; two positives
gained one extra finding each (a helmet call on the facade ladder, a
roof-edge call on the ladder-carry). Uncertainty honesty: uncertain
determinations now appear only where a finding exists (3 scenes), instead
of hedging everywhere.

SAM path (Oct 27, live SAM 3.1 segmentation via Responses API + Wonder 1.0
reasoning, prompt v1.3, same fixed set/harness/map; evidence in
`eval/runs-sam-v13/`, `eval/predictions-sam-v13.json`): precision 0.600,
recall 0.375, F1 0.462 (TP 3, FP 2, FN 5; 1 false alarm on 18 negative
scenes). Exact scene matches: 19/24. Opposite profile to vision: the
highest precision of any run, but recall drops — the SAM path misses the
flagship forklift path, the raised-hood welder, both ladder-carry
violations, and halves the facade-ladder call (helmet instead of ladder
work). Only 2 false positives in all 24 scenes.
Failure list: 5 misses (flagship path, welder hood, 2x ladder-carry,
facade ladder-work) vs 2 false flags (a vest call on the compliant crew,
a helmet call on the facade ladder).
Vest-flag investigation (evidence, no tuning): on the compliant-crew photo
SAM returns 4 person + 4 hard-hat + 4 safety-vest segments with vest boxes
overlapping the person boxes — and the photo shows all four workers in
hi-vis. The segments are correct; the reasoner minted "Worker without a
safety vest" anyway (likely the partially occluded worker behind netting).
Verdict: reasoning over-flag, NOT a SAM mislabel. Proposed general fix
(separate step, not applied): a missing-PPE finding should require a
person box with no overlapping PPE box; when every person overlaps a PPE
box, no missing-PPE finding.
Path switching verified live: auto mode uses SAM when enabled
(`segmentation_source: sam` on upload and live-camera finish); with SAM
unreachable (bogus model name forcing a 404) uploads fall back to vision
and live sessions pin vision (`segmentation_source: vision` both cases).

Shared failures (published, not tuned away):
- Over-eager observations: clean negatives almost always draw flags —
  mostly cautious "unable to verify X" wordings, but also genuine
  hallucinations (bare hands on gloved hands, a hanging mask on a masked
  textile worker, an uncapped-rebar call on a compliant crew photo).
- Compliant scenes rarely come back exactly empty; hedging plus findings
  at once inflates precision damage.

Takeaway for production: recall first is the right bias for safety, and
the v1.3 economy rule proved the verbosity was prompt-fixable on Wonder
(F1 0.173 → 0.560, same recall). Remaining work is model-side, not
prompt-side: the missed raised-hood welder and the grinding-close-up
flags need better visual grounding, not stricter wording.
Verdict stands: Spark for cheap dev loops (~7x cheaper per the Day-0 A/B),
Wonder for final reports (higher recall, richer actions); a Spark v1.3
re-run is still open and would test whether the economy rule lifts its
F1 0.218 the same way.
