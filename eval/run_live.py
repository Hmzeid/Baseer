"""Run the FIXED eval set (scenes.json) through the live vision pipeline.

Run: cd eval && BASEER_MODE=live BASEER_SEGMENTATION=vision \
     ../.venv/bin/python run_live.py
(The key comes from Ai/Baseer/.env via the runner's own loader below —
never print it, never commit it.)

For each scene: up to 3 evenly spaced frames (videos) or the photo itself,
plus the scene's notes_ar, through pipeline.run_inspection. Writes:
  predictions.json    {scene_id: [labels]} for score.py
  determinations.json {scene_id: true if any finding is "uncertain"}
  runs/<scene_id>.json  full reports (for the README failure narrative)

Title -> label map is keyword-based and FIXED here; unmapped titles fall
through as their own slug so unexpected findings still count (as false
alarms on clean scenes), never silently dropped.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))


def load_dotenv() -> None:
    root = os.path.join(HERE, "..")
    for name in (".env",):
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value


def title_to_label(title_en: str) -> str:
    t = (title_en or "").lower()
    if "helmet" in t or "hard hat" in t or "خوذة" in t:
        return "worker_without_helmet"
    if "guard rail" in t or "guardrail" in t:
        return "guard_rail_missing"
    if "forklift" in t and ("mark" in t or "path" in t or "route" in t):
        return "forklift_path_unmarked"
    if "ladder" in t:
        return "unsafe_ladder_work"
    if "eye" in t or "goggle" in t or "face shield" in t or "hood" in t:
        return "missing_eye_protection"
    slug = re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:48]
    return slug or "unmapped_finding"


def site_context(scene_id: str) -> str:
    if scene_id.startswith("construction"):
        return "construction site"
    if scene_id.startswith("farm"):
        return "farm"
    return "factory (industrial)"


def main() -> int:
    load_dotenv()
    import pipeline

    scenes = json.load(open(os.path.join(HERE, "scenes.json"), encoding="utf-8"))
    os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
    predictions: dict[str, list[str]] = {}
    determinations: dict[str, bool] = {}
    pending: list[dict] = []
    for scene in scenes:
        sid = scene["scene_id"]
        rp = os.path.join(HERE, "runs", f"{sid}.json")
        if os.path.exists(rp):
            try:
                prev = json.load(open(rp, encoding="utf-8"))
                if "labels" in prev:
                    predictions[sid] = prev["labels"]
                    determinations[sid] = bool(prev.get("uncertain", False))
                    print(f"[skip] {sid}: already ran "
                          f"({len(prev['labels'])} labels)", flush=True)
                    continue
            except Exception:
                pass
        pending.append(scene)
    for n, scene in enumerate(pending, 1):
        sid = scene["scene_id"]
        media = os.path.join(HERE, "..", scene["media"])
        blob = open(media, "rb").read()
        frames = pipeline.extract_frames([(os.path.basename(media), blob)])
        if len(frames) > 3:
            frames = [frames[0], frames[len(frames) // 2], frames[-1]]
        files = [(f"eval-{i}.jpg", fr) for i, fr in enumerate(frames)]
        try:
            report = pipeline.run_inspection(files, scene.get("notes_ar", ""), site_context(sid))
            labels = sorted({title_to_label(f["title_en"]) for f in report.findings})
            uncertain = any(f.get("determination") == "uncertain" for f in report.findings)
            json.dump(
                {"scene_id": sid, "labels": labels, "uncertain": uncertain,
                 "findings": [{"title_en": f["title_en"], "severity": f["severity"],
                               "determination": f.get("determination"),
                               "frame_index": f["frame_index"]} for f in report.findings],
                 "summary_en": report.summary_en,
                 "segmentation_source": report.segmentation_source},
                open(os.path.join(HERE, "runs", f"{sid}.json"), "w", encoding="utf-8"),
                ensure_ascii=False, indent=1)
        except Exception as exc:  # a scene that errors is a miss, recorded honestly
            labels, uncertain = [], False
            json.dump({"scene_id": sid, "error": str(exc)[:300]},
                      open(os.path.join(HERE, "runs", f"{sid}.json"), "w", encoding="utf-8"))
            print(f"[{n}/{len(scenes)}] {sid}: RUN-ERROR {exc}", flush=True)
            predictions[sid] = labels
            determinations[sid] = uncertain
            continue
        predictions[sid] = labels
        determinations[sid] = uncertain
        print(f"[{n}/{len(pending)}] {sid}: {labels} uncertain={uncertain}", flush=True)
    json.dump(predictions, open(os.path.join(HERE, "predictions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(determinations, open(os.path.join(HERE, "determinations.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"wrote predictions.json for {len(predictions)} scenes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
