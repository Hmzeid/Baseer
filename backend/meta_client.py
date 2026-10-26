"""
Meta Model API client adapter for Baseer.

Contract verified 2026-10-21 from the official Cerebral Valley waiver/event
page plus multiple independent sources quoting Meta's docs (Meta's own doc
domains were unreachable from the research sandbox — re-confirm on
https://developer.meta.com/docs/model-api in a normal browser at kickoff):

  - Base URL: https://api.meta.ai/v1 — OpenAI-compatible Chat Completions
    (Responses API is Meta's recommended surface; chat shape used here).
  - Auth: Bearer key in env MODEL_API_KEY, created at dev.meta.ai
    (API Keys tab, per-team, keys start with "LLM_"). Self-serve — no need
    to wait for the Oct 26 kickoff.
  - Muse Spark: model "muse-spark-1.3" (STANDARD tier). NEVER use the
    "-contributor" variants for anything Veebase-related: Meta may train on
    Contributor prompts/completions. Spark is multimodal (image/video/PDF),
    ~1M-token context.
  - SAM 3.1: model "sam-3.1". Hosted API takes TEXT prompts only — ONE short
    English concept phrase per call ("person", "forklift", ...). Output is
    special-token text records: boxes + base85-encoded masks + stable object
    IDs tracked across video frames (see parse below). Per-team gated: a team
    without SAM enabled gets 404 model_not_found — verify before kickoff.

Modes via env BASEER_MODE: "mock" (default, deterministic samples) / "live".
ALL Meta-specific shaping stays in this file.
"""
from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass, field

import httpx

MODE = os.getenv("BASEER_MODE", "mock").lower()
BASE_URL = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1")
API_KEY = os.getenv("MODEL_API_KEY", "") or os.getenv("META_API_KEY", "")
MUSE_MODEL = os.getenv("MUSE_MODEL", "muse-spark-1.3")
SAM_MODEL = os.getenv("SAM_MODEL", "sam-3.1")

# English concept phrases for SAM 3.1 (one API call per phrase).
SAM_CONCEPTS = [
    "person", "hard hat", "safety vest", "forklift", "truck",
    "guard rail", "ladder", "scaffolding", "machine", "fire extinguisher",
]


@dataclass
class Segment:
    label: str          # e.g. "worker_without_ppe", "guard_rail", "forklift"
    label_ar: str       # Arabic label
    confidence: float
    frame_index: int
    bbox: list[float] = field(default_factory=list)  # x, y, w, h (normalized)


@dataclass
class Finding:
    title_ar: str
    title_en: str
    severity: str       # "high" | "medium" | "low"
    detail_ar: str
    detail_en: str = ""
    action_ar: str = ""  # recommended corrective action (Arabic)
    action_en: str = ""
    frame_index: int = 0
    source: str = "segments"        # segments | inspector | both
    visually_confirmed: bool = True


def _headers() -> dict:
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


_BOX_RE = re.compile(
    r"<\|box;x1=(?P<x1>\d+);y1=(?P<y1>\d+);x2=(?P<x2>\d+);y2=(?P<y2>\d+)"
    r"(?:;w=(?P<w>\d+);h=(?P<h>\d+))?\|>")


def parse_sam_output(text: str, concept: str, frame_index: int) -> list[Segment]:
    """Parse SAM 3.1 special-token output records into Segments.

    Boxes arrive as <|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>; masks as
    <|mask;...data=<H>,<W>,<base85 payload>|> ('~' prefix = lossless,
    '!' = one-bit). Mask decoding for evidence overlays lands in the
    Oct 26-27 build (the third-party `meta-sam-parser` package implements
    the same format); boxes + labels are enough for reasoning input.
    """
    out: list[Segment] = []
    for m in _BOX_RE.finditer(text or ""):
        x1, y1, x2, y2 = (int(m[k]) for k in ("x1", "y1", "x2", "y2"))
        w = int(m["w"]) if m["w"] else 1000
        h = int(m["h"]) if m["h"] else 1000
        out.append(Segment(
            label=concept,
            label_ar=CONCEPT_AR.get(concept, concept),
            confidence=0.0,  # hosted output carries no per-box score
            frame_index=frame_index,
            bbox=[x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h],
        ))
    return out


