"""
Baseer live-camera mode (Hussein's direction, 2026-10-21).

Second input mode next to upload-and-inspect:
  upload mode  — photo/video in, inspection starts immediately (~30s report)
  live mode    — a camera connected to the system (USB / phone / IP camera)
                 streams frames; Baseer samples and segments them as they
                 arrive, raises alerts the moment a violation appears, and
                 finishing the session produces the full report + cases
                 through the exact same reasoning path as an upload.

"Real-time" here means sampled near-real-time analysis — a frame every few
seconds — which is how production PPE-compliance monitoring actually works
and keeps API cost/latency sane. The session core below is transport-free:
the event-window build wires it to getUserMedia / an RTSP grabber; tonight
frames arrive through the REST endpoint (the web UI posts snapshots).
"""
from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone

import meta_client
import pipeline

SESSIONS: dict[str, dict] = {}

# Labels that read as violations get an immediate live alert on first sight.
VIOLATION_HINTS = ("without", "missing", "no_", "_no")


def start_session(site_context: str = "") -> dict:
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {
        "session_id": sid,
        "site_context": site_context,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "segments": [],          # meta_client.Segment objects
        "alerted_labels": set(),
        "alerts": [],
        "frames_received": 0,
    }
    return {"session_id": sid, "status": "live"}


def add_frames(session_id: str, frames: list[bytes]) -> dict:
    session = SESSIONS.get(session_id)
    if session is None:
        raise KeyError("session not found")
    new_alerts: list[dict] = []
    for frame in frames:
        base_index = session["frames_received"]
        segments = meta_client.segment_frames([frame])
        for seg in segments:
            seg.frame_index = base_index
            session["segments"].append(seg)
            label = seg.label.lower()
            if any(h in label for h in VIOLATION_HINTS) and label not in session["alerted_labels"]:
                session["alerted_labels"].add(label)
                alert = {
                    "label": seg.label,
                    "label_ar": seg.label_ar,
                    "frame_index": base_index,
                    "message_en": f"Live alert: {seg.label.replace('_', ' ')} detected",
                    "message_ar": f"تنبيه مباشر: تم رصد {seg.label_ar}",
                }
                session["alerts"].append(alert)
                new_alerts.append(alert)
        session["frames_received"] += 1
    return {
        "session_id": session_id,
        "frames_received": session["frames_received"],
        "segments_total": len(session["segments"]),
        "new_alerts": new_alerts,
        "alerts_total": len(session["alerts"]),
    }


def finish_session(session_id: str, inspector_notes: str = "") -> dict:
    session = SESSIONS.pop(session_id, None)
    if session is None:
        raise KeyError("session not found")
    findings, summary_ar, summary_en = meta_client.reason_findings(
        session["segments"], inspector_notes, session["site_context"])
    return {
        "inspection_id": uuid.uuid4().hex[:12],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": meta_client.MODE,
        "source": "live-camera",
        "frames_processed": session["frames_received"],
        "segments": [asdict(s) for s in session["segments"]],
        "findings": pipeline.with_cases([asdict(f) for f in findings]),
        "summary_ar": summary_ar,
        "summary_en": summary_en,
        "live_alerts": session["alerts"],
    }
