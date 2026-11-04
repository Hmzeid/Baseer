# Baseer by Veebase — Architecture

## System at a glance

```
 Browser (frontend/: index.html + app.css + app.js, no build step)
   │  hash-routed SPA · bilingual AR/EN · light/dark · bearer token in localStorage
   ▼
 FastAPI (backend/app.py) ── auth.py (PBKDF2 users, HMAC tokens)
   │
   ├── pipeline.py ── extract_frames (images → JPEG, video → ≤8 sampled frames, OpenCV)
   │       │
   │       └── meta_client.py ── mock | live
   │              ├── segment_frames   SAM 3.1 via /v1/responses (one concept per call)
   │              ├── reason_findings  Muse over SAM segments + notes
   │              ├── reason_from_frames  Muse multimodal vision (fallback / vision mode)
   │              ├── verify_finding / compare_for_verification (re-inspection)
   │              └── chat_with_inspection (grounded evidence chat)
   ├── live.py ── camera sessions: per-frame alerts, finish → same reasoning path
   │       └── yolo.py (optional local PPE detector for live alerts)
   ├── analytics.py ── dashboard aggregation, SLA deadlines, history rows, case list
   ├── report_pdf.py ── server-rendered Arabic PDF (reportlab + arabic-reshaper + bidi)
   ├── voice.py ── WebSocket proxy to the Meta realtime transcription endpoint
   └── store.py ── SQLite (WAL): inspections, audit, live_sessions, users
                     data/evidence/<inspection_id>/ originals on disk
```

## The inspection loop

1. **Observe**: uploads (`POST /inspections`) or live frames
   (`POST /live/sessions/{sid}/frames`).
2. **Understand**: `BASEER_SEGMENTATION=auto` tries SAM 3.1 and falls back
   to Muse vision on a 404. `sam` never falls back, and `vision` skips SAM.
   The report records `segmentation_source` so nobody mistakes a vision
   report for a segmented one. Mock mode always records `mock`.
3. **Explain**: Muse writes bilingual findings (severity, detail,
   corrective action, evidence frame, source, determination) and a
   summary. The prompts live in `prompts.py` (v1.3, including the
   "finding economy" rule).
4. **Act**: `pipeline.with_cases` opens a case on every finding.
5. **Verify**: a plain AI verification, or a vision comparison against
   *after* evidence. Either one only ever *suggests* resolution.
6. **Close**: `approve` requires a suggested-resolved verification and a
   signed-in human. Every step appends to `case.history` and to the
   durable audit table.

## Segment overlays and crew briefings

- **Overlays**: `report.segments` (SAM path) hold normalized boxes per extracted frame.
  The console maps a frame to an evidence image by upload order (images before the first
  video map one-to-one) and draws an absolutely positioned layer over the image;
  `report_pdf.annotate_frame` draws the same boxes with PIL for the PDF appendix. Only
  `segmentation_source == "sam"` is drawn.
- **Crew briefing**: `meta_client.crew_briefing` sends the report context with
  `prompts.BRIEFING_SYSTEM_PROMPT` (one language, findings only, ~1 minute read-aloud) to
  Muse; results are cached on the report under `briefings[lang]`. Mock mode builds a
  briefing from the report's own bilingual text and labels non-Arabic/English output as
  demo instead of faking a translation.

## Data model

Reports are stored as JSON documents (`inspections.data`), so the schema
can evolve without migrations. Key nested objects:

- `finding.case = {status, assignee, verification, history[], notes[]}`.
  `history` and `notes` are append-only.
- `audit` table: one row per case action, never updated or deleted. It
  backs `/audit`, the CSV export and the PDF audit excerpt.
- `live_sessions`: a snapshot of every open session (segments, alerts,
  the decided segmentation path). Frame bytes are rebuilt from evidence
  files when the server boots.

`app.REPORTS` is a write-through, in-memory cache over SQLite. Every
mutation calls `store.save_report`.

### Derived, never stored

- **Deadlines and overdue status**: `analytics.case_deadline` computes
  `created_at + SLA_DAYS[severity]` (`high` 1 day, `medium` 7, `low` 30)
  on every read. Changing `SLA_DAYS` re-dates every case without a
  migration. The frontend reads the table from `/health`.
- **Sites**: the distinct `site_context` values (blank becomes `general`).
- **History rows and the case list**: `analytics.summarize` and
  `analytics.list_cases`.

## Security model

- Passwords: PBKDF2-HMAC-SHA256, 210k iterations, per-user salt.
- Tokens: stateless `base64(username:expiry:HMAC)`, 12-hour lifetime,
  signed with `data/.secret` (mode 0600, created on first boot).
- Every route except health, static files and login requires a token.
  User management requires Admin. Audit identity always comes from the
  token, never from the request body.
- Sign-in throttle: 6 failures per username per 5 minutes returns `429`.
- Input guards: 150 MB per request, notes ≤ 5000 characters,
  chat questions and case notes ≤ 2000.
- Evidence paths are sanitized to `[A-Za-z0-9._-]`.
- The first admin's password comes from `BASEER_ADMIN_PASSWORD`. The
  placeholder value is rejected, and a random one-time password is
  printed to the log instead.
- The Meta API key stays server-side. The voice proxy attaches it
  upstream and never echoes it.

## Frontend

`frontend/index.html` holds the markup for every view.
`frontend/app.css` is the design system: tokens on `:root` and
`[data-theme="dark"]`, and logical CSS properties so RTL and LTR mirror
without separate stylesheets. `frontend/app.js` holds the logic:

- **Router**: `#/overview`, `#/inspect`, `#/live`, `#/inspections`,
  `#/report/<id>?f=<finding>`, `#/cases?status=`, `#/audit`, `#/users`,
  `#/account`. Deep links work after a reload, and Copy link uses them.
- **i18n**: the `S.ar` and `S.en` dictionaries. Static text is bound with
  `data-i18n`, `data-i18n-ph` (placeholders) and `data-i18n-title`.
  Dynamic text goes through `T()`. Arabic uses Western digits
  (`ar-u-nu-latn`) for consistent numbers.
- **`api()`**: adds the bearer token, parses `{detail}` errors, and logs
  out only on a 401 from an authenticated route. A wrong current password
  or a network blip never ends the session.
- **Evidence**: a fresh upload shows the browser's own object URLs.
  Reopened reports fetch evidence with the token and cache it as blob
  URLs. Videos load only on demand.
- **Icons**: inline SVG paths in `ICONS`, rendered into `<i data-icon>`.

## Modes

| `BASEER_MODE` | Behavior |
|---|---|
| `mock` (default) | Deterministic fixtures, keyed by site (factory, construction, farm). No network, no key. Reports are badged **Demo data**. |
| `live` | Real Meta Model API calls (`MODEL_API_KEY`, `MUSE_MODEL`, `SAM_MODEL`). Retries with backoff on 429/5xx. |

---
*Baseer is a Veebase product. © 2026 Veebase.*
