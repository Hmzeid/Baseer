"""Structured inspection PDF report (Arabic-first, RTL) — not an app printout.

Built server-side with reportlab: cover block, executive summary, numbered
findings, corrective-action cases with history + notes, audit excerpt, and an
evidence appendix. Honest sourcing line on every report (mock vs live).
"""
from __future__ import annotations

import html
import io
import re
from datetime import datetime, timezone
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

NAVY = HexColor("#0A2540")
GOLD = HexColor("#C9A94E")
INK = HexColor("#131519")
MUTED = HexColor("#6E6A5C")
LINE = HexColor("#E3DED2")
SEV_COLORS = {"high": HexColor("#B3261E"), "medium": HexColor("#8A5A00"),
              "low": HexColor("#2F5D3A")}
SEV_TINTS = {"high": HexColor("#FDECEA"), "medium": HexColor("#FBF0DA"),
             "low": HexColor("#E7F2E9")}
SEV_AR = {"high": "عالية الخطورة", "medium": "متوسطة الخطورة",
          "low": "منخفضة الخطورة"}
STATUS_AR = {"open": "مفتوحة", "assigned": "مُسندة", "closed": "مغلقة"}
SRC_AR = {"segments": "النموذج البصري", "inspector": "ملاحظة المفتش",
          "both": "النموذج + ملاحظة المفتش", "vision": "النموذج البصري"}

_GEEZA = "/System/Library/Fonts/GeezaPro.ttc"


_LATIN_RUN = re.compile(r"[A-Za-z0-9]+(?:[ .,:_/\-][A-Za-z0-9]+)*")


def ar(text: object) -> str:
    """Shape + bidi-reorder Arabic for correct PDF rendering (HTML-escaped).

    The Arabic face carries no Latin glyphs, so Latin/digit runs (kept
    intact by bidi as single runs) are wrapped in Helvetica. Applied to the
    visual-order string, the wrapping never disturbs ordering.
    """
    vis = get_display(arabic_reshaper.reshape(html.escape(str(text or ""))))
    return _LATIN_RUN.sub(
        lambda m: f'<font name="Helvetica">{m.group(0)}</font>', vis)


def _fonts() -> tuple[str, str]:
    # Geeza Pro carries the Arabic presentation forms arabic_reshaper emits
    # plus full Latin/digit coverage; legacy Naskh-style fonts that expect
    # the renderer to shape render blanks here.
    try:
        registerFont(TTFont("Geeza", _GEEZA, subfontIndex=0))
        registerFont(TTFont("GeezaB", _GEEZA, subfontIndex=1))
    except Exception as exc:
        raise RuntimeError(f"arabic report fonts unavailable: {exc}")
    return "Geeza", "GeezaB"


def _styles(body: str, head: str) -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontName=head, fontSize=22,
                                leading=30, alignment=2, textColor=NAVY),
        "subtitle": ParagraphStyle("subtitle", fontName=body, fontSize=11,
                                   leading=16, alignment=2, textColor=MUTED),
        "h2": ParagraphStyle("h2", fontName=head, fontSize=15, leading=22,
                             alignment=2, textColor=NAVY, spaceBefore=14,
                             spaceAfter=6),
        "body": ParagraphStyle("body", fontName=body, fontSize=11,
                               leading=17, alignment=2, textColor=INK),
        "muted": ParagraphStyle("muted", fontName=body, fontSize=9.5,
                                leading=14, alignment=2, textColor=MUTED),
        "cell": ParagraphStyle("cell", fontName=body, fontSize=10,
                               leading=15, alignment=2, textColor=INK),
        "cellH": ParagraphStyle("cellH", fontName=head, fontSize=10,
                                leading=15, alignment=2, textColor=INK),
        "finding": ParagraphStyle("finding", fontName=head, fontSize=13,
                                  leading=19, alignment=2, textColor=NAVY),
    }


def _meta_table(st: dict, rows: list[tuple[str, str]]) -> Table:
    # RTL: value on the right, label on the left of it.
    data = [[Paragraph(ar(v), st["cell"]), Paragraph(ar(k), st["cellH"])]
            for k, v in rows]
    t = Table(data, colWidths=[11 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, -1), HexColor("#F5F3EE")),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _sev_label(sev: str) -> str:
    return SEV_AR.get(sev, sev)


