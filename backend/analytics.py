"""
Baseer analytics — Layer 2 (Hussein's decision, 2026-10-21).

Read-only aggregation over completed inspection reports: the safety
manager's view (top hazards, severity mix, recent activity). The seed
entries below are clearly-labeled demo history so the dashboard has shape
before real inspections accumulate; live reports are merged on top.
"""
from __future__ import annotations

from collections import Counter

SEED_REPORTS: list[dict] = [
    {"inspection_id": "seed-1041", "created_at": "2026-10-26T09:12:00Z", "frames_processed": 6,
     "findings": [
         {"title_en": "Worker without a safety helmet", "title_ar": "عامل بدون خوذة حماية", "severity": "high"},
         {"title_en": "Unmarked forklift path", "title_ar": "مسار الرافعة غير محدد بعلامات", "severity": "medium"}]},
    {"inspection_id": "seed-1038", "created_at": "2026-10-25T14:03:00Z", "frames_processed": 5,
     "findings": [
         {"title_en": "Worker without a safety helmet", "title_ar": "عامل بدون خوذة حماية", "severity": "high"},
         {"title_en": "Missing guard rail at the edge", "title_ar": "غياب حاجز الحماية عند الحافة", "severity": "high"},
         {"title_en": "Blocked emergency exit", "title_ar": "مخرج طوارئ مسدود", "severity": "medium"}]},
    {"inspection_id": "seed-1035", "created_at": "2026-10-24T08:47:00Z", "frames_processed": 4,
     "findings": [
         {"title_en": "Unmarked forklift path", "title_ar": "مسار الرافعة غير محدد بعلامات", "severity": "medium"},
         {"title_en": "Missing machine guard", "title_ar": "غياب واقي الماكينة", "severity": "high"}]},
]


def compute(live_reports: list[dict]) -> dict:
    reports = SEED_REPORTS + live_reports
    by_severity: Counter = Counter()
    hazard_counter: Counter = Counter()
    hazard_ar: dict[str, str] = {}
    for r in reports:
        for f in r.get("findings", []):
            by_severity[f.get("severity", "low")] += 1
            key = f.get("title_en", "")
            if key:
                hazard_counter[key] += 1
                hazard_ar[key] = f.get("title_ar", key)
    top_hazards = [
        {"title_en": title, "title_ar": hazard_ar.get(title, title), "count": n}
        for title, n in hazard_counter.most_common(5)
    ]
    recent = [
        {"inspection_id": r["inspection_id"], "created_at": r.get("created_at", ""),
         "findings": len(r.get("findings", [])),
         "high": sum(1 for f in r.get("findings", []) if f.get("severity") == "high")}
        for r in reports[-5:][::-1]
    ]
    return {
        "demo_seed_included": True,
        "total_inspections": len(reports),
        "total_findings": sum(by_severity.values()),
        "by_severity": {"high": by_severity["high"], "medium": by_severity["medium"],
                        "low": by_severity["low"]},
        "top_hazards": top_hazards,
        "recent": recent,
    }