CONCEPT_AR = {
    "person": "شخص", "hard hat": "خوذة حماية", "safety vest": "سترة سلامة",
    "forklift": "رافعة شوكية", "truck": "شاحنة", "guard rail": "حاجز حماية",
    "ladder": "سلم", "scaffolding": "سقالة", "machine": "معدة",
    "fire extinguisher": "طفاية حريق",
}


def segment_frames(frames: list[bytes]) -> list[Segment]:
    """Run SAM 3.1 segmentation over extracted frames.

    Hosted SAM takes ONE text concept per call, so this loops concepts x
    frames. A 404 means SAM is not enabled for the team — surface it loudly.
    """
    if MODE != "live":
        return _mock_segments(len(frames))
    if not API_KEY:
        raise RuntimeError("live mode requires MODEL_API_KEY (create one at dev.meta.ai)")
    segments: list[Segment] = []
    with httpx.Client(timeout=180) as client:
        for idx, frame in enumerate(frames):
            image_url = "data:image/jpeg;base64," + base64.b64encode(frame).decode()
            for concept in SAM_CONCEPTS:
                payload = {
                    "model": SAM_MODEL,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {"type": "text", "text": concept},
                        ],
                    }],
                }
                resp = client.post(f"{BASE_URL}/chat/completions",
                                   json=payload, headers=_headers())
                if resp.status_code == 404:
                    raise RuntimeError(
                        "SAM 3.1 returned 404 model_not_found — the model is "
                        "not enabled for this team/key yet. Check dev.meta.ai.")
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                segments.extend(parse_sam_output(text, concept, idx))
    return segments


