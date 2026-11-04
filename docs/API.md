# Baseer by Veebase — API Reference

FastAPI service (`backend/app.py`), version **0.4.0**. Interactive OpenAPI
docs are served at `/docs` on any running instance.

## Authentication

`POST /auth/login` returns a bearer token, valid for 12 hours. Send it on
every other request:

```
Authorization: Bearer <token>
```

Public routes: `GET /health`, `GET /`, `/static/*`, `POST /auth/login`.
The voice WebSocket takes the token as `?token=` because browsers cannot
set WebSocket headers.

Errors are JSON `{"detail": "..."}` with these status codes:
`400` invalid input, `401` missing or expired token, `403` admin only,
`404` not found, `413` upload over 150 MB, `429` sign-in throttled,
`503` model provider throttled mid-analysis (retry).

---

## System

### `GET /health`
```json
{"status": "ok", "mode": "mock", "version": "0.4.0",
 "segmentation": "auto", "sla_days": {"high": 1, "medium": 7, "low": 30},
 "product": "Baseer by Veebase", "briefing_languages": {"ur": {"name": "Urdu", "native": "اردو", "rtl": true}, …}}
```

## Inspections

### `POST /inspections` — run an inspection
`multipart/form-data`: `files` (0..n images or videos), `notes` (≤ 5000
characters), `site_context`. Returns the full report:

```json
{
  "inspection_id": "4fad6470e52b",
  "created_at": "2026-11-03T20:05:12+00:00",
  "mode": "mock | live",
  "frames_processed": 2,
  "segmentation_source": "mock | sam | vision",
  "site_context": "construction",
  "summary_ar": "…", "summary_en": "…",
  "segments": [ {"label": "...", "label_ar": "...", "confidence": 0.9, "frame_index": 0, "bbox": [x, y, w, h]} ],
  "findings": [ {
      "title_ar": "…", "title_en": "…", "severity": "high | medium | low",
      "detail_ar": "…", "detail_en": "…", "action_ar": "…", "action_en": "…",
      "frame_index": 0, "source": "segments | inspector | both | vision",
      "visually_confirmed": true, "determination": "confirmed | uncertain",
      "case": {"status": "open", "assignee": "", "verification": null, "history": [], "notes": []}
  } ],
  "evidence_files": ["00-site.jpg", "01-roof.jpg"]
}
```
Live-camera reports also carry `"source": "live-camera"` and `live_alerts`.

### `GET /inspections` — history
Query: `q` (matches ID, site, summaries and finding titles), `site`,
`severity` (`high|medium|low`: inspections having at least one), and
`format=csv`. Newest first. Each row:

```json
{"inspection_id": "…", "created_at": "…", "site": "factory", "source": "upload",
 "mode": "mock", "segmentation_source": "mock", "frames_processed": 2,
 "findings": 3, "high": 2, "medium": 1, "low": 0,
 "open_cases": 2, "closed_cases": 1, "evidence_files": 2,
 "summary_en": "…", "summary_ar": "…", "top_finding_en": "…", "top_finding_ar": "…"}
```

### `GET /inspections/{id}`
The full stored report (same shape as the `POST` response).

### `GET /inspections/{id}/report.pdf`
A structured Arabic (RTL) PDF: cover, summary, findings, cases with
history and notes, an audit excerpt, and an evidence appendix (up to 6
images).

### `GET /inspections/{id}/evidence/{filename}`
The original upload bytes. Filenames come from `evidence_files`.

### `POST /inspections/{id}/chat` — evidence chat
`{"question": "…", "history": [{"role": "user|assistant", "content": "…"}]}`
→ `{"answer": "…"}`. The question must be 1–2000 characters. Answers are
grounded in the report only.

### `POST /inspections/{id}/briefing` — crew briefing
`{"language": "ur", "refresh": false}`. Languages: `ar en ur hi bn ne tl ml` (also
listed with native names and text direction in `/health` → `briefing_languages`).
Returns `{language, name, native, rtl, text, generated_at, actor, cached}`. Cached per
language on the report under `briefings`; `refresh: true` regenerates. `400` for an
unknown language or a report with no findings, `503` if the model provider throttles.

### Segments
SAM-path reports carry `segments: [{label, label_ar, confidence, frame_index, bbox}]`
with `bbox` normalized `[x, y, w, h]` on the extracted frame. The console and the PDF
draw them only when `segmentation_source == "sam"`.

