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
    DAY-0 VERDICT (Oct 26): Chat Completions returned 404 for sam-3.1.
    OCT 27 CORRECTION: the 404 was the wrong surface, not a team gate —
    sam-3.1 is listed by GET /v1/models and answers on the Responses API,
    so segment_frames() below uses POST /v1/responses. Fallback stays:
    when SAM is unreachable, Muse reads the frames directly
    (reason_from_frames, prompts.VISION_SYSTEM_PROMPT).
    Pipeline selects via env BASEER_SEGMENTATION: "auto" (default — try SAM,
    fall back to vision on the 404), "sam" (never fall back), "vision"
    (skip SAM entirely). The report records which source was used.

Modes via env BASEER_MODE: "mock" (default, deterministic samples) / "live".
ALL Meta-specific shaping stays in this file.
"""
from __future__ import annotations

import base64
import os
import re
from dataclasses import asdict, dataclass, field

import httpx

# Load .env (backend/ then repo root) BEFORE reading any env vars, so the
# app picks up MODEL_API_KEY from the checkout's .env without the caller
# having to export it. Real environment variables always win; values are
# never printed. .env is git-ignored, so the key stays local.
def _load_dotenv() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (os.path.join(here, ".env"),
                      os.path.join(os.path.dirname(here), ".env")):
        if not os.path.exists(candidate):
            continue
        with open(candidate, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
        return


_load_dotenv()

MODE = os.getenv("BASEER_MODE", "mock").lower()
BASE_URL = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1")
API_KEY = os.getenv("MODEL_API_KEY", "") or os.getenv("META_API_KEY", "")
MUSE_MODEL = os.getenv("MUSE_MODEL", "muse-spark-1.3")
SAM_MODEL = os.getenv("SAM_MODEL", "sam-3.1")
SEGMENTATION = os.getenv("BASEER_SEGMENTATION", "auto").lower()  # auto | sam | vision

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
    source: str = "segments"        # segments | inspector | both | vision
    visually_confirmed: bool = True
    determination: str = "confirmed"  # confirmed | uncertain (prompt rule 9)


def _headers() -> dict:
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


_BOX_RE = re.compile(
    r"<\|box;x1=(?P<x1>\d+);y1=(?P<y1>\d+);x2=(?P<x2>\d+);y2=(?P<y2>\d+)"
    r"(?:;w=(?P<w>\d+);h=(?P<h>\d+))?\|>")


def parse_sam_output(text: str, concept: str, frame_index: int) -> list[Segment]:
    """Parse SAM 3.1 special-token output records into Segments.

    Boxes arrive as <|box;x1=..;y1=..;x2=..;y2=..;w=..;h=..|>; masks as
    <|mask;...data=<H>,<W>,<base85 payload>|> ('~' prefix = lossless,
    '!' = one-bit). Mask payloads are deliberately NOT stored — a single
    frame's lane can exceed 300KB of base85, and boxes + labels are enough
    for reasoning input. Mask decoding for evidence overlays lands in the
    Oct 26-27 build (the third-party `meta-sam-parser` package implements
    the same format).
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


def _post_with_retry(client: "httpx.Client", url: str, payload: dict,
                     headers: dict, what: str = "analysis"):
    """POST with backoff on 429/5xx. Video uploads fire dozens of calls in
    a burst; without this the provider throttles us and the user gets a 500
    after half a minute of silence. Honors Retry-After when present."""
    import time as _time
    import httpx as _httpx
    delay = 2.0
    for attempt in range(5):
        resp = client.post(url, json=payload, headers=headers)
        if resp.status_code == 404:
            return resp  # enablement signal — callers translate it, never retry
        if resp.status_code != 429 and resp.status_code < 500:
            return resp
        retry_after = resp.headers.get("retry-after")
        try:
            wait = float(retry_after) if retry_after else delay
        except ValueError:
            wait = delay
        if attempt == 4:
            raise _httpx.HTTPStatusError(
                f"{what} is rate-limited right now (429 after retries) — "
                "try again in a minute", request=resp.request, response=resp)
        _time.sleep(min(wait, 30))
        delay *= 2
    raise RuntimeError(f"{what} failed after retries")  # unreachable


