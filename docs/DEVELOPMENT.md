# Developing Baseer (Veebase)

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp .env.example .env          # BASEER_MODE=mock needs no key
```

The production service owns port **8001** (launchd, `data/`). Never use
port **8000**, which belongs to another app. For development, run a second
instance on its own port with its own data directory.

## A dev server with realistic demo data

```bash
cd backend
export BASEER_DATA_DIR=/tmp/baseer-demo        # any EMPTY directory, never ../data
../.venv/bin/python demo_seed.py               # 8 inspections, 4 users, cases in every state
BASEER_MODE=mock ../.venv/bin/uvicorn app:app --port 8010 --reload
# open http://127.0.0.1:8010
```

`demo_seed.py` runs everything through the real API in mock mode, using
the Pexels media in `demo/`. It backdates `created_at` so the trend chart
and the deadlines have shape. It refuses to run against `data/` or a
directory that already has a database. The demo accounts and their
passwords are at the top of the script (demo data only).

## Tests

```bash
cd backend && ../.venv/bin/python mock_suite.py
```

The suite runs 90+ checks in an isolated temporary data directory: upload
and video inspections, the live loop, chat, the full case lifecycle,
history, the case list and SLA deadlines, the audit log, RBAC and user
editing, durability across restarts, the YOLO seam, and voice proxy
safety. Exit code 0 means green. Run it before every commit.

The live-model evaluation harness lives in `eval/` (see the README
section on the evaluation benchmark).

## Frontend conventions

- No build step: edit `frontend/index.html`, `app.css` and `app.js`, then
  reload.
- **New text**: add the key to both `S.ar` and `S.en` in `app.js`, then
  bind it with `data-i18n="key"` (or `data-i18n-ph` / `data-i18n-title`),
  or read it with `T().key` in rendering code.
- **New view**: add a `<section id="view-NAME" class="view hidden">`, a
  sidebar `<a href="#/NAME" data-nav="NAME">`, `NAME` in `VIEWS`, a
  loader in `renderRoute`, and entries in `pT` and `pS`.
- **Colors**: use the tokens (`--surface`, `--text`, `--high`, …). Never
  hard-code a color that has to work in both themes.
- **Direction**: use logical properties (`margin-inline-start`,
  `inset-inline-end`, `border-inline-start`) so RTL works without
  overrides.
- Escape all server text with `esc()` before inserting HTML.

## Backend conventions

- Every case mutation appends to `case.history` (`pipeline.log_case_action`)
  **and** writes `store.log_audit`, with the actor taken from the token.
- Mock outputs must never claim `segmentation_source: "sam"`.
- New aggregate views belong in `analytics.py` as pure functions over
  report dicts, so the suite can test them without HTTP.
- Keep reports schema-flexible: add fields, never rename them (stored
  JSON is reloaded as-is).

## Releasing to the on-site service

```bash
(cd backend && ../.venv/bin/python mock_suite.py)  # must be GREEN
sh ops/backup.sh                                    # snapshot before restarting
launchctl kickstart -k gui/$(id -u)/com.veebase.baseer
curl -s http://127.0.0.1:8001/health                # version should read 0.4.0
```

See `ops/RUNBOOK.md` for backups, TLS, YOLO and staff changes.

---
*Baseer is a Veebase product. © 2026 Veebase.*
