# Baseer — Build Plan
Meta Global AI Developer Hackathon · Startup track · Theme: Build for Your World
Event: Mon Oct 26, 12:00 PM – Wed Nov 4, 9:00 PM CT (remote) · Submission due Nov 4, 9:00 PM ET via Cerebral Valley portal
Status: APPROVED (Oct 21). Prep scaffold complete Oct 21 — pipeline runs end-to-end in mock mode. BILINGUAL (Hussein's direction, Oct 21): the app is fully dual-language EN/AR — UI toggle with full RTL flip in the frontend, and every report field (title, detail, action, summary) exists in both languages. Reasoning prompt DRAFT v1 lives in backend/prompts.py (grounding rules, severity rubric, bilingual output schema, few-shot example) — to be refined with Hussein before kickoff. UI design mockup delivered Oct 21 (Baseer_UI_Mockup_2026-10-21.html): home / capture / analysis / report screens with the language switch working.

## Product (as submitted in the application)
Inspector uploads a short phone video or photo set → SAM 3.1 segments equipment,
workers, PPE, vehicles, visible hazards → Muse Spark reasons over segments +
the inspector's Arabic voice/text notes → structured report in Arabic (English
summary): each finding with severity, the exact frame as evidence, and a
recommended corrective action.

## Architecture (already scaffolded in this repo)
- `backend/app.py` — FastAPI: POST /inspections (multipart), GET /health, serves UI
- `backend/pipeline.py` — ingest → frame extraction (images pass through; video
  sampled via OpenCV, max 8 frames) → segmentation → reasoning → report
- `backend/meta_client.py` — the ONLY file that knows the Meta Model API
  contract. Modes: mock (default) / live (env-driven). Swap point for Day 0.
- `frontend/index.html` — Arabic RTL report viewer + upload form (light theme)

## API contract (verified 2026-10-21 — waiver/event page official; API details
## consistent across many sources quoting Meta's docs; re-confirm on
## developer.meta.com/docs/model-api in a normal browser)
- Base URL `https://api.meta.ai/v1`, OpenAI-compatible; key = `MODEL_API_KEY`
  from dev.meta.ai (per-team, `LLM_` prefix). **Self-serve today — no need to
  wait for Oct 26.** Standard Muse Spark 1.3 = $1.25/M in, $4.25/M out;
  SAM 3.1 = $2.50/1K images, $0.20/1K video frames. Prep spend is negligible.
- Muse Spark 1.3: multimodal (image/video/PDF), ~1M context. **Standard tier
  only — Contributor variants let Meta train on prompts. Hard rule.**
- SAM 3.1: text prompts ONLY on the hosted API, one English concept phrase
  per call; output = special-token text (boxes + base85 masks + stable object
  IDs across video); video ≤15,000 frames, ≤16 objects/frame, MP4/MOV H.264
  (no WebM). **Per-team gated: 404 if not enabled — check before kickoff.**
- $150 participant credits: confirmed in the official waiver, but NO
  redemption mechanism is published yet — expect it via Cerebral Valley/email
  at kickoff. Don't block on it; PAYG prep costs cents.
- Muse Voice Transcribe is realtime-WebSocket ONLY (no batch endpoint) —
  voice notes pivot below (Oct 29).

