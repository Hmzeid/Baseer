"""Baseer mock-mode suite — run from backend/: ../.venv/bin/python mock_suite.py

Exercises the behavior this repo owns, without network or keys:
video + image inspections, the live-camera loop (frames -> alerts ->
finish -> report + cases), evidence chat, the case lifecycle including
approve-before-verify rejection, verify-with-evidence staging, the voice
fallback, and analytics merging live reports over the seed.

Exit 0 = green. Any failure prints the exact mismatch and exits 1.
"""
from __future__ import annotations

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["BASEER_MODE"] = "mock"
# Isolated runtime data: the suite must not touch the real ./data dir.
import tempfile as _tempfile
os.environ["BASEER_DATA_DIR"] = _tempfile.mkdtemp(prefix="baseer-suite-")
os.environ["BASEER_ADMIN_PASSWORD"] = "suite-admin-pw"

from PIL import Image  # noqa: E402


def solid_jpeg(color=(30, 90, 160)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), color).save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def solid_mp4(path: str, frames: int = 40) -> None:
    import cv2
    import numpy as np
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    for i in range(frames):
        frame = np.full((240, 320, 3), (200, 200, 190), np.uint8)
        cv2.rectangle(frame, (50 + i, 60), (110 + i, 180), (30, 90, 160), -1)
        vw.write(frame)
    vw.release()


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        raise SystemExit(f"mock suite FAILED at: {name} {detail}")


