"""
Baseer pipeline: ingest -> frame extraction -> SAM 3.1 segmentation ->
Muse Spark reasoning -> bilingual inspection report.
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
        d["case"] = {"status": "open", "assignee": "", "verification": None}
    return finding_dicts


def run_inspection(files: list[tuple[str, bytes]], inspector_notes: str,
                   site_context: str = "") -> InspectionReport:
    frames = extract_frames(files)
    if not frames:
        # Mock mode with no uploads still demonstrates the full flow.
        frames = [b""] if meta_client.MODE != "live" else []
    segments = meta_client.segment_frames(frames)
    findings, summary_ar, summary_en = meta_client.reason_findings(
        segments, inspector_notes, site_context)
    finding_dicts = with_cases([asdict(f) for f in findings])
    return InspectionReport(
        inspection_id=uuid.uuid4().hex[:12],
        created_at=datetime.now(timezone.utc).isoformat(),
        mode=meta_client.MODE,
        frames_processed=len(frames),
        segments=[asdict(s) for s in segments],
        findings=finding_dicts,
        summary_ar=summary_ar,
        summary_en=summary_en,
    )