def reason_findings(segments: list[Segment], inspector_notes: str,
                    site_context: str = "") -> tuple[list[Finding], str, str]:
    """Muse Spark reasons over segments + inspector notes.

    Returns (findings, summary_ar, summary_en).
    """
    if MODE != "live":
        return _mock_findings(segments)
    if not API_KEY:
        raise RuntimeError("live mode requires MODEL_API_KEY (create one at dev.meta.ai)")
    if MUSE_MODEL.endswith("-contributor"):
        raise RuntimeError(
            "Refusing Contributor-tier model: Meta may train on its prompts. "
            "Use the Standard muse-spark-1.3.")
    import prompts
    payload = {
        "model": MUSE_MODEL,
        "messages": [
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": prompts.build_user_prompt(
                segments, inspector_notes, site_context)},
        ],
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=180) as client:
        resp = client.post(f"{BASE_URL}/chat/completions", json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    import json
    parsed = json.loads(content)
    known = {f.name for f in Finding.__dataclass_fields__.values()}
    findings = [Finding(**{k: v for k, v in f.items() if k in known})
                for f in parsed["findings"]]
    return findings, parsed["summary_ar"], parsed["summary_en"]


def verify_finding(finding: dict) -> dict:
    """Verify step: would a re-inspection clear this finding?

    Live build (Oct 30): re-run segmentation on the after-footage and check
    whether the violating segments persist. Mock mode returns the staged
    demo outcome — the flagship PPE finding resolves; the floor-marking
    finding deliberately does NOT, so the demo shows an honest mixed result.
    """
    title = (finding.get("title_en") or "").lower()
    if MODE == "live":
        # Conservative default until the segment comparison lands: never
        # auto-suggest resolution without evidence.
        return {"suggested_resolved": False,
                "note": "Live verification compares re-inspection segments; pending Oct 30 build."}
    if "forklift path" in title or "markings" in title:
        return {"suggested_resolved": False,
                "note": "Re-inspection still shows no floor markings on the forklift route."}
    return {"suggested_resolved": True,
            "note": "Re-inspection evidence shows the violation corrected (demo simulation)."}


def chat_with_inspection(report: dict, history: list[dict], question: str) -> str:
    """Evidence chat: answer questions about one completed inspection.

    Layer 1 (Hussein's decision, 2026-10-21): the report stays the core;
    chat hangs off it, grounded strictly in its findings and frames.
    """
    if MODE != "live":
        return _mock_chat(report, question)
    if not API_KEY:
        raise RuntimeError("live mode requires MODEL_API_KEY (create one at dev.meta.ai)")
    if MUSE_MODEL.endswith("-contributor"):
        raise RuntimeError("Refusing Contributor-tier model for chat.")
    import prompts
    messages = [{"role": "system", "content": prompts.CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": "INSPECTION REPORT:\n" + prompts.build_chat_context(report)}]
    for turn in history[-8:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})
    payload = {"model": MUSE_MODEL, "messages": messages}
    with httpx.Client(timeout=120) as client:
        resp = client.post(f"{BASE_URL}/chat/completions", json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Mock mode — deterministic, clearly synthetic. Mirrors the shape of the real
# outputs so the UI and report layers develop against the true contract.
# ---------------------------------------------------------------------------

def _mock_segments(n_frames: int) -> list[Segment]:
    base = [
        Segment("worker", "عامل", 0.97, 0, [0.12, 0.20, 0.18, 0.62]),
        Segment("worker_without_helmet", "عامل بدون خوذة", 0.91, 0, [0.55, 0.22, 0.16, 0.60]),
        Segment("guard_rail_missing", "غياب حاجز حماية", 0.88, 0, [0.70, 0.10, 0.28, 0.30]),
        Segment("forklift", "رافعة شوكية", 0.95, 0, [0.30, 0.55, 0.30, 0.35]),
    ]
    out: list[Segment] = []
    for i in range(max(1, n_frames)):
        for s in base:
            out.append(Segment(s.label, s.label_ar, s.confidence, i, list(s.bbox)))
    return out


def _mock_findings(segments: list[Segment]) -> tuple[list[Finding], str, str]:
    findings = [
        Finding(
            title_ar="عامل بدون خوذة حماية",
            title_en="Worker without a safety helmet",
            severity="high",
            detail_ar="ظهر عامل في منطقة العمل دون خوذة حماية، بينما تتحرك رافعة شوكية في نفس المنطقة.",
            detail_en="A worker appears in the work area without a safety helmet while a forklift moves through the same area.",
            action_ar="إيقاف العمل فورًا في المنطقة وتزويد العامل بمعدات الحماية الشخصية قبل استئناف العمل.",
            action_en="Stop work in the area immediately and issue the worker personal protective equipment before work resumes.",
            frame_index=0, source="both",
        ),
        Finding(
            title_ar="غياب حاجز الحماية عند الحافة",
            title_en="Missing guard rail at the edge",
            severity="high",
            detail_ar="الحافة العلوية في إطار الصورة بدون حاجز حماية، ما يشكل خطر سقوط من ارتفاع.",
            detail_en="The upper edge in the frame has no guard rail, creating a fall-from-height risk.",
            action_ar="تركيب حاجز حماية مؤقت اليوم، وحاجز دائم قبل نهاية الأسبوع.",
            action_en="Install a temporary guard rail today and a permanent one before the end of the week.",
            frame_index=0, source="segments",
        ),
        Finding(
            title_ar="مسار الرافعة غير محدد بعلامات",
            title_en="Forklift path not marked",
            severity="medium",
            detail_ar="مسار حركة الرافعة الشوكية غير محدد بعلامات أرضية، ويتقاطع مع مسار مشاة العمال.",
            detail_en="The forklift route has no floor markings and crosses the pedestrian walkway.",
            action_ar="رسم مسارات منفصلة للمشاة والرافعات بعلامات أرضية واضحة.",
            action_en="Paint clearly separated pedestrian and forklift routes with floor markings.",
            frame_index=0, source="segments",
        ),
    ]
    summary_ar = (
        "أظهر الفحص ملاحظتين عاليتي الخطورة (عامل بدون خوذة، وغياب حاجز حماية) "
        "وملاحظة متوسطة تتعلق بمسارات الحركة. يُنصح بمعالجة الملاحظات العالية قبل استئناف العمل في المنطقة."
    )
    summary_en = (
        "The inspection found two high-severity issues (a worker without a helmet "
        "and a missing guard rail) and one medium issue (unmarked forklift path). "
        "Resolve the high-severity items before work resumes in the area."
    )
    return findings, summary_ar, summary_en


def _mock_chat(report: dict, question: str) -> str:
    """Keyword-grounded sample answers over the mock report (AR + EN)."""
    q = question or ""
    arabic = any("؀" <= ch <= "ۿ" for ch in q)
    ql = q.lower()
    findings = report.get("findings", [])
    def f(i):  # 1-based finding shortcut
        return findings[i - 1] if len(findings) >= i else None
    if any(k in ql for k in ("helmet", "خوذة", "خوذه")) and f(1):
        return ("الملاحظة ١ (إطار الدليل ١) عالية الخطورة لأن العامل يعمل دون خوذة بينما تتحرك رافعة شوكية في نفس المنطقة — أي اصطدام أو سقوط جسم قد يكون قاتلًا. الإجراء المطلوب: إيقاف العمل فورًا حتى تُسلَّم معدات الحماية."
                if arabic else
                "Finding 1 (evidence frame 1) is high severity because the worker has no helmet while a forklift moves through the same area — any collision or falling object could be fatal. The corrective action is to stop work immediately until protective equipment is issued.")
    if any(k in ql for k in ("rail", "guard", "حاجز", "edge", "حافة")) and f(2):
        return ("الملاحظة ٢ (إطار الدليل ١): الحافة العلوية بلا حاجز حماية، وخطر السقوط من ارتفاع هو أكثر أسباب الوفيات شيوعًا في مواقع الإنشاء. الحل على مرحلتين: حاجز مؤقت اليوم، ودائم قبل نهاية الأسبوع."
                if arabic else
                "Finding 2 (evidence frame 1): the upper edge has no guard rail, and falls from height are the most common cause of death on construction sites. The fix is staged — a temporary rail today, a permanent one before the end of the week.")
    if any(k in ql for k in ("notice", "contractor", "خطاب", "مقاول", "draft", "صياغة")):
        return ("مسودة إشعار للمقاول:\n\nالموضوع: إجراءات تصحيحية مطلوبة — تقرير فحص BSR\n\nبناءً على فحص اليوم، المطلوب معالجة ما يلي: (١) عامل بدون خوذة حماية — إيقاف فوري للعمل في المنطقة حتى الامتثال؛ (٢) غياب حاجز حماية عند الحافة — حاجز مؤقت اليوم ودائم قبل نهاية الأسبوع؛ (٣) مسار رافعة غير محدد — رسم مسارات منفصلة للمشاة والرافعات. الأدلة: إطارات التقرير المرفقة. سيُعاد الفحص للتحقق من الإغلاق."
                if arabic else
                "Draft notice to the contractor:\n\nSubject: Required corrective actions — inspection report\n\nFollowing today's inspection, please address: (1) worker without a safety helmet — immediate stop of work in the area until compliant; (2) missing guard rail at the edge — temporary rail today, permanent before end of week; (3) unmarked forklift path — paint separated pedestrian and forklift routes. Evidence: the attached report frames. A re-inspection will verify closure.")
    if any(k in ql for k in ("summar", "ملخص", "brief", "manager", "مدير")):
        return (report.get("summary_ar") if arabic else report.get("summary_en")) or ""
    return ("أستطيع الإجابة من أدلة هذا الفحص فقط: ثلاث ملاحظات — ملاحظتان عاليتا الخطورة (عامل بدون خوذة، وغياب حاجز حماية) وواحدة متوسطة (مسار رافعة غير محدد). اسألني عن أي ملاحظة، أو اطلب صياغة إشعار للمقاول."
            if arabic else
            "I can answer from this inspection's evidence only: three findings — two high severity (worker without a helmet, missing guard rail) and one medium (unmarked forklift path). Ask me about any finding, or ask for a draft notice to the contractor.")