def build_pdf(report: dict, audit_entries: list[dict],
              evidence_dir: Path | None) -> bytes:
    """Render the full structured report. Returns PDF bytes."""
    body, head = _fonts()
    st = _styles(body, head)
    story: list = []
    findings = report.get("findings", [])
    by_sev = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_sev[f.get("severity", "low")] = by_sev.get(f.get("severity", "low"), 0) + 1

    mode = report.get("mode", "mock")
    if mode == "live":
        src = {"sam": "تحليل مباشر — SAM 3.1",
               "vision": "تحليل مباشر — رؤية Muse"}.get(
            report.get("segmentation_source", ""), "تحليل مباشر")
    else:
        src = "بيانات تجريبية — للعرض فقط"
    try:
        when = datetime.fromisoformat(
            report.get("created_at", "").replace("Z", "+00:00"))
        when_s = when.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        when_s = report.get("created_at", "")

    story.append(Paragraph(ar("تقرير فحص سلامة ميداني"), st["title"]))
    story.append(Paragraph(ar("Baseer · بصير — Field Inspection Report"),
                           st["subtitle"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(_meta_table(st, [
        ("رقم الفحص", report.get("inspection_id", "")),
        ("التاريخ", when_s),
        ("الموقع", (report.get("site_context") or "").strip() or "عام"),
        ("مصدر التحليل", src),
        ("الملاحظات", f"{len(findings)} "
         f"(عالية {by_sev.get('high', 0)} · متوسطة {by_sev.get('medium', 0)} · "
         f"منخفضة {by_sev.get('low', 0)})"),
    ]))

    story.append(Paragraph(ar("الملخص التنفيذي"), st["h2"]))
    story.append(Paragraph(ar(report.get("summary_ar", "")), st["body"]))

    story.append(Paragraph(ar("الملاحظات"), st["h2"]))
    if not findings:
        story.append(Paragraph(ar("لا توجد ملاحظات مسجلة في هذا الفحص."),
                               st["muted"]))
    for i, f in enumerate(findings, 1):
        sev = f.get("severity", "low")
        sev_para = Paragraph(
            f'<font color="{SEV_COLORS.get(sev, INK).hexval()}">'
            f"{ar(_sev_label(sev))}</font>", st["cellH"])
        head_t = Table(
            [[Paragraph(ar(f"ملاحظة {i} — {f.get('title_ar', '')}"),
                        st["finding"]), sev_para]],
            colWidths=[12.5 * cm, 3 * cm])
        head_t.setStyle(TableStyle([
            ("BACKGROUND", (1, 0), (1, 0), SEV_TINTS.get(sev, LINE)),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ("BOX", (1, 0), (1, 0), 0.6, SEV_COLORS.get(sev, LINE)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(head_t)
        if f.get("title_en"):
            story.append(Paragraph(ar(f["title_en"]), st["muted"]))
        story.append(Paragraph(ar(f.get("detail_ar", "")), st["body"]))
        if f.get("action_ar"):
            story.append(Paragraph(
                ar("الإجراء المطلوب: ") + ar(f["action_ar"]), st["body"]))
        meta = []
        if f.get("source"):
            meta.append(SRC_AR.get(f["source"], f["source"]))
        if f.get("determination") == "uncertain":
            meta.append("تعذّر التحديد من الدليل")
        if f.get("frame_index") is not None:
            meta.append(f"الإطار {f.get('frame_index', 0) + 1}")
        if meta:
            story.append(Paragraph(ar(" · ".join(meta)), st["muted"]))

        case = f.get("case") or {}
        if case:
            cv = case.get("verification") or {}
            if cv and cv.get("suggested_resolved") is not None:
                vline = ("يُقترح: تمت الإزالة — بانتظار الاعتماد البشري"
                         if cv.get("suggested_resolved")
                         else "يُقترح: لم تُزَل — تتطلب معالجة")
                story.append(Paragraph(ar("التحقق: ") + ar(vline), st["body"]))
            cline = (f"الحالة: {STATUS_AR.get(case.get('status', 'open'), '')}"
                     + (f" · المكلَّف: {case['assignee']}"
                        if case.get("assignee") else ""))
            story.append(Paragraph(ar(cline), st["muted"]))
            for n in (case.get("notes") or []):
                story.append(Paragraph(
                    ar(f"ملاحظة [{n.get('actor', '')}]: {n.get('text', '')}"),
                    st["muted"]))
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(ar("سجل الإجراءات"), st["h2"]))
    mine = [e for e in (audit_entries or [])
            if e.get("inspection_id") == report.get("inspection_id")]
    if not mine:
        story.append(Paragraph(ar("لا توجد إجراءات مسجلة بعد."), st["muted"]))
    for e in mine:
        story.append(Paragraph(
            ar(f"{e.get('action', '')} — {e.get('actor', '')} — "
               f"{(e.get('detail') or '')[:140]}"), st["muted"]))

    if evidence_dir and evidence_dir.exists():
        imgs = sorted(p for p in evidence_dir.iterdir()
                      if p.suffix.lower() in (".jpg", ".jpeg", ".png"))[:6]
        if imgs:
            story.append(Paragraph(ar("الأدلة المصورة"), st["h2"]))
            row = []
            rows = []
            for p in imgs:
                try:
                    im = Image(str(p), width=7.5 * cm, height=5.5 * cm)
                    im._restrictSize(7.5 * cm, 5.5 * cm)
                    im.hAlign = "CENTER"
                    row.append([im, Paragraph(ar(p.name), st["muted"])])
                    if len(row) == 2:
                        rows.append(row)
                        row = []
                except Exception:
                    continue
            if row:
                while len(row) < 2:
                    row.append([Paragraph("", st["muted"]),
                                Paragraph("", st["muted"])])
                rows.append(row)
            if rows:
                t = Table(rows, colWidths=[8 * cm, 8 * cm])
                t.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(t)

    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(MUTED)
        canvas.setFont(body, 8)
        canvas.drawRightString(
            A4[0] - 2 * cm, 1.2 * cm,
            get_display(arabic_reshaper.reshape("أُنتج بواسطة بصير")))
        canvas.setFont("Helvetica", 8)
        canvas.drawString(2 * cm, 1.2 * cm,
                          f"{report.get('inspection_id', '')} - {gen} - p{doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm,
                            leftMargin=2 * cm, topMargin=2.2 * cm,
                            bottomMargin=2 * cm, title="Baseer inspection")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