## Corrective-action cases

### `POST /inspections/{id}/findings/{index}/case`
`{"action": "assign", "assignee": "Contractor — Gulf Scaffolding"}`,
`{"action": "verify"}` or `{"action": "approve"}`. Returns the updated
finding. `approve` returns `400` unless the latest verification has
`suggested_resolved: true`. Closed cases reject every action. The actor is
always the signed-in user, never a client-supplied value.

### `POST /inspections/{id}/findings/{index}/verify-evidence`
`multipart/form-data` `files` (after photo or video). The vision
comparison sets `case.verification = {suggested_resolved, note, note_ar, note_en}`.

### `POST /inspections/{id}/findings/{index}/case/notes`
`{"text": "…"}` (1–2000 characters). Append-only, and audited.

### `GET /cases` — all cases
Query: `status` (`open|assigned|closed|overdue`), `site`, `format=csv`.
Active cases come first, overdue ones at the top, then by severity and
deadline. Closed cases come last.

```json
{"inspection_id": "…", "finding_index": 0, "site": "factory",
 "title_en": "…", "title_ar": "…", "severity": "high", "status": "assigned",
 "assignee": "…", "created_at": "…", "age_days": 3,
 "due_at": "2026-11-04T20:05:12+00:00", "overdue": true,
 "suggested_resolved": false, "notes": 1, "last_action": {"ts": "…", "action": "assign", "actor": "omar (Site Manager)", "detail": "…"}}
```

Deadline = inspection time + `SLA_DAYS[severity]` (high 1 day, medium 7,
low 30). It is computed on read, so older reports get deadlines too.

## Live camera

| Method & path | Body | Returns |
|---|---|---|
| `POST /live/sessions` | `{"site_context": "factory"}` | `{"session_id", "status": "live"}` |
| `GET /live/sessions` | – | open sessions, including ones restored after a restart |
| `POST /live/sessions/{sid}/frames` | multipart `files` | `{frames_received, segments_total, new_alerts[], alerts_total}` |
| `POST /live/sessions/{sid}/finish` | `{"notes": "…"}` | full report (`source: "live-camera"`) |
| `GET /live/yolo-status` | – | local YOLO watcher status (`configured`, `weights`, `classes`, …) |

Each alert type fires once per session. On finish, the session's frames
move under the new inspection ID, so the evidence and PDF endpoints serve
them.

## Analytics & records

### `GET /analytics?site=`
`total_inspections`, `total_findings`, `by_severity`, `top_hazards` (5),
`recent` (6, newest first, `seed` flag), `trend` (zero-filled daily
series, last 30 days), `open_cases` (20, with `due_at` and `overdue`),
`cases` (`total, open, assigned, closed, overdue, closure_rate`), and
`demo_seed_included`.

### `GET /sites`
`{"sites": [{"site": "factory", "inspections": 5}, …]}`, derived from
real site contexts (an empty context counts as `general`).

### `GET /audit`
Query: `inspection_id`, `format=csv`. Append-only entries, newest first:
`{ts, inspection_id, site, finding_index, finding, action, actor, detail}`.

## Accounts

| Method & path | Access | Body |
|---|---|---|
| `POST /auth/login` | public | `{"username", "password"}` → `{"token", "username", "role"}` |
| `GET /auth/me` | user | → `{"username", "role"}` |
| `POST /auth/password` | user | `{"old_password", "new_password"}` (≥ 8) |
| `GET /auth/users` | admin | → `{"users": [{username, role, created_at}]}` |
| `POST /auth/users` | admin | `{"username", "password", "role"}` |
| `PATCH /auth/users/{username}` | admin | `{"role"?, "password"?}`; you cannot drop your own Admin role |
| `DELETE /auth/users/{username}` | admin | you cannot delete yourself |

Roles: `Safety Supervisor`, `Site Manager`, `Contractor`, `Admin`.

## Voice

`WS /voice/transcribe?token=…` — send microphone audio chunks (binary)
and receive JSON text frames `{"type": "partial|final|error", …}`. The
Meta key is attached server-side and never reaches the browser. Without
`META_TRANSCRIBE_WS_URL` the socket sends one `error` frame and closes.

---
*Baseer is a Veebase product. © 2026 Veebase.*
