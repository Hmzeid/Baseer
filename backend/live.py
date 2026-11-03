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
import store
import yolo

SESSIONS: dict[str, dict] = {}


def _snapshot(session: dict) -> None:
    """Persist everything needed to resume: segments + alerts + decision.
    Frame bytes are rebuilt from the stored evidence originals on restore."""
    try:
        store.save_session(session["session_id"], {
            "site_context": session.get("site_context", ""),
            "started_at": session.get("started_at", ""),
            "seg_path": session.get("seg_path"),
            "segments": [asdict(s) for s in session.get("segments", [])],
            "alerted_labels": sorted(session.get("alerted_labels", set())),
            "alerts": session.get("alerts", []),
            "frames_received": session.get("frames_received", 0),
        })
    except Exception:
        pass  # durability layer; never break the live loop


def restore_sessions(evidence_root: str) -> int:
    """Re-register sessions salvaged from SQLite after a restart. Returns
    the count restored. Frame bytes are re-extracted from the stored
    evidence originals (chronological order)."""
    from pathlib import Path
    restored = 0
    for sid, snap in store.load_sessions().items():
        frames: list[bytes] = []
        evdir = Path(evidence_root) / "evidence" / sid
        if evdir.exists():
            for p in sorted(evdir.glob("*")):
                try:
                    frames.extend(pipeline.extract_frames([(p.name, p.read_bytes())]))
                except Exception:
                    continue
        SESSIONS[sid] = {
            "session_id": sid,
            "site_context": snap.get("site_context", ""),
            "started_at": snap.get("started_at", ""),
            "segments": [meta_client.Segment(**s) for s in snap.get("segments", [])],
            "frames": frames,
            "seg_path": snap.get("seg_path"),
            "alerted_labels": set(snap.get("alerted_labels", [])),
            "alerts": snap.get("alerts", []),
            "frames_received": snap.get("frames_received", 0),
        }
        restored += 1
    return restored

# Labels that read as violations get an immediate live alert on first sight.
VIOLATION_HINTS = ("without", "missing", "no_", "_no")


def start_session(site_context: str = "") -> dict:
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {
        "session_id": sid,
        "site_context": site_context,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "segments": [],          # meta_client.Segment objects (SAM path)
        "frames": [],            # raw JPEG bytes (vision path + finish)
        "seg_path": None,        # decided on first frame: "sam" | "vision"
        "alerted_labels": set(),
        "alerts": [],
        "frames_received": 0,
    }
    _snapshot(SESSIONS[sid])
    return {"session_id": sid, "status": "live"}


def _decide_path(session: dict) -> str:
    """Pick the segmenter for this session. "vision" is forced by config;
    "auto" tries SAM once and pins "vision" for the rest of the session
    if SAM answers 404 (gated team). "sam" stays strict and raises."""
    if session["seg_path"] is not None:
        return session["seg_path"]
    if meta_client.SEGMENTATION == "vision":
        session["seg_path"] = "vision"
    else:
        session["seg_path"] = "sam"
    return session["seg_path"]


def _vision_alerts(session: dict, findings: list, frame_index: int) -> list[dict]:
    """One alert per violation type on first appearance. Only high/medium
    findings alert — low findings are observations, not alarms."""
    new_alerts: list[dict] = []
    for f in findings:
        key = (f.title_en or "").strip().lower()
        if not key or f.severity not in ("high", "medium"):
            continue
        if key in session["alerted_labels"]:
            continue
        session["alerted_labels"].add(key)
        alert = {
            "label": f.title_en,
            "label_ar": f.title_ar,
            "frame_index": frame_index,
            "message_en": f"Live alert: {f.title_en} detected",
            "message_ar": f"تنبيه مباشر: تم رصد {f.title_ar}",
        }
        session["alerts"].append(alert)
        new_alerts.append(alert)
    return new_alerts


def _yolo_alerts(session: dict, alerts: list[dict], frame_index: int) -> list[dict]:
    """First-appearance YOLO alerts. Same shape as the other alert paths,
    plus source + confidence so the UI can show what watched the stream."""
    new_alerts: list[dict] = []
    for a in alerts:
        key = a.get("key", "")
        if not key or a.get("severity") not in ("high", "medium"):
            continue
        if key in session["alerted_labels"]:
            continue
        session["alerted_labels"].add(key)
        alert = {
            "label": a["title_en"],
            "label_ar": a["title_ar"],
            "frame_index": frame_index,
            "message_en": f"Live alert: {a['title_en']} detected",
            "message_ar": f"تنبيه مباشر: تم رصد {a['title_ar']}",
            "source": "yolo",
            "confidence": a.get("confidence"),
        }
        session["alerts"].append(alert)
        new_alerts.append(alert)
    return new_alerts


