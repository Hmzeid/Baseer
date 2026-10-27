"""Baseer API — FastAPI surface.

Core: POST /inspections (the ~30-second inspection).
Layers (Hussein's decision, 2026-10-21): evidence chat on a completed
report, and read-only analytics across reports. Integrations are a
stretch/roadmap item, not part of the core surface.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import analytics
import live
import meta_client
import pipeline
import voice

app = FastAPI(title="Baseer — Arabic Field Inspection Copilot", version="0.2.0")
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

# In-memory report store (demo-grade; a real deployment uses a database).
REPORTS: dict[str, dict] = {}


@app.get("/health")
def health():
    return {"status": "ok", "mode": meta_client.MODE}


@app.post("/inspections")
async def create_inspection(
    notes: str = Form(""),
    site_context: str = Form(""),
    files: list[UploadFile] = File(default=[]),
):
    payload = [(f.filename or "upload", await f.read()) for f in files]
    report = pipeline.run_inspection(payload, notes, site_context)
    data = asdict(report)
    REPORTS[report.inspection_id] = data
    return data


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/inspections/{inspection_id}/chat")
def chat(inspection_id: str, req: ChatRequest):
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
def update_case(inspection_id: str, index: int, req: CaseRequest):
    report = REPORTS.get(inspection_id)
    if report is None:
        raise HTTPException(status_code=404, detail="inspection not found")
    if index < 0 or index >= len(report["findings"]):
        raise HTTPException(status_code=404, detail="finding not found")
    finding = report["findings"][index]
    case = finding.setdefault("case", {"status": "open", "assignee": "", "verification": None})
    if case["status"] == "closed":
        raise HTTPException(status_code=400, detail="case already closed")
    if req.action == "assign":
        if not req.assignee.strip():
            raise HTTPException(status_code=400, detail="assignee required")
        case["assignee"] = req.assignee.strip()
        case["status"] = "assigned"
        pipeline.log_case_action(case, "assign", req.actor, f"to {case['assignee']}")
    elif req.action == "verify":
        case["verification"] = meta_client.verify_finding(finding)
        pipeline.log_case_action(case, "verify", req.actor,
            "suggested resolved" if (case.get("verification") or {}).get("suggested_resolved")
            else "not resolved")
    elif req.action == "approve":
        if not (case.get("verification") or {}).get("suggested_resolved"):
            raise HTTPException(
                status_code=400,
                detail="closure requires a verification suggesting resolution — a human approves, Baseer never closes alone")
        case["status"] = "closed"
        pipeline.log_case_action(case, "approve", req.actor, "closed")
    else:
        raise HTTPException(status_code=400, detail="unknown action")
    return finding


@app.post("/inspections/{inspection_id}/findings/{index}/verify-evidence")
async def verify_with_evidence(
    inspection_id: str, index: int, files: list[UploadFile] = File(default=[]),
    actor: str = Form(""),
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
    pipeline.log_case_action(case, "verify_evidence", actor,
        "suggested resolved" if (case.get("verification") or {}).get("suggested_resolved")
        else "not resolved")
    return finding


class LiveStartRequest(BaseModel):
    site_context: str = ""


@app.post("/live/sessions")
def live_start(req: LiveStartRequest):
    return live.start_session(req.site_context)


@app.post("/live/sessions/{session_id}/frames")
async def live_frames(session_id: str, files: list[UploadFile] = File(default=[])):
    payload = [(f.filename or "frame", await f.read()) for f in files]
    frames = pipeline.extract_frames(payload)
    try:
        return live.add_frames(session_id, frames)
    except KeyError:
        raise HTTPException(status_code=404, detail="live session not found")


class LiveFinishRequest(BaseModel):
    notes: str = ""


@app.post("/live/sessions/{session_id}/finish")
def live_finish(session_id: str, req: LiveFinishRequest):
    try:
        data = live.finish_session(session_id, req.notes)
    except KeyError:
        raise HTTPException(status_code=404, detail="live session not found")
    REPORTS[data["inspection_id"]] = data
    return data


@app.get("/analytics")
def get_analytics(site: str = ""):
    return analytics.compute(list(REPORTS.values()), site=site)


@app.get("/sites")
def list_sites():
    """Site registry derived from real inspection contexts — never
    invented. Empty contexts group under 'general'."""
    counts: dict[str, int] = {}
    for r in list(analytics.SEED_REPORTS) + list(REPORTS.values()):
        key = (r.get("site_context") or "").strip() or "general"
        counts[key] = counts.get(key, 0) + 1
    return {"sites": [{"site": s, "inspections": n} for s, n in sorted(counts.items())]}


@app.get("/audit")
def get_audit(format: str = "json"):
    """Formal audit trail: every case action across live reports, newest
    first. History entries are append-only at the case level; this endpoint
    only reads. format=csv returns a downloadable CSV."""
    entries = []
    for r in list(REPORTS.values()):
        for i, f in enumerate(r.get("findings", [])):
            for h in (f.get("case") or {}).get("history", []):
                entries.append({
                    "ts": h.get("ts", ""),
                    "inspection_id": r.get("inspection_id", ""),
                    "site": (r.get("site_context") or "").strip() or "general",
                    "finding_index": i,
                    "finding": f.get("title_en", ""),
                    "action": h.get("action", ""),
                    "actor": h.get("actor", ""),
                    "detail": h.get("detail", ""),
                })
    entries.sort(key=lambda e: e["ts"], reverse=True)
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


@app.websocket("/voice/transcribe")
async def voice_transcribe(ws: WebSocket):
    # Mic audio in, transcript text out. The Meta key is attached
    # server-side inside voice.proxy — it never reaches the browser.
    await voice.proxy(ws)


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
