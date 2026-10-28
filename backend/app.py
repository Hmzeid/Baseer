"""Baseer API — FastAPI surface.

Core: POST /inspections (the ~30-second inspection).
Layers (Hussein's decision, 2026-10-21): evidence chat on a completed
report, and read-only analytics across reports. Integrations are a
stretch/roadmap item, not part of the core surface.
"""
from __future__ import annotations

import os
import secrets
import time
from dataclasses import asdict
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import analytics
import auth
import live
import meta_client
import pipeline
import store
import voice

app = FastAPI(title="Baseer — Arabic Field Inspection Copilot", version="0.3.0")
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
DATA_DIR = Path(os.getenv("BASEER_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))

# Durable store (production): REPORTS is a write-through cache over SQLite.
REPORTS: dict[str, dict] = {}

store.init(str(DATA_DIR / "baseer.db"))
REPORTS.update(store.load_reports())
_n_restored = live.restore_sessions(str(DATA_DIR))
if _n_restored:
    print(f"[baseer] restored {_n_restored} interrupted live session(s) — resume them from the Live view")

_secret_file = DATA_DIR / ".secret"
if _secret_file.exists():
    _secret = _secret_file.read_text().strip()
else:
    _secret = secrets.token_urlsafe(32)
    _secret_file.write_text(_secret)
    try:
        os.chmod(_secret_file, 0o600)
    except OSError:
        pass
auth.init(_secret)

_first_admin = auth.ensure_admin(store._conn())
if _first_admin:
    print(f"[baseer] first boot: admin user '{_first_admin[0]}' created — "
          f"password: {_first_admin[1]} (shown once; set BASEER_ADMIN_PASSWORD to choose it)")

if not store.read_audit():
    for _r in REPORTS.values():
        for _i, _f in enumerate(_r.get("findings", [])):
            for _h in (_f.get("case") or {}).get("history", []):
                store.log_audit({
                    "ts": _h.get("ts", ""), "inspection_id": _r.get("inspection_id", ""),
                    "site": (_r.get("site_context") or "").strip() or "general",
                    "finding_index": _i, "action": _h.get("action", ""),
                    "actor": _h.get("actor", ""), "detail": _h.get("detail", ""),
                    "finding": _f.get("title_en", "")})


async def current_user(authorization: str = Header(default="")) -> dict:
    """Bearer-token guard. Public: /health, /, /static, /auth/login."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="login required")
    username = auth.check_token(authorization[len("Bearer "):])
    if not username:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    user = auth.get_user(store._conn(), username)
    if not user:
        raise HTTPException(status_code=401, detail="unknown user")
    return {"username": user["username"], "role": user["role"]}


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="admin only")
    return user


@app.get("/health")
def health():
    return {"status": "ok", "mode": meta_client.MODE}


def _save_evidence(inspection_id: str, payload: list[tuple[str, bytes]]) -> list[str]:
    """Durable copy of original uploads. Returns stored filenames."""
    dest = DATA_DIR / "evidence" / inspection_id
    dest.mkdir(parents=True, exist_ok=True)
    names = []
    for i, (name, blob) in enumerate(payload):
        safe = "".join(c for c in (name or "upload") if c.isalnum() or c in "._-") or "upload"
        fname = f"{i:02d}-{safe}"
        (dest / fname).write_bytes(blob)
        names.append(fname)
    return names


@app.post("/inspections")
async def create_inspection(
    notes: str = Form(""),
    site_context: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    user: dict = Depends(current_user),
):
    payload = [(f.filename or "upload", await f.read()) for f in files]
    report = pipeline.run_inspection(payload, notes, site_context)
    data = asdict(report)
    data["evidence_files"] = _save_evidence(report.inspection_id, payload)
    REPORTS[report.inspection_id] = data
    store.save_report(data)
    return data


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/inspections/{inspection_id}/chat")
def chat(inspection_id: str, req: ChatRequest, user: dict = Depends(current_user)):
    report = REPORTS.get(inspection_id)
    if report is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    answer = meta_client.chat_with_inspection(report, req.history, req.question)
    return {"answer": answer}


class CaseRequest(BaseModel):
    action: str  # assign | verify | approve
    assignee: str = ""
    actor: str = ""  # declared role identity, stored verbatim in the audit trail


@app.post("/inspections/{inspection_id}/findings/{index}/case")
def update_case(inspection_id: str, index: int, req: CaseRequest,
                user: dict = Depends(current_user)):
    report = REPORTS.get(inspection_id)
    if report is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    if index < 0 or index >= len(report["findings"]):
        raise HTTPException(status_code=404, detail="finding not found")
    finding = report["findings"][index]
    case = finding.setdefault("case", {"status": "open", "assignee": "", "verification": None})
    # Production accountability: the audit identity is the signed-in user,
    # never a client-supplied string.
    actor = f"{user['username']} ({user['role']})"
    if case["status"] == "closed":
        raise HTTPException(status_code=400, detail="case already closed")
    if req.action == "assign":
        if not req.assignee.strip():
            raise HTTPException(status_code=400, detail="assignee required")
        case["assignee"] = req.assignee.strip()
        case["status"] = "assigned"
        detail = f"to {case['assignee']}"
        pipeline.log_case_action(case, "assign", actor, detail)
    elif req.action == "verify":
        case["verification"] = meta_client.verify_finding(finding)
        detail = ("suggested resolved"
                  if (case.get("verification") or {}).get("suggested_resolved")
                  else "not resolved")
        pipeline.log_case_action(case, "verify", actor, detail)
    elif req.action == "approve":
        if not (case.get("verification") or {}).get("suggested_resolved"):
            raise HTTPException(
                status_code=400,
                detail="closure requires a verification suggesting resolution — a human approves, Baseer never closes alone")
        case["status"] = "closed"
        detail = "closed"
        pipeline.log_case_action(case, "approve", actor, detail)
    else:
        raise HTTPException(status_code=400, detail="unknown action")
    store.save_report(report)
    store.log_audit({
        "ts": case["history"][-1]["ts"] if case.get("history") else "",
        "inspection_id": inspection_id,
        "site": (report.get("site_context") or "").strip() or "general",
        "finding_index": index, "action": req.action, "actor": actor,
        "detail": detail, "finding": finding.get("title_en", ""),
    })
    return finding


@app.post("/inspections/{inspection_id}/findings/{index}/verify-evidence")
async def verify_with_evidence(
    inspection_id: str, index: int, files: list[UploadFile] = File(default=[]),
    actor: str = Form(""),
    user: dict = Depends(current_user),
):
    """Verify against AFTER photo/video of the same location (vision
    comparison). Additive to the plain verify action, which stays
    conservative without evidence. Approval is still required to close."""
    report = REPORTS.get(inspection_id)
    if report is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    if index < 0 or index >= len(report["findings"]):
        raise HTTPException(status_code=404, detail="finding not found")
    finding = report["findings"][index]
    case = finding.setdefault("case", {"status": "open", "assignee": "", "verification": None})
    if case["status"] == "closed":
        raise HTTPException(status_code=400, detail="case already closed")
    payload = [(f.filename or "after", await f.read()) for f in files]
    frames = pipeline.extract_frames(payload)
    case["verification"] = meta_client.compare_for_verification(finding, frames)
    actor = f"{user['username']} ({user['role']})"
    detail = ("suggested resolved"
              if (case.get("verification") or {}).get("suggested_resolved")
              else "not resolved")
    pipeline.log_case_action(case, "verify_evidence", actor, detail)
    _save_evidence(inspection_id + "-verify", [(f"after-{index}-{n[0]}", n[1])
                                              for n in payload])
    store.save_report(report)
    store.log_audit({
        "ts": case["history"][-1]["ts"] if case.get("history") else "",
        "inspection_id": inspection_id,
        "site": (report.get("site_context") or "").strip() or "general",
        "finding_index": index, "action": "verify_evidence", "actor": actor,
        "detail": detail, "finding": finding.get("title_en", ""),
    })
    return finding


class LiveStartRequest(BaseModel):
    site_context: str = ""


@app.post("/live/sessions")
def live_start(req: LiveStartRequest, user: dict = Depends(current_user)):
    return live.start_session(req.site_context)


@app.get("/live/sessions")
def live_list(user: dict = Depends(current_user)):
    """Open (incl. restored-after-restart) live sessions, for resume."""
    return {"sessions": [
        {"session_id": sid,
         "site_context": s.get("site_context", ""),
         "frames_received": s.get("frames_received", 0),
         "alerts_total": len(s.get("alerts", [])),
         "started_at": s.get("started_at", "")}
        for sid, s in live.SESSIONS.items()]}


@app.post("/live/sessions/{session_id}/frames")
async def live_frames(session_id: str, files: list[UploadFile] = File(default=[]),
                      user: dict = Depends(current_user)):
    payload = [(f.filename or "frame", await f.read()) for f in files]
    if session_id not in live.SESSIONS:
        raise HTTPException(status_code=404, detail="live session not found")
    _dest = DATA_DIR / "evidence" / session_id
    _dest.mkdir(parents=True, exist_ok=True)
    _base = int(time.time() * 1000)
    for _n, (_name, _blob) in enumerate(payload):
        _safe = "".join(c for c in (_name or "frame") if c.isalnum() or c in "._-") or "frame"
        (_dest / f"{_base}-{_n:02d}-{_safe}").write_bytes(_blob)
    frames = pipeline.extract_frames(payload)
    try:
        return live.add_frames(session_id, frames)
    except KeyError:
        raise HTTPException(status_code=404, detail="live session not found")


class LiveFinishRequest(BaseModel):
    notes: str = ""


@app.post("/live/sessions/{session_id}/finish")
def live_finish(session_id: str, req: LiveFinishRequest,
                user: dict = Depends(current_user)):
    try:
        data = live.finish_session(session_id, req.notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="live session not found")
    _live_dir = DATA_DIR / "evidence" / session_id
    data["evidence_files"] = sorted(p.name for p in _live_dir.glob("*")) if _live_dir.exists() else []
    REPORTS[data["inspection_id"]] = data
    store.save_report(data)
    return data


@app.get("/analytics")
def get_analytics(site: str = "", user: dict = Depends(current_user)):
    return analytics.compute(list(REPORTS.values()), site=site)


@app.get("/sites")
def list_sites(user: dict = Depends(current_user)):
    """Site registry derived from real inspection contexts — never
    invented. Empty contexts group under 'general'."""
    counts: dict[str, int] = {}
    for r in list(analytics.SEED_REPORTS) + list(REPORTS.values()):
        key = (r.get("site_context") or "").strip() or "general"
        counts[key] = counts.get(key, 0) + 1
    return {"sites": [{"site": s, "inspections": n} for s, n in sorted(counts.items())]}


@app.get("/audit")
def get_audit(format: str = "json", user: dict = Depends(current_user)):
    """Formal audit trail: every case action across live reports, newest
    first. Durable in SQLite (survives restarts); entries are append-only,
    this endpoint only reads. format=csv returns a downloadable CSV."""
    entries = store.read_audit()
    if format == "csv":
        import csv
        import io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=["ts", "inspection_id", "site", "finding_index",
                                            "finding", "action", "actor", "detail"])
        w.writeheader()
        w.writerows(entries)
        return PlainTextResponse(buf.getvalue(), media_type="text/csv")
    return {"entries": entries}


@app.get("/inspections/{inspection_id}/evidence/{filename}")
def get_evidence(inspection_id: str, filename: str, user: dict = Depends(current_user)):
    """Download an original upload stored server-side."""
    safe_id = "".join(c for c in inspection_id if c.isalnum() or c in "-_")
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    path = DATA_DIR / "evidence" / safe_id / safe_name
    if not safe_id or not safe_name or not path.is_file():
        raise HTTPException(status_code=404, detail="evidence not found")
    return FileResponse(path)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


_login_failures: dict[str, list[float]] = {}


def _login_allowed(username: str) -> bool:
    now = time.time()
    hits = [t for t in _login_failures.get(username, []) if now - t < 300]
    _login_failures[username] = hits
    return len(hits) < 6


@app.post("/auth/login")
def login(req: LoginRequest):
    username = req.username.strip()
    if not _login_allowed(username):
        raise HTTPException(status_code=429, detail="too many failed attempts — wait 5 minutes")
    user = auth.get_user(store._conn(), username)
    if not user or not auth.verify_password(req.password, user["pw_hash"], user["salt"]):
        _login_failures.setdefault(username, []).append(time.time())
        raise HTTPException(status_code=401, detail="invalid username or password")
    _login_failures.pop(username, None)
    return {"token": auth.mint_token(user["username"]),
            "username": user["username"], "role": user["role"]}


@app.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user


@app.get("/auth/users")
def list_users(admin: dict = Depends(require_admin)):
    rows = store._conn().execute(
        "SELECT username, role, created_at FROM users ORDER BY username").fetchall()
    return {"users": [{"username": r[0], "role": r[1], "created_at": r[2]} for r in rows]}


@app.post("/auth/users")
def create_user_api(req: UserCreateRequest, admin: dict = Depends(require_admin)):
    try:
        auth.create_user(store._conn(), req.username, req.password, req.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"username": req.username.strip(), "role": req.role}


@app.delete("/auth/users/{username}")
def delete_user_api(username: str, admin: dict = Depends(require_admin)):
    if username == admin["username"]:
        raise HTTPException(status_code=400, detail="cannot delete your own admin account")
    cur = store._conn().execute("DELETE FROM users WHERE username = ?", (username,))
    store._conn().commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="user not found")
    return {"deleted": username}


@app.post("/auth/password")
def change_password_api(req: PasswordChangeRequest, user: dict = Depends(current_user)):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="new password must be at least 8 characters")
    row = auth.get_user(store._conn(), user["username"])
    if not row or not auth.verify_password(req.old_password, row["pw_hash"], row["salt"]):
        raise HTTPException(status_code=401, detail="current password is wrong")
    pw_hash, salt = auth.hash_password(req.new_password)
    store._conn().execute("UPDATE users SET pw_hash = ?, salt = ? WHERE username = ?",
                          (pw_hash, salt, user["username"]))
    store._conn().commit()
    return {"username": user["username"]}


@app.websocket("/voice/transcribe")
async def voice_transcribe(ws: WebSocket):
    # Mic audio in, transcript text out. Browsers cannot set WS headers,
    # so the client passes ?token= (query only, never the Meta key — that
    # stays server-side inside voice.proxy and never reaches the browser).
    await ws.accept()
    username = auth.check_token(ws.query_params.get("token", ""))
    if not username or not auth.get_user(store._conn(), username):
        await ws.close(code=4401)
        return
    await voice.proxy(ws, accepted=True)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