def add_frames(session_id: str, frames: list[bytes]) -> dict:
    """Analyze each frame as it arrives. Mock mode keeps the synthetic
    segment path. Live mode uses the session's pinned path: SAM segments
    where enabled, otherwise one vision call per frame (auto mode pins
    "vision" for the session after the first SAM 404).

    When a local YOLO model is configured (BASEER_YOLO_WEIGHTS), the YOLO
    path alerts on PPE detections directly; frames still accumulate so the
    Meta report at finish is unchanged."""
    session = SESSIONS.get(session_id)
    if session is None:
        raise KeyError("session not found")
    new_alerts: list[dict] = []
    use_vision = (
        meta_client.MODE == "live"
        and _decide_path(session) == "vision"
    )
    yolo_active = meta_client.MODE == "live" and yolo.is_configured()
    for frame in frames:
        base_index = session["frames_received"]
        if yolo_active and frame:
            session["frames"].append(frame)
            try:
                dets = yolo.detect(frame)
            except Exception:
                dets = None  # never break the loop; fall back below
            if dets is not None:
                new_alerts.extend(
                    _yolo_alerts(session, yolo.map_detections(dets),
                                 base_index))
                session["frames_received"] += 1
                continue
        if use_vision:
            session["frames"].append(frame)
            if frame:
                findings, _, _ = meta_client.reason_from_frames(
                    [frame], "", session["site_context"])
                for f in findings:
                    f.frame_index = base_index
                new_alerts.extend(
                    _vision_alerts(session, findings, base_index))
        else:
            try:
                segments = meta_client.segment_frames([frame])
            except RuntimeError as exc:
                if (meta_client.MODE == "live"
                        and meta_client.SEGMENTATION == "auto"
                        and "404" in str(exc)):
                    session["seg_path"] = "vision"
                    session["frames"].append(frame)
                    if frame:
                        findings, _, _ = meta_client.reason_from_frames(
                            [frame], "", session["site_context"])
                        for f in findings:
                            f.frame_index = base_index
                        new_alerts.extend(
                            _vision_alerts(session, findings, base_index))
                    session["frames_received"] += 1
                    continue
                raise
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
    _snapshot(session)
    return {
        "session_id": session_id,
        "frames_received": session["frames_received"],
        "segments_total": len(session["segments"]),
        "new_alerts": new_alerts,
        "alerts_total": len(session["alerts"]),
    }


def finish_session(session_id: str, inspector_notes: str = "") -> dict:
    """Finish through the same reasoning path as an upload. Vision-path
    sessions re-run the full vision analysis over the collected frames;
    SAM-path sessions reason over segments as before."""
    session = SESSIONS.pop(session_id, None)
    if session is None:
        raise KeyError("session not found")
    try:
        store.delete_session(session_id)
    except Exception:
        pass
    segmentation_source = "mock" if meta_client.MODE != "live" else "sam"
    if session.get("seg_path") == "vision" or (
            meta_client.MODE == "live" and not session["segments"] and session["frames"]):
        segmentation_source = "vision"
        if session["frames"]:
            findings, summary_ar, summary_en = meta_client.reason_from_frames(
                session["frames"], inspector_notes, session["site_context"])
        else:
            findings, summary_ar, summary_en = meta_client.reason_findings(
                [], inspector_notes, session["site_context"])
        segments: list = []
    else:
        findings, summary_ar, summary_en = meta_client.reason_findings(
            session["segments"], inspector_notes, session["site_context"])
        segments = session["segments"]
    if meta_client.MODE != "live":
        segmentation_source = "mock"
    return {
        "inspection_id": uuid.uuid4().hex[:12],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": meta_client.MODE,
        "source": "live-camera",
        "frames_processed": session["frames_received"],
        "segments": [asdict(s) for s in segments],
        "findings": pipeline.with_cases([asdict(f) for f in findings]),
        "summary_ar": summary_ar,
        "summary_en": summary_en,
        "segmentation_source": segmentation_source,
        "site_context": session.get("site_context", ""),
        "live_alerts": session["alerts"],
    }
