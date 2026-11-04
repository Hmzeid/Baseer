"""Stage a LIVE-mode Baseer history for the Meta submission video.

Real Meta model calls (Muse vision path) on real demo media; only created_at
is moved back a few days so the trend/deadline views have shape.
Run from backend/:  BASEER_DATA_DIR=... python live_stage.py
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path("/Users/husseinabdelwahab/Ai/Baseer")
os.environ["BASEER_MODE"] = "live"
os.environ["BASEER_SEGMENTATION"] = "vision"
os.environ.setdefault("BASEER_ADMIN_PASSWORD", "demo-admin-2026")
sys.path.insert(0, str(REPO / "backend"))
assert os.environ.get("BASEER_DATA_DIR") and "scratchpad" in os.environ["BASEER_DATA_DIR"], "scratch data dir only"

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

import app  # noqa: E402
import store  # noqa: E402

USERS = [("layla", "demo-layla-2026", "Safety Supervisor"), ("omar", "demo-omar-2026", "Site Manager"),
         ("nasser", "demo-nasser-2026", "Contractor")]


def shrink(rel):
    p = REPO / "demo" / rel
    blob = p.read_bytes()
    if p.suffix.lower() == ".jpg":
        img = Image.open(io.BytesIO(blob)).convert("RGB")
        img.thumbnail((1600, 1600))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=86)
        blob = out.getvalue()
        return p.name, blob, "image/jpeg"
    return p.name, blob, "video/mp4"


def client(user, pw):
    c = TestClient(app.app)
    r = c.post("/auth/login", json={"username": user, "password": pw})
    r.raise_for_status()
    c.headers["Authorization"] = "Bearer " + r.json()["token"]
    return c


admin = client("admin", os.environ["BASEER_ADMIN_PASSWORD"])
for u, pw, role in USERS:
    if admin.post("/auth/users", json={"username": u, "password": pw, "role": role}).status_code not in (200, 400):
        raise SystemExit("user create failed")
layla, omar, nasser = (client(u, pw) for u, pw, _ in USERS)

HISTORY = [
    (9, "construction", "footage/construction/worker-scaffolding_32228166.mp4", "Scaffold lift, east elevation. Checking PPE at height."),
    (7, "factory", "photos/welder-outdoors_36227261.jpg", "Outdoor welding bay, afternoon shift."),
    (5, "construction", "photos/construction-workers-site_12314551.jpg", "Crew on the level-3 slab edge, routine check."),
    (3, "factory", "footage/factory/worker-helmet_5100046.mp4", "Machine hall walk-through."),
    (2, "farm", "footage/farm/tractor-spraying_36768458.mp4", "Spraying season check in the orchard rows."),
]
now = datetime.now(timezone.utc)
log = {}
for days, site, rel, note in HISTORY:
    name, blob, mime = shrink(rel)
    t0 = time.time()
    r = layla.post("/inspections", files=[("files", (name, blob, mime))], data={"notes": note, "site_context": site})
    if r.status_code != 200:
        print("FAILED", rel, r.status_code, r.text[:300]); continue
    rep = r.json()
    rep["created_at"] = (now - timedelta(days=days, hours=2)).isoformat()
    app.REPORTS[rep["inspection_id"]] = rep
    store.save_report(rep)
    log[rel] = rep["inspection_id"]
    print(f"{site:13} {rep['inspection_id']} {time.time()-t0:5.1f}s src={rep['segmentation_source']} ->",
          [(f["title_en"], f["severity"], f.get("determination")) for f in rep["findings"]])

# Case activity on the history (real verification call on one finding).
def case(c, iid, i, **body):
    r = c.post(f"/inspections/{iid}/findings/{i}/case", json=body)
    return r.status_code, r.json()

for rel, iid in log.items():
    rep = app.REPORTS[iid]
    for i, f in enumerate(rep["findings"]):
        if i == 0:
            case(omar, iid, i, action="assign", assignee="Contractor — Gulf Scaffolding" if "construction" in rep["site_context"] else "Site Manager")
            nasser.post(f"/inspections/{iid}/findings/{i}/case/notes", json={"text": "Crew briefed; corrective kit ordered."})

# Try a real after-photo verification on the factory helmet finding.
helmet_iid = log.get("footage/factory/worker-helmet_5100046.mp4")
if helmet_iid and app.REPORTS[helmet_iid]["findings"]:
    name, blob, mime = shrink("photos/construction-workers-site_12314551.jpg")
    t0 = time.time()
    r = layla.post(f"/inspections/{helmet_iid}/findings/0/verify-evidence", files=[("files", (name, blob, mime))])
    print("verify-evidence", r.status_code, f"{time.time()-t0:.1f}s", json.dumps((r.json().get("case") or {}).get("verification"), ensure_ascii=False)[:400])
json.dump(log, open(Path(os.environ["BASEER_DATA_DIR"]) / "stage_log.json", "w"), indent=1)
print("done")
