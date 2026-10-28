"""
Baseer pipeline: ingest -> frame extraction -> segmentation -> Muse
reasoning -> bilingual inspection report.

Segmentation source (BASEER_SEGMENTATION, default "auto"): SAM 3.1 where
enabled; Muse's own multimodal vision as fallback (Day-0 verdict Oct 26:
this team is SAM-gated, 404). The report records segmentation_source so
no reader mistakes a vision report for a segmented one — vision reports
carry no bounding-box overlays, only frame indices + regions in words.
"""
from __future__ import annotations

import io
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from PIL import Image

import meta_client

MAX_FRAMES = 8


@dataclass
class InspectionReport:
    inspection_id: str
    created_at: str
    mode: str
    frames_processed: int
    segments: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    summary_ar: str = ""
    summary_en: str = ""
    segmentation_source: str = "sam"  # sam | vision | mock (mock mode never claims SAM)
    site_context: str = ""  # free-text site label; drives /sites + site-scoped /analytics


def extract_frames(files: list[tuple[str, bytes]]) -> list[bytes]:
    """Accept uploaded (filename, bytes). Images pass through; videos are
    sampled with OpenCV when available. Returns up to MAX_FRAMES JPEG bytes."""
    frames: list[bytes] = []
    for name, blob in files:
        lower = name.lower()
        if lower.rsplit(".", 1)[-1] in ("jpg", "jpeg", "png", "webp"):
            frames.append(_to_jpeg(blob))
        elif lower.rsplit(".", 1)[-1] in ("mp4", "mov", "webm", "mkv"):
            frames.extend(_sample_video(blob))
        if len(frames) >= MAX_FRAMES:
            break
    return frames[:MAX_FRAMES]


def _to_jpeg(blob: bytes) -> bytes:
    img = Image.open(io.BytesIO(blob)).convert("RGB")
    img.thumbnail((1280, 1280))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


def _sample_video(blob: bytes) -> list[bytes]:
    try:
        import cv2  # optional at prep stage; required for real video ingest
        import numpy as np
    except ImportError:
        return []
    import os, tempfile
    frames: list[bytes] = []
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(blob)
        path = tmp.name
    try:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, total // MAX_FRAMES) if total else 30
        idx = 0
        while len(frames) < MAX_FRAMES:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                ok2, buf = cv2.imencode(".jpg", frame)
                if ok2:
                    frames.append(buf.tobytes())
            idx += 1
        cap.release()
    finally:
        os.unlink(path)
    return frames


def with_cases(finding_dicts: list[dict]) -> list[dict]:
    """Act step of the loop: every finding opens a corrective-action case.
    Lifecycle: open -> assigned -> (verification suggested) -> closed
    (human approval only — Baseer never closes a case by itself)."""
    for d in finding_dicts:
        d["case"] = {"status": "open", "assignee": "", "verification": None, "history": []}
    return finding_dicts


def _missing_ppe_concept(text: str) -> str | None:
    """Map a finding title to the SAM PPE concept it claims is missing."""
    t = (text or "").lower()
    if "helmet" in t or "hard hat" in t or "خوذة" in t:
        return "hard hat"
    if "vest" in t or "سترة" in t:
        return "safety vest"
    return None


def _overlap_ratio(a: list[float], b: list[float]) -> float:
    """Intersection over the smaller box. Boxes are [x, y, w, h], normalized."""
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    inter = ix * iy
    smaller = min(a[2] * a[3], b[2] * b[3])
    return inter / smaller if smaller > 0 else 0.0


def drop_covered_ppe_findings(finding_dicts: list[dict], segments: list) -> list[dict]:
    """Deterministic guard against missing-PPE over-flags (code-side; the
    prompt is frozen). A missing-helmet/vest finding survives only if some
    person box has NO overlapping box of that PPE concept. When every
    worker overlaps PPE (the compliant-crew case), the finding is dropped.
    Findings about other violations pass through untouched."""
    persons = [s for s in segments if (s.label or "").lower() == "person"]
    if not persons:
        return finding_dicts
    ppe: dict[str, list] = {}
    for s in segments:
        ppe.setdefault((s.label or "").lower(), []).append(s.bbox)
    kept = []
    for f in finding_dicts:
        concept = _missing_ppe_concept(
            f.get("title_en", "") + " " + f.get("title_ar", ""))
        if concept is None:
            kept.append(f)
            continue
        boxes = ppe.get(concept, [])
        uncovered = [p for p in persons
                     if not any(_overlap_ratio(p.bbox, b) > 0.25 for b in boxes)]
        if uncovered:
            kept.append(f)
    return kept


def log_case_action(case: dict, action: str, actor: str, detail: str = "") -> None:
    """Append one entry to a case's audit history. History is append-only:
    entries are never edited or removed, only added."""
    case.setdefault("history", []).append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor or "inspector",
        "detail": detail,
    })


def run_inspection(files: list[tuple[str, bytes]], inspector_notes: str,
                   site_context: str = "") -> InspectionReport:
    frames = extract_frames(files)
    if not frames:
        # Mock mode with no uploads still demonstrates the full flow.
        frames = [b""] if meta_client.MODE != "live" else []
    # Mock mode segments are synthetic fixtures, never SAM output — the
    # report must not claim "sam" for them (QA flag 2026-10-26).
    segmentation_source = "mock" if meta_client.MODE != "live" else "sam"
    segments: list = []
    if meta_client.SEGMENTATION == "vision":
        segmentation_source = "vision"
        if frames:
            findings, summary_ar, summary_en = meta_client.reason_from_frames(
                frames, inspector_notes, site_context)
        else:
            # No media: notes-only reasoning, same as the SAM path.
            findings, summary_ar, summary_en = meta_client.reason_findings(
                [], inspector_notes, site_context)
    else:
        try:
            segments = meta_client.segment_frames(frames)
            findings, summary_ar, summary_en = meta_client.reason_findings(
                segments, inspector_notes, site_context)
        except RuntimeError as exc:
            # SAM unreachable (404) + auto mode: fall back to vision, loudly.
            if meta_client.SEGMENTATION == "auto" and "404" in str(exc):
                segmentation_source = "vision"
                if frames:
                    findings, summary_ar, summary_en = meta_client.reason_from_frames(
                        frames, inspector_notes, site_context)
                else:
                    findings, summary_ar, summary_en = meta_client.reason_findings(
                        [], inspector_notes, site_context)
            else:
                raise
    if meta_client.MODE != "live":
        # Mock mode: every branch above produced synthetic fixtures, so the
        # final word is "mock" regardless of the SEGMENTATION setting.
        segmentation_source = "mock"
    finding_dicts = with_cases([asdict(f) for f in findings])
    if segmentation_source == "sam" and segments:
        # Code-side overlap guard (prompts frozen): drop missing-PPE
        # findings when every worker overlaps that PPE in SAM boxes.
        finding_dicts = drop_covered_ppe_findings(finding_dicts, segments)
    return InspectionReport(
        inspection_id=uuid.uuid4().hex[:12],
        created_at=datetime.now(timezone.utc).isoformat(),
        mode=meta_client.MODE,
        frames_processed=len(frames),
        segments=[asdict(s) for s in segments],
        findings=finding_dicts,
        summary_ar=summary_ar,
        summary_en=summary_en,
        segmentation_source=segmentation_source,
        site_context=site_context,
    )
