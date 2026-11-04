"""Baseer demo seed — fill an ISOLATED data dir with a realistic mock-mode
history: four role accounts, inspections across three sites built from the
Pexels demo media in demo/, and corrective-action cases in every state.

    BASEER_DATA_DIR=/tmp/baseer-demo ../.venv/bin/python demo_seed.py

Refuses to run against the production data dir (repo data/) or without
BASEER_DATA_DIR. Everything runs through the real API in mock mode, so the
data is exactly what the app would produce; only created_at is backdated so
the trend and deadline views have shape. Reports stay labeled "Demo data".
"""
from __future__ import annotations

import io
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = os.environ.get("BASEER_DATA_DIR", "")
if not DATA or Path(DATA).resolve() == (REPO / "data").resolve():
    sys.exit("demo_seed: set BASEER_DATA_DIR to an empty scratch directory (never the production data/)")
if (Path(DATA) / "baseer.db").exists():
    sys.exit(f"demo_seed: {DATA} already has a database — use an empty directory")
os.environ["BASEER_MODE"] = "mock"
os.environ.setdefault("BASEER_ADMIN_PASSWORD", "demo-admin-2026")
sys.path.insert(0, str(HERE))

# Demo-only accounts (isolated demo data dir; never production credentials).
DEMO_USERS = [
    ("layla", "demo-layla-2026", "Safety Supervisor"),
    ("omar", "demo-omar-2026", "Site Manager"),
    ("nasser", "demo-nasser-2026", "Contractor"),
]

PHOTOS = REPO / "demo" / "photos"
FOOTAGE = REPO / "demo" / "footage"

# (days ago, site, media, inspector note)
INSPECTIONS = [
    (11, "factory", ["photos/person-grinder_12303734.jpg"], "جولة أسبوعية في ورشة التصنيع — منطقة الجلخ."),
    (9, "construction", ["photos/construction-workers-site_12314551.jpg", "photos/workers-rebar_32141074.jpg"],
     "Weekly walk on the tower block site, levels 3–4."),
    (8, "farm", ["footage/farm/tractor-spraying_36768458.mp4"], "فحص موسم الرش في البيوت المحمية."),
    (6, "factory", ["photos/welder-dark-room_27630177.jpg", "photos/worker-grinding-sparks_36003964.jpg"],
     "Welding bay follow-up after last week's findings."),
    (4, "construction", ["photos/man-ladder-roof_19769643.jpg", "photos/worker-climbing-ladder_38510725.jpg"],
     "عمل على السطح والسلالم — الواجهة الشرقية."),
    (2, "factory", ["photos/worker-glove-mask_3678228.jpg", "photos/cutoff-saw-sparks_1145434.jpg"],
     "Night shift spot check, cutting line."),
    (1, "construction", ["photos/welder-outdoors_36227261.jpg"], "لحام خارجي قرب منطقة التخزين."),
]


def shrink(path: Path) -> tuple[str, bytes]:
    """Photos are downsized (the pipeline caps frames at 1280px anyway)."""
    blob = path.read_bytes()
    if path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        from PIL import Image
        img = Image.open(io.BytesIO(blob)).convert("RGB")
        img.thumbnail((1600, 1600))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=86)
        blob = out.getvalue()
    return path.name, blob


def main() -> None:
    from fastapi.testclient import TestClient
    import app
    import store

    admin = TestClient(app.app)
    tok = admin.post("/auth/login", json={"username": "admin",
                                          "password": os.environ["BASEER_ADMIN_PASSWORD"]}).json()["token"]
    admin.headers["Authorization"] = f"Bearer {tok}"
    clients = {}
    for name, pw, role in DEMO_USERS:
        admin.post("/auth/users", json={"username": name, "password": pw, "role": role}).raise_for_status()
        c = TestClient(app.app)
        c.headers["Authorization"] = "Bearer " + c.post(
            "/auth/login", json={"username": name, "password": pw}).json()["token"]
        clients[name] = c
    layla, omar, nasser = clients["layla"], clients["omar"], clients["nasser"]

    now = datetime.now(timezone.utc)
    ids = []
    for days, site, media, note in INSPECTIONS:
        files = []
        for rel in media:
            p = REPO / "demo" / rel
            if p.exists():
                name, blob = shrink(p)
                files.append(("files", (name, blob, "video/mp4" if name.endswith(".mp4") else "image/jpeg")))
        r = layla.post("/inspections", files=files or None, data={"notes": note, "site_context": site})
        r.raise_for_status()
        rep = r.json()
        rep["created_at"] = (now - timedelta(days=days, hours=3)).isoformat()
        app.REPORTS[rep["inspection_id"]] = rep
        store.save_report(rep)
        ids.append(rep["inspection_id"])
        print(f"  {site:<13} {rep['inspection_id']}  {len(rep['findings'])} findings, {len(files)} files")

    def case(c, iid, i, **body):
        c.post(f"/inspections/{iid}/findings/{i}/case", json=body).raise_for_status()

    def note(c, iid, i, text):
        c.post(f"/inspections/{iid}/findings/{i}/case/notes", json={"text": text}).raise_for_status()

    # Oldest factory inspection: fully worked through and closed.
    for i in range(3):
        case(omar, ids[0], i, action="assign", assignee="Contractor — Al Noor Fabrication")
    note(nasser, ids[0], 0, "Helmets issued to the grinding crew; signed PPE register attached to the site file.")
    for i in (0, 1):
        case(layla, ids[0], i, action="verify")
        case(omar, ids[0], i, action="approve")
    case(layla, ids[0], 2, action="verify")  # forklift path: still not resolved
    note(layla, ids[0], 2, "Floor paint scheduled for Thursday night shift — re-inspect Friday.")
    # Construction: assigned, one closed, the rest overdue.
    case(omar, ids[1], 0, action="assign", assignee="Contractor — Gulf Scaffolding")
    case(omar, ids[1], 1, action="assign", assignee="Site Manager")
    case(layla, ids[1], 1, action="verify")
    case(omar, ids[1], 1, action="approve")
    note(omar, ids[1], 0, "Harness training booked for the whole scaffold crew on Sunday.")
    # Farm: in progress.
    case(omar, ids[2], 0, action="assign", assignee="Farm supervisor")
    note(nasser, ids[2], 0, "تم طلب كمامات بفلتر كيميائي — التسليم خلال يومين.")
    # Recent factory: one assigned.
    case(omar, ids[3], 0, action="assign", assignee="Safety Supervisor")

    # A finished live-camera session (mock frames from the demo photos).
    s = layla.post("/live/sessions", json={"site_context": "factory"}).json()["session_id"]
    for rel in ("photos/worker-grinding-sparks_36003964.jpg", "photos/person-grinder_12303734.jpg"):
        p = REPO / "demo" / rel
        if p.exists():
            name, blob = shrink(p)
            layla.post(f"/live/sessions/{s}/frames", files={"files": (name, blob, "image/jpeg")}).raise_for_status()
    fin = layla.post(f"/live/sessions/{s}/finish", json={"notes": "Live camera check, grinding line."}).json()
    print(f"  live-camera   {fin['inspection_id']}  {len(fin['findings'])} findings")
    print(f"\nSeeded {DATA}: {len(ids) + 1} inspections, {len(DEMO_USERS) + 1} users "
          f"(demo passwords are in {Path(__file__).name}).")


if __name__ == "__main__":
    main()
