"""
Baseer evaluation scorer (built 2026-10-21, pre-event).

Scores predicted hazard labels against a labeled scene set and reports
per-label and overall precision / recall / F1. The labeled set is built
from the same staged/public footage as the demo (see BUILD_PLAN.md,
"Evaluation benchmark"); it is FIXED before runs begin and is never tuned
to flatter the results.

Formats
-------
Ground truth (labels.json):
  [{"scene_id": "factory-01", "expected": ["worker_without_helmet", ...]}, ...]
  An empty "expected" list marks a NEGATIVE scene: any prediction there is
  a false positive — negative scenes are how false-alarm rate is measured.

Predictions (predictions.json):
  {"factory-01": ["worker_without_helmet", ...], ...}
  In live mode these come from the pipeline's segment labels per scene;
  latency per scene is reported separately by the run harness.

Usage:
  python score.py labels.json predictions.json
  python score.py --selftest
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict


def score(truth: list[dict], predictions: dict[str, list[str]]) -> dict:
    per_label: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    scenes_scored = 0
    negative_scenes = 0
    negative_false_alarms = 0
    for scene in truth:
        sid = scene["scene_id"]
        expected = set(scene.get("expected", []))
        predicted = set(predictions.get(sid, []))
        scenes_scored += 1
        if not expected:
            negative_scenes += 1
            negative_false_alarms += len(predicted)
        for label in predicted & expected:
            per_label[label]["tp"] += 1
        for label in predicted - expected:
            per_label[label]["fp"] += 1
        for label in expected - predicted:
            per_label[label]["fn"] += 1

    def prf(c: dict[str, int]) -> dict:
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {"tp": tp, "fp": fp, "fn": fn,
                "precision": round(precision, 3), "recall": round(recall, 3),
                "f1": round(f1, 3)}

    labels = {label: prf(counts) for label, counts in sorted(per_label.items())}
    totals = {"tp": sum(c["tp"] for c in per_label.values()),
              "fp": sum(c["fp"] for c in per_label.values()),
              "fn": sum(c["fn"] for c in per_label.values())}
    return {
        "scenes": scenes_scored,
        "negative_scenes": negative_scenes,
        "false_alarms_on_negative_scenes": negative_false_alarms,
        "overall": prf(totals),
        "per_label": labels,
    }


def _selftest() -> None:
    truth = [
        {"scene_id": "a", "expected": ["worker_without_helmet", "forklift"]},
        {"scene_id": "b", "expected": ["guard_rail_missing"]},
        {"scene_id": "c", "expected": []},  # negative scene
    ]
    preds = {
        "a": ["worker_without_helmet"],                 # 1 TP, 1 FN
        "b": ["guard_rail_missing", "worker"],          # 1 TP, 1 FP (not a hazard label match)
        "c": ["worker_without_helmet"],                 # false alarm on negative scene
    }
    r = score(truth, preds)
    assert r["overall"]["tp"] == 2 and r["overall"]["fp"] == 2 and r["overall"]["fn"] == 1, r
    assert r["per_label"]["worker_without_helmet"]["precision"] == 0.5, r
    assert r["per_label"]["worker_without_helmet"]["recall"] == 1.0, r  # 1 TP, 0 FN (the scene-c hit is an FP)
    assert r["false_alarms_on_negative_scenes"] == 1, r
    print("eval scorer selftest: OK", json.dumps(r["overall"]))


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        _selftest()
    elif len(sys.argv) == 3:
        truth = json.load(open(sys.argv[1], encoding="utf-8"))
        preds = json.load(open(sys.argv[2], encoding="utf-8"))
        print(json.dumps(score(truth, preds), indent=2, ensure_ascii=False))
    else:
        print(__doc__)
        sys.exit(2)
