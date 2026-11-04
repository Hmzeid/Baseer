"""
Baseer analytics — Layer 2 (Hussein's decision, 2026-10-21).

Read-only aggregation over completed inspection reports: the safety
manager's view (top hazards, severity mix, recent activity). The seed
entries below are clearly-labeled demo history so the dashboard has shape
before real inspections accumulate; live reports are merged on top.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

SEED_REPORTS: list[dict] = [
    {"inspection_id": "seed-1041", "created_at": "2026-10-26T09:12:00Z", "frames_processed": 6,
     "site_context": "factory",
     "findings": [
         {"title_en": "Worker without a safety helmet", "title_ar": "عامل بدون خوذة حماية", "severity": "high"},
         {"title_en": "Unmarked forklift path", "title_ar": "مسار الرافعة غير محدد بعلامات", "severity": "medium"}]},
    {"inspection_id": "seed-1038", "created_at": "2026-10-25T14:03:00Z", "frames_processed": 5,
     "site_context": "construction",
     "findings": [
         {"title_en": "Worker without a safety helmet", "title_ar": "عامل بدون خوذة حماية", "severity": "high"},
         {"title_en": "Missing guard rail at the edge", "title_ar": "غياب حاجز الحماية عند الحافة", "severity": "high"},
         {"title_en": "Blocked emergency exit", "title_ar": "مخرج طوارئ مسدود", "severity": "medium"}]},
    {"inspection_id": "seed-1035", "created_at": "2026-10-24T08:47:00Z", "frames_processed": 4,
     "site_context": "factory",
     "findings": [
         {"title_en": "Unmarked forklift path", "title_ar": "مسار الرافعة غير محدد بعلامات", "severity": "medium"},
         {"title_en": "Missing machine guard", "title_ar": "غياب واقي الماكينة", "severity": "high"}]},
]


# Corrective-action deadlines by severity (days from the inspection). A case
# past its deadline and not closed is "overdue" — computed on read, so older
# reports get deadlines too and nothing new is stored.
SLA_DAYS = {"high": 1, "medium": 7, "low": 30}


def _parse_ts(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _site(report: dict) -> str:
    return (report.get("site_context") or "").strip() or "general"


def case_deadline(report: dict, finding: dict, now: datetime | None = None) -> dict:
    created = _parse_ts(report.get("created_at", ""))
    if created is None:
        return {"due_at": "", "overdue": False}
    due = created + timedelta(days=SLA_DAYS.get(finding.get("severity", "low"), 30))
    status = (finding.get("case") or {}).get("status", "open")
    now = now or datetime.now(timezone.utc)
    return {"due_at": due.isoformat(), "overdue": status != "closed" and now > due}


def summarize(report: dict) -> dict:
    """One row of the inspections history (no segments, no frames)."""
    findings = report.get("findings", [])
    sev = Counter(f.get("severity", "low") for f in findings)
    statuses = Counter((f.get("case") or {}).get("status", "open") for f in findings)
    top = max(findings, key=lambda f: {"high": 2, "medium": 1}.get(f.get("severity"), 0),
              default=None)
    return {
        "inspection_id": report["inspection_id"],
        "created_at": report.get("created_at", ""),
        "site": _site(report),
        "source": report.get("source", "upload"),
        "mode": report.get("mode", ""),
        "segmentation_source": report.get("segmentation_source", ""),
        "frames_processed": report.get("frames_processed", 0),
        "findings": len(findings),
        "high": sev["high"], "medium": sev["medium"], "low": sev["low"],
        "open_cases": len(findings) - statuses["closed"],
        "closed_cases": statuses["closed"],
        "evidence_files": len(report.get("evidence_files", [])),
        "summary_en": report.get("summary_en", ""),
        "summary_ar": report.get("summary_ar", ""),
        "top_finding_en": (top or {}).get("title_en", ""),
        "top_finding_ar": (top or {}).get("title_ar", ""),
    }


def list_cases(reports: list[dict], now: datetime | None = None) -> list[dict]:
    """Every corrective-action case across reports, most urgent first."""
    now = now or datetime.now(timezone.utc)
    out = []
    for r in reports:
        created = _parse_ts(r.get("created_at", ""))
        age_days = max(0, (now - created).days) if created else 0
        for i, f in enumerate(r.get("findings", [])):
            case = f.get("case")
            if not case:
                continue
            history = case.get("history", [])
            out.append({
                "inspection_id": r["inspection_id"],
                "finding_index": i,
                "site": _site(r),
                "title_en": f.get("title_en", ""),
                "title_ar": f.get("title_ar", f.get("title_en", "")),
                "severity": f.get("severity", "low"),
                "status": case.get("status", "open"),
                "assignee": case.get("assignee", ""),
                "created_at": r.get("created_at", ""),
                "age_days": age_days,
                "suggested_resolved": bool((case.get("verification") or {}).get("suggested_resolved")),
                "notes": len(case.get("notes", [])),
                "last_action": history[-1] if history else None,
                **case_deadline(r, f, now),
            })
    rank = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda c: (c["status"] == "closed", not c["overdue"],
                            rank.get(c["severity"], 3), c["due_at"]))
    return out


def compute(live_reports: list[dict], site: str = "") -> dict:
    reports = SEED_REPORTS + live_reports
    if site:
        reports = [r for r in reports if _site(r) == site]
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
    by_date = sorted(reports, key=lambda r: r.get("created_at", ""), reverse=True)
    recent = [
        {"inspection_id": r["inspection_id"], "created_at": r.get("created_at", ""),
         "site": _site(r), "seed": r["inspection_id"].startswith("seed-"),
         "findings": len(r.get("findings", [])),
         "high": sum(1 for f in r.get("findings", []) if f.get("severity") == "high")}
        for r in by_date[:6]
    ]
    now = datetime.now(timezone.utc)
    daily: dict[str, dict] = {}
    for r in reports:
        try:
            day = datetime.fromisoformat(
                r.get("created_at", "").replace("Z", "+00:00")).date().isoformat()
        except (ValueError, TypeError):
            continue
        d = daily.setdefault(day, {"day": day, "inspections": 0, "findings": 0})
        d["inspections"] += 1
        d["findings"] += len(r.get("findings", []))
    if daily:
        # Zero-fill the calendar so quiet days show as gaps, not vanish.
        day = datetime.fromisoformat(min(daily)).date()
        last = max(datetime.fromisoformat(max(daily)).date(), now.date())
        while day <= last:
            daily.setdefault(day.isoformat(), {"day": day.isoformat(), "inspections": 0, "findings": 0})
            day += timedelta(days=1)
    trend = sorted(daily.values(), key=lambda d: d["day"])[-30:]
    open_cases = []
    for r in reports:
        try:
            age_days = max(0, (now - datetime.fromisoformat(
                r.get("created_at", "").replace("Z", "+00:00"))).days)
        except (ValueError, TypeError):
            age_days = 0
        for i, f in enumerate(r.get("findings", [])):
            case = f.get("case") or {}
            if case and case.get("status", "open") != "closed":
                open_cases.append({
                    "inspection_id": r["inspection_id"],
                    "finding_index": i,
                    "title_en": f.get("title_en", ""),
                    "title_ar": f.get("title_ar", f.get("title_en", "")),
                    "severity": f.get("severity", "low"),
                    "assignee": case.get("assignee", ""),
                    "status": case.get("status", "open"),
                    "age_days": age_days,
                    **case_deadline(r, f, now),
                })
    open_cases.sort(key=lambda c: (c["overdue"], c["age_days"], c["severity"] == "high"), reverse=True)
    all_cases = list_cases(reports, now)
    case_status = Counter(c["status"] for c in all_cases)
    return {
        "demo_seed_included": True,
        "total_inspections": len(reports),
        "total_findings": sum(by_severity.values()),
        "by_severity": {"high": by_severity["high"], "medium": by_severity["medium"],
                        "low": by_severity["low"]},
        "top_hazards": top_hazards,
        "recent": recent,
        "trend": trend,
        "open_cases": open_cases[:20],
        "cases": {
            "total": len(all_cases),
            "open": case_status["open"],
            "assigned": case_status["assigned"],
            "closed": case_status["closed"],
            "overdue": sum(1 for c in all_cases if c["overdue"]),
            "closure_rate": round(case_status["closed"] / len(all_cases), 3) if all_cases else 0.0,
        },
    }