## Day 0 — before/at kickoff (Oct 26)
- [x] **API key strategy (Hussein's decision, Oct 21): WAIT for the
      event-provided key + $150 credits as the primary path.** DONE Oct 26:
      credits claimed, key in Muse Code on Hussein's Mac, and the same key
      value in `Ai/Baseer/.env` (git-ignored) for the app. The WAIT decision
      is closed; no self-serve fallback was needed.
- [x] **On key arrival (whichever source):** run one live SAM 3.1 call to
      confirm the team isn't 404-gated; run the Arabic A/B test — same
      inspection through Muse Spark 1.3 AND Muse Wonder 1.0 (the API's top
      tier; "Wonder Full" is a Muse Code subscription exclusive, not an API
      model) — pick the reasoning model for final reports empirically.
      Hybrid default: Spark for dev/testing, Wonder for final report
      generation. VERDICTS Oct 26 (run via `backend/day0_check.py`):
  - **SAM 3.1: GATED — 404 model_not_found, not enabled for this team/key.**
    The live segmentation path in `meta_client.py` will 404 until SAM is
    enabled. This is a verdict, not a failure. Decision: (a) build the
    Muse-multimodal-vision fallback NOW so the Oct 26–27 live pipeline
    validates regardless of enablement; (b) request SAM enablement in
    parallel via the event Discord office-hours channel (draft in the
    Day-0 memo below); if SAM is enabled mid-week, the segmentation
    source swaps inside `meta_client.py` only.
  - **Arabic A/B: hybrid CONFIRMED.** Same note in, both models returned
    3 findings (2 high, 1 medium), right order, grounded, no invented
    standards. Spark 1.3: 3,036 out tokens, $0.016/report, concise MSA,
    bare-imperative actions. Wonder 1.0: 5,027 out tokens, $0.109/report,
    formal wordier MSA, actions name the actor (supervisor, maintenance,
    safety officer — marginally better). Locked: Spark for dev loops,
    Wonder for final reports. Both trivially cheap without SAM in the mix
    (reasoning-only costs; SAM's $2.50/1K images would have dominated).
- [ ] Accept the Official Rules on the event page when published (participant action)
- [ ] Claim the $150 credits when the mechanism appears (watch CV portal/email)
- [ ] Join the event Discord; note office-hours schedule (Oct 27 – Nov 4)
- [ ] **Rotate the dev.meta.ai key after submission (Nov 4):** the key
      passed through Warp agent chat history during setup. Rotation is
      free and does not affect the $150 credits (credits live on the
      account, not the key).

## Scope (Hussein's decision, 2026-10-21)
CORE = the inspection: capture → report in ~30 seconds. Everything else is a
layer AFTER the report exists, never a step before it.
- **Layer 1 — Evidence chat (IN):** ask Baseer about a completed inspection
  ("why is finding 1 high?", "draft the contractor notice") — grounded in the
  report's findings/frames only, AR/EN. Backend + UI already implemented in
  mock mode (POST /inspections/{id}/chat, prompts.CHAT_SYSTEM_PROMPT).
- **Layer 2 — Analytics (IN, light):** the safety manager's view over report
  history: totals, severity mix, top hazards, recent activity. Backend + UI
  implemented in mock mode (GET /analytics; demo seed clearly labeled).
  Full version (site comparisons, contractor scorecards) = post-event.
- **Layer 3 — Integrations (FEATURE PLAN / stretch only):** if ahead of
  schedule: WhatsApp + PDF share on the report. Roadmap (post-event, hooks
  designed now): VeeSign sign-off, VeeArchive sealed storage, CMMS/ERP
  connectors, Baseer REST API + webhooks, offline capture with sync.
- **Input modes (Hussein, 2026-10-21): TWO.**
  1. *Upload inspection (built)* — photo/video in → the inspection starts
     immediately → report in ~30 seconds.
  2. *Live camera (session core IMPLEMENTED in mock mode Oct 21 —
     backend/live.py + REST endpoints + UI panel)* — a camera connected to
     the system (USB / phone / IP) streams frames; Baseer samples and
     segments them as they arrive, raises an alert the moment a violation
     first appears (once per violation type), and finishing the session
     produces the full report + cases through the same pipeline. "Real-time"
     = sampled near-real-time analysis (a frame every few seconds) — how
     production PPE monitoring actually works; never market it as
     frame-by-frame. Event-window work: getUserMedia / RTSP wiring (Oct 28).
- **Use cases (positioning): factory (FLAGSHIP demo), construction/building,
  farms.** One deep factory story for the demo; the other two are real use
  cases with backup footage, not parallel builds.
- **Footage sources:** staged at a real site; public/openly-licensed clips
  from the internet (log source + license in demo/SOURCES.md); or a live
  camera in the room. AI-generated imagery is illustrative fiction and is
  NEVER submission material (Hussein confirmed Oct 21).

## Evaluation benchmark (adopted 2026-10-21 — the submission's proof, not its promise)
A small labeled test set, built from the SAME staged/public footage as the
demo (sources logged in demo/SOURCES.md): ~24 scenes across the flagship
factory scenario + construction/farm backups, deliberately including edge
cases — poor lighting, a partially visible helmet, a hazard the inspector's
note contradicts, and scenes where the correct answer is "unable to
determine". Scorer lives at `eval/score.py` (built Oct 21): per-hazard
precision / recall / F1 from segment labels, plus end-to-end latency per
inspection and a human spot-check of Arabic report quality. Prep the set
Oct 30–31 alongside the footage shoot; run it Nov 2. **The results —
including the failures — go into the submission README.** Judges score
production readiness; a team that publishes its own failure modes reads as
one that has actually run its system. Never tune the set to flatter the
numbers: the set is fixed before the runs start.

## Build days
- **Oct 26–27 — Live pipeline:** SAM 3.1 live segmentation on stills; Muse Spark
  live findings in Arabic; evidence frame rendering with bbox overlays.
- **Oct 28 — Video path + live camera wiring:** frame sampling tuned
  (scene-change + interval), segment tracking across frames, dedupe findings
  across frames. Wire the live-session core (built Oct 21) to a real camera:
  getUserMedia snapshot loop first (a frame every ~3s), RTSP grabber if time.
  Rehearse the in-room live beat for the demo video: person walks into frame
  without a helmet → alert fires → same person returns wearing it → finish
  session → report with the case already open.
- **Oct 29 — Voice notes + evidence chat live:** no batch transcription on the
  Meta API (realtime WebSocket only) → live-mic streaming spike or typed
  notes fallback; wire the chat layer to the live model (it is context-only
  work — the report pipeline is untouched).
- **Oct 30 — Act + Verify loop, analytics live, report polish:** findings open
  corrective-action cases (assign to supervisor); re-inspection comparison
  suggests resolution and a human approves closure; analytics over real
  inspection history; severity model, corrective-action quality pass,
  printable report (Arabic typesetting via browser print), English summary.
  (Case lifecycle endpoints + UI already implemented in mock mode Oct 21;
  the live segment comparison is this day's work.)
- **Oct 31 — Buffer / hardening:** error states, large-file handling, latency.
  Stretch if ahead: WhatsApp/PDF share buttons (Layer 3).
- **Nov 1 — Demo assets:** stage and shoot the demo inspections (see demo/),
  record the demo video (problem → upload → report, under 3 minutes).
- **Nov 2 — Dry-run submission + benchmark:** full portal submission drafted
  end-to-end; run the evaluation set (see above) and write the results —
  successes AND failures — into the README and portal description.
- **Nov 3 — Fix + rehearse:** judging-criteria pass (technical execution,
  production-readiness), README, repo cleanup.
- **Nov 4 — Submit early** (target: before noon CT; deadline 9:00 PM ET).

## Flagship demo scenario (adopted 2026-10-21 — one deep scenario, not three shallow ones)
Positioning line: **"Baseer — the AI that sees, understands, and acts. In Arabic."**
Portal pitch (one problem, not three industries): "Millions of industrial
inspections depend on manual observations, fragmented reports, and delayed
corrective actions. Baseer turns a short site video — or a live camera
feed — and an Arabic voice note into an evidence-grounded safety
inspection, then tracks corrective actions until a human verifies the
resolution."
The demo tells ONE story end-to-end, industrial workplace safety:
1. **Observe** — the inspector's phone clip: a worker at a machine without a
   helmet, a forklift crossing behind him.
2. **Understand** — SAM 3.1 segments worker / missing PPE / forklift;
   Muse Spark/Wonder reasons over segments + the Arabic voice note.
3. **Explain** — the Arabic report: finding, severity, evidence frame,
   corrective action (English mirror throughout).
4. **Act** — the high finding automatically opens a corrective-action CASE,
   assigned to the safety supervisor; the evidence chat drafts the notice.
5. **Verify** — a second short clip of the same spot: the worker now wears
   the helmet. Baseer suggests the case is resolved; a HUMAN approves the
   closure. (No autonomous safety decisions — the human closes cases.)
6. **Learn** — the analytics view: this hazard has now recurred 3 times
   this month across inspections.
Backup footage (only if the flagship shoot fails): construction edge
(missing guard rail), farm (irrigation PPE). Staged or public footage ONLY —
no customer data, no Veebase production IP, and no AI-generated imagery
presented as real footage. Shoot on a phone; clips 10–20s; the flagship
needs a matched BEFORE/AFTER pair of the same scene.

## Submission checklist (Cerebral Valley portal)
- [ ] Working demo (hosted URL or runnable repo + clear run instructions)
- [ ] Demo video (<3 min): problem → upload → live report generation
- [ ] Public repo with README (problem, how it uses SAM 3.1 + Muse Spark,
      architecture diagram, run steps) — license: pick at submission (MIT
      recommended for a demo repo; Hussein's call)
- [ ] Project description matching the approved application text
- [ ] Confirm no confidential material anywhere in repo/video

## Risks & mitigations
- Meta Model API access may open only at kickoff → mock-mode scaffold means
  UI/report work is never blocked; live swap is one file.
- SAM 3.1 contract differs from assumptions → all shaping isolated in
  `meta_client.py`; Day 0 verification memo pins the real contract first.
- Arabic output quality from Muse Spark unproven → prompt + JSON schema are
  strict; keep a post-format validator; test with real Arabic notes early.
- Solo schedule vs deal work → scope is deliberately narrow (one pipeline,
  three demo scenes); Nov 1 assets deadline protects the submission date.
