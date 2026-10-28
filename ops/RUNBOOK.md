# Baseer production runbook (on-site Mac)

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
- Every case action is stamped `username (role)` in the audit log;
  the acting-as selector shows the signed-in identity.
- Back up nightly: `sh ops/backup.sh` (SQLite snapshot + evidence copies
  under `backups/`). Copy `backups/` off the machine weekly.

## After a restart / crash
- `launchctl` restarts the service automatically (`KeepAlive`). Reports,
  cases, users, and the audit log reload from `data/baseer.db`; in-flight
  live-camera sessions do not survive a restart (by design — re-start the
  session). Verify with `/health` and the mock suite:
  `cd backend && BASEER_MODE=mock ../.venv/bin/python mock_suite.py`.

## Key rotation / staff changes
- Deactivate a user: delete the row from `users` in `data/baseer.db`
  (tokens are stateless and expire after 12h, so removal takes effect on
  next sign-in at the latest).
- Rotate the Meta key: edit `.env`, `launchctl kickstart -k` the service.

## What is NOT production here
- Single on-site server, no TLS termination (serve behind the site VPN or
  a reverse proxy for remote access), backups are local copies.
- The fixed 24-scene eval set and mock fixtures are dev/test tools only
  and are never presented as live results (badges stay honest).
