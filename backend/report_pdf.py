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
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
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


# Latin/digit runs, plus the punctuation the Arabic face has no glyph for
# (middle dot, dashes, colon, brackets, plus, percent, quotes, &, <, >):
# all render in Helvetica, else they show as tofu boxes.
_LATIN_RUN = re.compile(r"[A-Za-z0-9]+(?:[ .,:_/\-][A-Za-z0-9]+)*|[·—–:•()+%\[\]!?;&<>\"']+")


def ar(text: object) -> str:
    """Shape + bidi-reorder Arabic for correct PDF rendering (HTML-escaped).

    The Arabic face carries no Latin glyphs, so Latin/digit runs (kept
    intact by bidi as single runs) are wrapped in Helvetica. Applied to the
    visual-order string, the wrapping never disturbs ordering. Each piece is
    escaped after splitting, so "&" or "<" in user text can never break the
    paragraph markup.
    """
    vis = get_display(arabic_reshaper.reshape(str(text or "")))
    out, pos = [], 0
    for m in _LATIN_RUN.finditer(vis):
        out.append(html.escape(vis[pos:m.start()]))
        out.append(f'<font name="Helvetica">{html.escape(m.group(0))}</font>')
        pos = m.end()
    out.append(html.escape(vis[pos:]))
    return "".join(out)


_HAZARD_HINTS = ("without", "missing", "no_", "_no")


def annotate_frame(blob: bytes, segments: list[dict]) -> bytes:
    """Draw SAM 3.1 segment boxes + labels on one evidence frame (JPEG out).

    Boxes are normalized [x, y, w, h]; hazard-type labels draw red, objects
    blue. Returns the original bytes untouched when nothing is drawable.
    """
    from PIL import Image as PILImage, ImageDraw, ImageFont
    boxes = [s for s in segments if len(s.get("bbox") or []) == 4]
    if not boxes:
        return blob
    img = PILImage.open(io.BytesIO(blob)).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    stroke = max(2, round(min(W, H) / 220))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(14, round(min(W, H) / 32)))
    except Exception:
        font = ImageFont.load_default()
    for seg in boxes:
        x, y, w, h = seg["bbox"]
        x0, y0, x1, y1 = x * W, y * H, (x + w) * W, (y + h) * H
        label = str(seg.get("label", "")).replace("_", " ")
        color = (210, 59, 44) if any(k in str(seg.get("label", "")).lower() for k in _HAZARD_HINTS) else (47, 111, 228)
        draw.rectangle([x0, y0, x1, y1], outline=color, width=stroke)
        tb = draw.textbbox((0, 0), label, font=font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        ty = y0 - th - 2 * stroke if y0 - th - 2 * stroke > 0 else y0
        draw.rectangle([x0, ty, x0 + tw + 4 * stroke, ty + th + 2 * stroke], fill=color)
        draw.text((x0 + 2 * stroke, ty + stroke - tb[1]), label, fill=(255, 255, 255), font=font)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


BODY_W = 16.4 * cm  # A4 minus the 2 cm margins, with a little slack


def arp(text: object, style: ParagraphStyle, width: float = BODY_W) -> str:
    """Multi-line Arabic paragraph: wrap in reading order, then bidi each line.

    Reordering a whole paragraph before reportlab wraps it puts the lines in
    reverse (the sentence starts on the last line). Measuring the shaped words
    against the paragraph width and reordering line by line keeps them top-down.
    """
    lines, cur = [], ""
    for word in str(text or "").split():
        cand = f"{cur} {word}".strip()
        if cur and stringWidth(arabic_reshaper.reshape(cand), style.fontName, style.fontSize) > width:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return "<br/>".join(ar(line) for line in lines)


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
    story.append(Paragraph(ar("Baseer · بصير by Veebase — Field Inspection Report"),
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
    story.append(Paragraph(arp(report.get("summary_ar", ""), st["body"]), st["body"]))

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
            colWidths=[12.0 * cm, 3.5 * cm])
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
        story.append(Paragraph(arp(f.get("detail_ar", ""), st["body"]), st["body"]))
        if f.get("action_ar"):
            story.append(Paragraph(
                arp("الإجراء المطلوب: " + f["action_ar"], st["body"]), st["body"]))
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
                story.append(Paragraph(arp("التحقق: " + vline, st["body"]), st["body"]))
            cline = (f"الحالة: {STATUS_AR.get(case.get('status', 'open'), '')}"
                     + (f" · المكلَّف: {case['assignee']}"
                        if case.get("assignee") else ""))
            story.append(Paragraph(arp(cline, st["muted"]), st["muted"]))
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
        files = sorted(p for p in evidence_dir.iterdir() if p.is_file())
        # Frame index -> image: extract_frames emits one frame per image in
        # upload order, but a video emits several, so mapping stops there.
        frame_of, idx = {}, 0
        for p in files:
            if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                break
            frame_of[p] = idx
            idx += 1
        imgs = [p for p in files if p.suffix.lower() in (".jpg", ".jpeg", ".png")][:6]
        segs = report.get("segments") or []
        src = report.get("segmentation_source", "")
        # Only real SAM output is drawn; demo segments are synthetic boxes.
        seg_caption = "مقاطع SAM 3.1" if src == "sam" else ""
        if imgs:
            story.append(Paragraph(ar("الأدلة المصورة"), st["h2"]))
            row = []
            rows = []
            for p in imgs:
                try:
                    frame_segs = [sg for sg in segs if p in frame_of and sg.get("frame_index") == frame_of[p]]
                    caption = p.name
                    if frame_segs and seg_caption:
                        im = Image(io.BytesIO(annotate_frame(p.read_bytes(), frame_segs)),
                                   width=7.5 * cm, height=5.5 * cm)
                        caption = f"{p.name} · {seg_caption} ({len(frame_segs)})"
                    else:
                        im = Image(str(p), width=7.5 * cm, height=5.5 * cm)
                    im._restrictSize(7.5 * cm, 5.5 * cm)
                    im.hAlign = "CENTER"
                    row.append([im, Paragraph(ar(caption), st["muted"])])
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
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, "Baseer by Veebase")
        canvas.drawString(2 * cm, 1.2 * cm,
                          f"{report.get('inspection_id', '')} - {gen} - p{doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm,
                            leftMargin=2 * cm, topMargin=2.2 * cm,
                            bottomMargin=2 * cm, title="Baseer inspection", author="Baseer by Veebase",
                            creator="Baseer by Veebase")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