def main() -> int:
    from fastapi.testclient import TestClient
    import app

    anon = TestClient(app.app)
    r = anon.get("/analytics")
    check("auth required", r.status_code == 401, r.text[:120])
    r = anon.post("/auth/login",
                  json={"username": "admin", "password": "wrong"})
    check("login rejects bad password", r.status_code == 401, r.text[:120])
    r = anon.post("/auth/login",
                  json={"username": "admin", "password": "suite-admin-pw"})
    check("admin login", r.status_code == 200, r.text[:200])
    admin_tok = r.json()["token"]
    admin = TestClient(app.app,
                       headers={"Authorization": f"Bearer {admin_tok}"})
    r = admin.post("/auth/users",
                   json={"username": "layla", "password": "field-pw-1",
                         "role": "Safety Supervisor"})
    check("admin creates user", r.status_code == 200, r.text[:200])
    r = anon.post("/auth/login",
                  json={"username": "layla", "password": "field-pw-1"})
    check("user login + role", r.json().get("role") == "Safety Supervisor",
          r.text[:200])
    layla_tok = r.json()["token"]
    c = TestClient(app.app,
                   headers={"Authorization": f"Bearer {layla_tok}"})
    jpg = solid_jpeg()
    solid_mp4("/tmp/mock-suite-video.mp4")
    mp4 = open("/tmp/mock-suite-video.mp4", "rb").read()

    # 1. image inspection
    r = c.post("/inspections", files={"files": ("site.jpg", jpg, "image/jpeg")},
               data={"notes": "test", "site_context": "factory"})
    check("image inspection 200", r.status_code == 200, r.text[:200])
    rep = r.json()
    check("image findings+cases", len(rep["findings"]) == 3
          and all(f["case"]["status"] == "open" for f in rep["findings"]))
    check("mock source label", rep["segmentation_source"] == "mock", rep.get("segmentation_source"))
    iid = rep["inspection_id"]

    # 1b. video inspection (OpenCV sampling, max 8)
    r = c.post("/inspections", files={"files": ("walk.mp4", mp4, "video/mp4")},
               data={"notes": "test", "site_context": "factory"})
    check("video inspection 200", r.status_code == 200, r.text[:200])
    rep_v = r.json()
    check("video frames capped", 0 < rep_v["frames_processed"] <= 8, str(rep_v["frames_processed"]))
    check("video findings", len(rep_v["findings"]) == 3)

    # 2. live loop
    s = c.post("/live/sessions", json={"site_context": "factory"}).json()
    sid = s["session_id"]
    f1 = c.post(f"/live/sessions/{sid}/frames",
                files={"files": ("frame.jpg", jpg, "image/jpeg")}).json()
    check("live alerts fire", f1["frames_received"] == 1 and len(f1["new_alerts"]) == 2, str(f1))
    f2 = c.post(f"/live/sessions/{sid}/frames",
                files={"files": ("frame.jpg", jpg, "image/jpeg")}).json()
    check("live alerts dedupe", len(f2["new_alerts"]) == 0 and f2["alerts_total"] == 2, str(f2))
    fin = c.post(f"/live/sessions/{sid}/finish", json={"notes": "test"}).json()
    check("live finish report", fin["source"] == "live-camera" and len(fin["findings"]) == 3
          and fin["segmentation_source"] == "mock", str({k: fin.get(k) for k in ("source", "segmentation_source")}))

    # chat
    ch = c.post(f"/inspections/{iid}/chat",
                json={"question": "Why is finding 1 high?", "history": []}).json()
    check("evidence chat answers", bool(ch.get("answer")), str(ch)[:150])

    # 4. case lifecycle on finding 0 (mock staged: resolves)
    a = c.post(f"/inspections/{iid}/findings/0/case",
               json={"action": "assign", "assignee": "Safety Supervisor"})
    check("case assign", a.json()["case"]["status"] == "assigned", a.text[:150])
    v = c.post(f"/inspections/{iid}/findings/0/case", json={"action": "verify"})
    check("case verify suggests", v.json()["case"]["verification"]["suggested_resolved"] is True,
          str(v.json()["case"]["verification"])[:150])
    ap = c.post(f"/inspections/{iid}/findings/0/case", json={"action": "approve"})
    check("case approve closes", ap.json()["case"]["status"] == "closed", ap.text[:150])

    # approve-before-verify rejected on finding 2 (mock staged: not resolved)
    bad = c.post(f"/inspections/{iid}/findings/2/case", json={"action": "approve"})
    check("approve-before-verify rejected",
          bad.status_code == 400 and "verification" in bad.json()["detail"], bad.text[:150])

    # verify-with-evidence staging
    ve0 = c.post(f"/inspections/{iid}/findings/1/verify-evidence",
                 files={"files": ("after.jpg", jpg, "image/jpeg")}).json()
    check("verify-evidence resolves PPE",
          ve0["case"]["verification"]["suggested_resolved"] is True,
          str(ve0["case"]["verification"])[:150])
    ve2 = c.post(f"/inspections/{iid}/findings/2/verify-evidence",
                 files={"files": ("after.jpg", jpg, "image/jpeg")}).json()
    check("verify-evidence holds markings",
          ve2["case"]["verification"]["suggested_resolved"] is False,
          str(ve2["case"]["verification"])[:150])

    # 3. voice fallback (unconfigured upstream answers cleanly;
    # authed via ?token= since browsers cannot set WS headers)
    with c.websocket_connect(f"/voice/transcribe?token={layla_tok}") as ws:
        import json as _json
        msg = _json.loads(ws.receive_text())
    check("voice fallback frame", msg.get("type") == "error", str(msg)[:150])

    # 5. analytics merges live reports over seed
    an = c.get("/analytics").json()
    check("analytics merges", an["total_inspections"] == 3 + 3 and an["total_findings"] == 7 + 9,
          f"{an['total_inspections']} inspections, {an['total_findings']} findings")

    # 6. multi-site slicing + formal audit log (all suite posts use factory)
    sl = c.get("/sites").json()
    check("sites listed",
          any(s["site"] == "factory" and s["inspections"] == 2 + 3 for s in sl["sites"]),
          str(sl)[:150])
    anf = c.get("/analytics", params={"site": "factory"}).json()
    check("analytics site filter",
          anf["total_inspections"] == 2 + 3 and anf["total_findings"] == 4 + 9,
          f"{anf['total_inspections']} inspections, {anf['total_findings']} findings")
    au = c.get("/audit").json()
    check("audit log records",
          len(au["entries"]) >= 3 and all("actor" in e for e in au["entries"]),
          f"{len(au['entries'])} entries")
    csv = c.get("/audit", params={"format": "csv"})
    check("audit csv export",
          csv.status_code == 200 and csv.text.splitlines()[0].startswith("ts,"),
          csv.text[:80])

    # Arabic display labels must not collide: two distinct English
    # findings sharing one Arabic string renders as a duplicated row.
    import analytics as _analytics
    seen: dict[str, str] = {}
    for r in _analytics.SEED_REPORTS + [rep, rep_v, fin]:
        for f in r.get("findings", []):
            en, ar = f.get("title_en", ""), f.get("title_ar", "")
            if ar in seen and seen[ar] != en:
                check("arabic labels distinct", False,
                      f"{ar!r} labels both {seen[ar]!r} and {en!r}")
            seen[ar] = en
    check("arabic labels distinct", True)

    # 7. prompt v1.3: finding-economy rule present in BOTH reasoning
    # paths (severity rubric untouched — count only, never softer).
    import prompts as _prompts
    check("prompt economy rule",
          _prompts.PROMPT_VERSION == "1.3"
          and "FINDING ECONOMY" in _prompts.SYSTEM_PROMPT
          and "FINDING ECONOMY" in _prompts.VISION_SYSTEM_PROMPT
          and "empty findings array" in _prompts.VISION_SYSTEM_PROMPT,
          _prompts.PROMPT_VERSION)

    # 8. production durability: evidence on disk, audit stamped with the
    # signed-in identity, reports reloadable from SQLite after a restart.
    import store as _store
    ev_dir = os.path.join(os.environ["BASEER_DATA_DIR"], "evidence", iid)
    check("evidence stored",
          bool(rep.get("evidence_files"))
          and all(os.path.isfile(os.path.join(ev_dir, n))
                  for n in rep["evidence_files"]),
          ev_dir)
    au = c.get("/audit").json()
    check("audit stamped identity",
          any(e["actor"] == "layla (Safety Supervisor)" for e in au["entries"]),
          str([e["actor"] for e in au["entries"]])[:150])
    app.REPORTS.clear()
    app.REPORTS.update(_store.load_reports())
    check("restart reloads reports",
          iid in app.REPORTS
          and app.REPORTS[iid]["findings"][0]["case"]["status"] == "closed",
          f"{len(app.REPORTS)} reports reloaded")
    check("audit survives restart", len(_store.read_audit()) >= 3,
          f"{len(_store.read_audit())} entries")

    print(f"mock suite: GREEN ({an['total_inspections']} inspections, {an['total_findings']} findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