def _responses_text(resp_json: dict) -> str:
    """Extract SAM's special-token lane from a Responses API object.

    Segmentation output arrives as output_text parts inside message items
    (one line per frame: <Nf>id<|box;...|><|mask;...|> records). An absent
    concept completes with empty output_text — a normal zero-match result,
    not an error.
    """
    texts = []
    for item in resp_json.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for part in item.get("content", []) or []:
            if part.get("type") == "output_text" and part.get("text"):
                texts.append(part["text"])
    return "\n".join(texts)


def segment_frames(frames: list[bytes]) -> list[Segment]:
    """Run SAM 3.1 segmentation over extracted frames.

    SAM 3.1 is served ONLY on the Responses API (/v1/responses) — the Chat
    Completions shape 404s for it. Hosted SAM takes ONE text concept per
    call, so this loops concepts x frames. A 404 means SAM is not enabled
    for the team — surface it loudly (auto mode falls back to vision).
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
                    "input": [{
                        "type": "message",
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": concept},
                            {"type": "input_image", "image_url": image_url},
                        ],
                    }],
                }
                import time as _t
                _t.sleep(0.4)  # stagger the concept x frame burst
                resp = _post_with_retry(client, f"{BASE_URL}/responses",
                                        payload, _headers(), "segmentation")
                if resp.status_code == 404:
                    raise RuntimeError(
                        "SAM 3.1 returned 404 model_not_found — the model is "
                        "not enabled for this team/key yet. Check dev.meta.ai.")
                resp.raise_for_status()
                text = _responses_text(resp.json())
                segments.extend(parse_sam_output(text, concept, idx))
    return segments


def reason_findings(segments: list[Segment], inspector_notes: str,
                    site_context: str = "") -> tuple[list[Finding], str, str]:
    """Muse Spark reasons over segments + inspector notes.

    Returns (findings, summary_ar, summary_en).
    """
    if MODE != "live":
        return _mock_findings(segments, site_context)
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
        resp = _post_with_retry(client, f"{BASE_URL}/chat/completions", payload, _headers())
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    import json
    parsed = json.loads(content)
    known = {f.name for f in Finding.__dataclass_fields__.values()}
    findings = [Finding(**{k: v for k, v in f.items() if k in known})
                for f in parsed["findings"]]
    return findings, parsed["summary_ar"], parsed["summary_en"]


def reason_from_frames(frames: list[bytes], inspector_notes: str,
                       site_context: str = "") -> tuple[list[Finding], str, str]:
    """Vision fallback: Muse reads the frames directly (no SAM segments).

    Same Finding contract as reason_findings, except findings carry
    source "vision" and describe their region in words (no boxes exist).
    Used when SAM 3.1 is unreachable (404 fallback in auto mode) and when
    BASEER_SEGMENTATION=vision. The caller labels each image with its
    frame index so findings can cite frame_index correctly.
    """
    if MODE != "live":
        return _mock_findings([], site_context)
    if not frames:
        raise RuntimeError("vision reasoning needs at least one frame")
    if not API_KEY:
        raise RuntimeError("live mode requires MODEL_API_KEY (create one at dev.meta.ai)")
    if MUSE_MODEL.endswith("-contributor"):
        raise RuntimeError(
            "Refusing Contributor-tier model: Meta may train on its prompts. "
            "Use the Standard muse-spark-1.3.")
    import prompts
    content: list[dict] = []
    for idx, frame in enumerate(frames):
        image_url = "data:image/jpeg;base64," + base64.b64encode(frame).decode()
        content.append({"type": "text", "text": f"Frame {idx}:"})
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompts.build_vision_prompt(
        inspector_notes, site_context)})
    payload = {
        "model": MUSE_MODEL,
        "messages": [
            {"role": "system", "content": prompts.VISION_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=180) as client:
        resp = _post_with_retry(client, f"{BASE_URL}/chat/completions", payload, _headers())
        resp.raise_for_status()
        data = resp.json()
    content_text = data["choices"][0]["message"]["content"]
    import json
    parsed = json.loads(content_text)
    known = {f.name for f in Finding.__dataclass_fields__.values()}
    findings = [Finding(**{k: v for k, v in f.items() if k in known})
                for f in parsed["findings"]]
    return findings, parsed["summary_ar"], parsed["summary_en"]


def verify_finding(finding: dict) -> dict:
    """Verify step: would a re-inspection clear this finding?

    Live mode never suggests resolution without new evidence: the real check
    is compare_for_verification on an after-photo/video. Mock mode returns the
    staged demo outcome — the flagship PPE finding resolves; the
    floor-marking finding deliberately does NOT, so the demo shows an honest
    mixed result.
    """
    title = (finding.get("title_en") or "").lower()
    if MODE == "live":
        note_en = "No re-inspection evidence yet: attach an after-photo of the same spot to verify the fix."
        note_ar = "لا توجد أدلة إعادة فحص بعد: أرفق صورة لاحقة للموقع نفسه للتحقق من الإصلاح."
        return {"suggested_resolved": False, "note": note_en,
                "note_en": note_en, "note_ar": note_ar}
    if "forklift path" in title or "markings" in title:
        return {"suggested_resolved": False,
                "note": "Re-inspection still shows no floor markings on the forklift route."}
    return {"suggested_resolved": True,
            "note": "Re-inspection evidence shows the violation corrected (demo simulation)."}


def compare_for_verification(finding: dict, after_frames: list[bytes]) -> dict:
    """Compare AFTER photo/video frames against ONE finding.

    Returns {"suggested_resolved": bool, "note": str, "note_ar": str,
    "note_en": str}. The verdict only ever suggests — the case endpoint
    still requires a human approve step before closure. With no after
    frames, falls back to the conservative no-evidence verdict.
    """
    if MODE != "live":
        title = (finding.get("title_en") or "").lower()
        if "forklift path" in title or "markings" in title:
            return {"suggested_resolved": False,
                    "note": "Re-inspection still shows no floor markings on the forklift route.",
                    "note_ar": "ما زالت إعادة الفحص تُظهر غياب العلامات الأرضية على مسار الرافعة.",
                    "note_en": "Re-inspection still shows no floor markings on the forklift route."}
        return {"suggested_resolved": True,
                "note": "Re-inspection evidence shows the violation corrected (demo simulation).",
                "note_ar": "تُظهر أدلة إعادة الفحص تصحيح المخالفة (محاكاة تجريبية).",
                "note_en": "Re-inspection evidence shows the violation corrected (demo simulation)."}
    if not after_frames:
        return verify_finding(finding)
    if not API_KEY:
        raise RuntimeError("live mode requires MODEL_API_KEY (create one at dev.meta.ai)")
    if MUSE_MODEL.endswith("-contributor"):
        raise RuntimeError("Refusing Contributor-tier model for verification.")
    import prompts
    content: list[dict] = []
    for idx, frame in enumerate(after_frames):
        image_url = "data:image/jpeg;base64," + base64.b64encode(frame).decode()
        content.append({"type": "text", "text": f"After frame {idx}:"})
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompts.build_verify_prompt(finding)})
    payload = {
        "model": MUSE_MODEL,
        "messages": [
            {"role": "system", "content": prompts.VERIFY_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=180) as client:
        resp = _post_with_retry(client, f"{BASE_URL}/chat/completions", payload, _headers())
        resp.raise_for_status()
        data = resp.json()
    import json
    parsed = json.loads(data["choices"][0]["message"]["content"])
    resolved = bool(parsed.get("suggested_resolved", False))
    note_en = str(parsed.get("note_en", ""))
    note_ar = str(parsed.get("note_ar", ""))
    return {"suggested_resolved": resolved,
            "note": note_en or note_ar,
            "note_ar": note_ar,
            "note_en": note_en}


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
        resp = _post_with_retry(client, f"{BASE_URL}/chat/completions", payload, _headers())
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


# Site-keyed mock scenes so a demo across sites reads like different
# walkthroughs. Any context without a construction/farm keyword (including
# "factory" and empty) gets the original factory scene, unchanged.
_MOCK_SCENES: dict[str, tuple[list[Finding], str, str]] = {
    "construction": (
        [
            Finding(
                title_ar="عامل على السقالة دون حزام أمان",
                title_en="Worker on scaffolding without a safety harness",
                severity="high",
                detail_ar="يظهر عامل على منصة السقالة العلوية دون حزام أمان مثبت بنقطة تثبيت، على ارتفاع يتجاوز طابقين.",
                detail_en="A worker stands on the upper scaffold platform, more than two storeys up, with no harness tied off to an anchor point.",
                action_ar="إيقاف العمل على الارتفاع حتى يُزوَّد العامل بحزام أمان كامل ونقطة تثبيت معتمدة.",
                action_en="Stop work at height until the worker has a full-body harness tied off to an approved anchor.",
                frame_index=0, source="both",
            ),
            Finding(
                title_ar="غياب لوح الحافة على منصة السقالة",
                title_en="Missing toe board on scaffold platform",
                severity="medium",
                detail_ar="منصة السقالة بلا لوح حافة، ما يسمح بسقوط الأدوات والمواد على العاملين في الأسفل.",
                detail_en="The scaffold platform has no toe board, so tools and materials can fall onto workers below.",
                action_ar="تركيب ألواح الحافة على كل المنصات العاملة وتطويق المنطقة أسفل السقالة.",
                action_en="Fit toe boards on every working platform and cordon off the area below the scaffold.",
                frame_index=0, source="segments",
            ),
            Finding(
                title_ar="مواد مكدسة قرب حافة البلاطة",
                title_en="Materials stacked near the slab edge",
                severity="low",
                detail_ar="حديد تسليح مكدس على بعد أقل من متر من حافة البلاطة المفتوحة.",
                detail_en="Rebar is stacked less than a metre from the open slab edge.",
                action_ar="نقل المواد إلى مسافة مترين على الأقل من الحافة وتحديد منطقة تخزين.",
                action_en="Move materials at least two metres back from the edge and mark a storage zone.",
                frame_index=0, source="segments",
            ),
        ],
        "رُصدت ملاحظة عالية الخطورة (عامل على السقالة دون حزام أمان)، وملاحظة متوسطة (غياب لوح الحافة)، "
        "وملاحظة منخفضة تتعلق بتخزين المواد قرب الحافة. يجب إيقاف العمل على الارتفاع حتى تُعالج الملاحظة العالية.",
        "One high-severity issue (a worker on scaffolding without a harness), one medium "
        "(missing toe board) and one low (materials stacked near the slab edge). Stop work at "
        "height until the high-severity item is resolved.",
    ),
    "farm": (
        [
            Finding(
                title_ar="عامل يرش المبيدات دون كمامة واقية",
                title_en="Worker spraying pesticide without a respirator",
                severity="high",
                detail_ar="عامل يرش المبيدات داخل البيت المحمي دون كمامة أو نظارات واقية.",
                detail_en="A worker sprays pesticide inside the greenhouse with no respirator or goggles.",
                action_ar="إيقاف الرش فورًا وتزويد العامل بكمامة بفلتر كيميائي ونظارات واقية.",
                action_en="Stop spraying immediately and issue a chemical-cartridge respirator and goggles.",
                frame_index=0, source="both",
            ),
            Finding(
                title_ar="جرار يعمل قرب العمال دون مراقب",
                title_en="Tractor operating close to workers without a spotter",
                severity="medium",
                detail_ar="جرار يتحرك بين صفوف العمل على مسافة قريبة من عمال الحصاد دون مراقب أرضي.",
                detail_en="A tractor moves between rows close to harvest workers with no ground spotter.",
                action_ar="تعيين مراقب أرضي وتحديد مسافة أمان لا تقل عن خمسة أمتار.",
                action_en="Assign a ground spotter and enforce a minimum five-metre safety distance.",
                frame_index=0, source="segments",
            ),
        ],
        "رُصدت ملاحظة عالية الخطورة (رش مبيدات دون كمامة) وملاحظة متوسطة (جرار قرب العمال دون مراقب). "
        "يجب إيقاف الرش حتى تُوفَّر معدات الوقاية.",
        "One high-severity issue (pesticide spraying without a respirator) and one medium "
        "(tractor near workers without a spotter). Stop spraying until protective equipment is issued.",
    ),
}


def _mock_scene(site_context: str) -> str:
    ctx = (site_context or "").lower()
    if any(k in ctx for k in ("construction", "scaffold", "building", "إنشاء", "بناء")):
        return "construction"
    if any(k in ctx for k in ("farm", "greenhouse", "agri", "مزرعة", "زراع")):
        return "farm"
    return "factory"


def _mock_findings(segments: list[Segment], site_context: str = "") -> tuple[list[Finding], str, str]:
    scene = _mock_scene(site_context)
    if scene in _MOCK_SCENES:
        findings, summary_ar, summary_en = _MOCK_SCENES[scene]
        return [Finding(**asdict(f)) for f in findings], summary_ar, summary_en
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
            title_ar="مسار الرافعة بلا علامات أرضية",
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


_AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_SEV_AR = {"high": "عالية", "medium": "متوسطة", "low": "منخفضة"}
_ORDINALS = {"first": 1, "second": 2, "third": 3, "الأولى": 1, "الثانية": 2, "الثالثة": 3}


def _mock_chat(report: dict, question: str) -> str:
    """Grounded sample answers built from the report's own findings (AR + EN):
    a named or numbered finding is explained, a notice is drafted, a summary
    is returned — never anything the report does not contain."""
    q = question or ""
    arabic = any("\u0600" <= ch <= "\u06FF" for ch in q)
    ql = q.lower()
    findings = report.get("findings", [])

    def n_ar(n: int) -> str:
        return str(n).translate(_AR_DIGITS)

    if any(k in ql for k in ("notice", "contractor", "draft", "خطاب", "مقاول", "إشعار", "اشعار", "صياغة", "صغ")):
        if arabic:
            items = "؛ ".join(f"({n_ar(i + 1)}) {f.get('title_ar', '')} — {f.get('action_ar', '').rstrip('.')}"
                             for i, f in enumerate(findings))
            return ("مسودة إشعار للمقاول:\n\nالموضوع: إجراءات تصحيحية مطلوبة — تقرير الفحص "
                    f"{report.get('inspection_id', '')}\n\nبناءً على فحص اليوم، المطلوب معالجة ما يلي: {items}. "
                    "الأدلة: إطارات التقرير المرفقة. سيُعاد الفحص للتحقق من الإغلاق.")
        items = "; ".join(f"({i + 1}) {f.get('title_en', '').lower()} — {f.get('action_en', '').rstrip('.')}"
                          for i, f in enumerate(findings))
        return ("Draft notice to the contractor:\n\nSubject: Required corrective actions — inspection "
                f"{report.get('inspection_id', '')}\n\nFollowing today's inspection, please address: {items}. "
                "Evidence: the attached report frames. A re-inspection will verify closure.")
    if any(k in ql for k in ("summar", "brief", "manager", "ملخص", "لخّص", "لخص", "مدير")):
        return (report.get("summary_ar") if arabic else report.get("summary_en")) or ""

    target = None
    for word, n in _ORDINALS.items():
        if word in ql and n <= len(findings):
            target = n - 1
    for i in range(len(findings)):
        if any(p in ql for p in (f"finding {i + 1}", f"#{i + 1}", f"الملاحظة {i + 1}", f"الملاحظة {n_ar(i + 1)}")):
            target = i
    if target is None:
        best = 0
        for i, f in enumerate(findings):
            words = [w for w in (f.get("title_en", "").lower().split() + f.get("title_ar", "").split()) if len(w) > 3]
            hits = sum(1 for w in words if w in ql or w in q)
            if hits > best:
                best, target = hits, i
    if target is not None:
        f = findings[target]
        frame = f.get("frame_index", 0) + 1
        if arabic:
            return (f"الملاحظة {n_ar(target + 1)} (إطار الدليل {n_ar(frame)}): «{f.get('title_ar', '')}» — "
                    f"خطورتها {_SEV_AR.get(f.get('severity'), '')} لأن {f.get('detail_ar', '')}\n\n"
                    f"الإجراء المطلوب: {f.get('action_ar', '')}")
        return (f"Finding {target + 1} (evidence frame {frame}), \"{f.get('title_en', '')}\", is "
                f"{f.get('severity', '')} severity: {f.get('detail_en', '')}\n\n"
                f"Corrective action: {f.get('action_en', '')}")
    if arabic:
        listing = "، ".join(f"{f.get('title_ar', '')} ({_SEV_AR.get(f.get('severity'), '')})" for f in findings)
        return (f"أستطيع الإجابة من أدلة هذا الفحص فقط: {n_ar(len(findings))} ملاحظات — {listing}. "
                "اسألني عن أي ملاحظة، أو اطلب صياغة إشعار للمقاول.")
    listing = ", ".join(f"{f.get('title_en', '').lower()} ({f.get('severity', '')})" for f in findings)
    return (f"I can answer from this inspection's evidence only: {len(findings)} findings — {listing}. "
            "Ask me about any finding, or ask for a draft notice to the contractor.")
