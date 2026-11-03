"""Local YOLO provider for the live camera stream (real-life path).

In production the stream goes to YOLO: per-frame PPE detections fire live
alerts locally (fast, offline-capable, no per-frame API cost), while the
Meta API still writes the final grounded report at session finish from the
accumulated frames.

Setup (operator):
  1. pip install -r backend/requirements-yolo.txt   (torch + ultralytics)
  2. Drop the trained PPE weights at, e.g., data/yolo/best.pt
  3. Set BASEER_YOLO_WEIGHTS to that path and restart.

Without weights (or without torch installed) this module reports
unconfigured and the live path keeps its current SAM/vision behavior —
nothing breaks, mock mode is untouched.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# label substring (lowercase) -> (title_en, title_ar, severity).
# First match wins; plain "person"/"worker" never alerts on its own.
DEFAULT_MAP: dict[str, tuple[str, str, str]] = {
    "no helmet": ("Worker without a safety helmet",
                  "عامل بدون خوذة حماية", "high"),
    "without helmet": ("Worker without a safety helmet",
                       "عامل بدون خوذة حماية", "high"),
    "no-helmet": ("Worker without a safety helmet",
                  "عامل بدون خوذة حماية", "high"),
    "no hard hat": ("Worker without a safety helmet",
                    "عامل بدون خوذة حماية", "high"),
    "no vest": ("Worker without a safety vest",
                "عامل بدون سترة سلامة", "medium"),
    "without vest": ("Worker without a safety vest",
                     "عامل بدون سترة سلامة", "medium"),
    "no-vest": ("Worker without a safety vest",
                "عامل بدون سترة سلامة", "medium"),
    "no gloves": ("Worker without gloves",
                  "عامل بدون قفازات", "medium"),
    "without gloves": ("Worker without gloves",
                       "عامل بدون قفازات", "medium"),
    "smoke": ("Smoke visible", "دخان ظاهر", "high"),
    "fire": ("Fire visible", "حريق ظاهر", "high"),
}

_model = None
_model_path: str | None = None


def weights_path() -> str:
    return os.getenv("BASEER_YOLO_WEIGHTS", "").strip()


def confidence() -> float:
    try:
        return float(os.getenv("BASEER_YOLO_CONF", "0.5"))
    except ValueError:
        return 0.5


def label_map() -> dict[str, tuple[str, str, str]]:
    merged = dict(DEFAULT_MAP)
    raw = os.getenv("BASEER_YOLO_MAP", "").strip()
    if raw:
        try:
            for k, v in json.loads(raw).items():
                if isinstance(v, (list, tuple)) and len(v) == 3:
                    merged[str(k).lower()] = (str(v[0]), str(v[1]),
                                              str(v[2]))
        except (ValueError, AttributeError):
            pass  # bad JSON never breaks the loop; defaults stand
    return merged


def is_configured() -> bool:
    """True only when weights exist AND the runtime imports."""
    wp = weights_path()
    if not wp or not Path(wp).is_file():
        return False
    try:
        import ultralytics  # noqa: F401
        return True
    except ImportError:
        return False


def status() -> dict:
    wp = weights_path()
    try:
        import ultralytics  # noqa: F401
        runtime = True
    except ImportError:
        runtime = False
    info: dict = {"configured": bool(wp and Path(wp).is_file() and runtime),
                  "weights": wp, "weights_found": bool(wp and Path(wp).is_file()),
                  "runtime": runtime, "confidence": confidence()}
    if info["configured"]:
        try:
            info["classes"] = _load()[1]
        except Exception as exc:
            info["configured"] = False
            info["error"] = str(exc)[:200]
    return info


def _load():
    """Lazily load the model once. Raises RuntimeError with a human message."""
    global _model, _model_path
    wp = weights_path()
    if not wp or not Path(wp).is_file():
        raise RuntimeError("YOLO weights not set — set BASEER_YOLO_WEIGHTS "
                           "to a .pt file (see ops/RUNBOOK.md)")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics/torch not installed — run: pip "
                           "install -r backend/requirements-yolo.txt") from exc
    if _model is None or _model_path != wp:
        _model = YOLO(wp)
        _model_path = wp
    names = getattr(getattr(_model, "model", None), "names", None)
    if callable(names):
        try:
            names = names()
        except Exception:
            names = None
    classes = ({int(k): str(v) for k, v in names.items()}
               if isinstance(names, dict) else {})
    return _model, classes


def detect(jpeg: bytes) -> list[dict]:
    """Run inference on one JPEG frame.

    Returns [{label, confidence, bbox}] with bbox in normalized xywh.
    Never returns synthetic data — empty list means nothing detected."""
    model, classes = _load()
    import io as _io
    from PIL import Image as _Image
    img = _Image.open(_io.BytesIO(jpeg)).convert("RGB")
    out = model.predict(img, conf=confidence(), verbose=False)
    dets: list[dict] = []
    for r in out:
        boxes = getattr(r, "boxes", None)
        if boxes is None:
            continue
        for b in boxes:
            try:
                cls = int(b.cls[0])
                conf = float(b.conf[0])
                xywhn = [float(x) for x in b.xywhn[0]]
            except (IndexError, TypeError, ValueError):
                continue
            label = str(classes.get(cls, cls))
            dets.append({"label": label, "confidence": round(conf, 3),
                         "bbox": [round(x, 4) for x in xywhn]})
    return dets


def map_detections(dets: list[dict]) -> list[dict]:
    """Map raw YOLO labels to Baseer violation alerts (pure function).

    Returns [{key, title_en, title_ar, severity, confidence}]; plain
    person/worker labels and below-threshold hits produce nothing."""
    mapping = label_map()
    conf_min = confidence()
    alerts: list[dict] = []
    for d in dets:
        label = str(d.get("label", "")).lower()
        if not label or label in ("person", "worker", "people"):
            continue
        if float(d.get("confidence", 0)) < conf_min:
            continue
        for sub, (en, ar_, sev) in mapping.items():
            if sub in label:
                alerts.append({"key": en.strip().lower(), "title_en": en,
                               "title_ar": ar_, "severity": sev,
                               "confidence": d.get("confidence")})
                break
    return alerts
