# Baseer by Veebase — production runbook (on-site Mac)

## First boot
1. `cd ~/Ai/Baseer && git pull`
2. Copy env: `cp .env.example .env` — fill `MODEL_API_KEY` (never commit it).
3. Set the admin password: `export BASEER_ADMIN_PASSWORD='<strong secret>'`
   (or put it in the launchd plist before loading; first boot creates the
   `admin` user and prints the password once into the server log).
4. Install the service: `cp ops/com.veebase.baseer.plist
   ~/Library/LaunchAgents/` then
   `launchctl load ~/Library/LaunchAgents/com.veebase.baseer.plist`
5. Open `http://127.0.0.1:8001`, sign in as `admin`, create inspector
   accounts (Safety Supervisor / Site Manager / Contractor). Never use
   port 8000 — it belongs to another app.

## Daily operation
- Console: `http://127.0.0.1:8001` (mock data) — for live inspections run
  the same service with `BASEER_MODE=live` (edit the plist, reload).
- Every case action is stamped `username (role)` in the audit log
  (the signed-in identity, shown in the sidebar user chip).
- Overdue corrective actions (high 1 day, medium 7, low 30 after the
  inspection) appear on the Overview and in Cases → Overdue.
- Back up nightly: `sh ops/backup.sh` (SQLite snapshot + evidence copies
  under `backups/`). Copy `backups/` off the machine weekly.

## After a restart / crash
- `launchctl` restarts the service automatically (`KeepAlive`). Reports,
  cases, users, the audit log, and interrupted live-camera sessions reload
  from `data/baseer.db` (frames rebuild from `data/evidence/`); keep the
  browser's Live view open and keep sending frames to the same session.
  Verify with `/health` and the mock suite:
  `cd backend && BASEER_MODE=mock ../.venv/bin/python mock_suite.py`.

## Key rotation / staff changes
- Add, re-role, reset the password of, or delete a user from the
  console's **Users** page (Admin). Tokens are stateless and expire after
  12h, so a deletion takes effect at the next sign-in at the latest; a
  role change applies to the very next request.
- Rotate the Meta key: edit `.env`, `launchctl kickstart -k` the service.

## YOLO stream watcher (real-life camera path)
- In production the live stream goes to a local YOLO PPE model: it fires
  live alerts on the spot (fast, works offline, no per-frame API cost).
  The Meta API still writes the final grounded report at session finish.
- Install once: `../.venv/bin/pip install -r backend/requirements-yolo.txt`
  (torch + ultralytics, ~2 GB; Apple Silicon uses MPS automatically).
- Place the trained weights at `data/yolo/best.pt` (git-ignored, like the
  DB) and set `BASEER_YOLO_WEIGHTS=/Users/husseinabdelwahab/Ai/Baseer/data/yolo/best.pt`
  in the launchd plist (or export it), then reload the service.
- Tune: `BASEER_YOLO_CONF` (default 0.5). If your model's class names
  differ, map them with `BASEER_YOLO_MAP` JSON, e.g.
  `{"no_helmet": ["Worker without a safety helmet", "عامل بدون خوذة حماية", "high"]}`.
- Verify: sign in, open `GET /live/yolo-status` — `configured` must be
  true and list the model's classes. Without weights (or without torch)
  the server logs nothing and keeps the SAM/vision path, so a missing
  model file can never break the camera.
- YOLO alerts carry `"source": "yolo"`; severities on live alerts are
  preliminary — the finished report is authoritative.

## LAN HTTPS (optional)
- `sh ops/tls.sh [hostname]` mints a self-signed cert into `data/tls/`;
  launch uvicorn with `--ssl-certfile/--ssl-keyfile` (command is printed
  by the script). Expect a one-time browser trust warning; for access
  outside the site LAN prefer the site VPN.

## What is NOT production here
- Single on-site server, backups are local copies (copy `backups/`
  off the machine weekly).
- The fixed 24-scene eval set and mock fixtures are dev/test tools only
  and are never presented as live results (badges stay honest).

---
*Baseer is a Veebase product. © 2026 Veebase.*
