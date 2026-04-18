"""
Professional PDF Report Generator for IA Validation Reports
Generates well-structured, clean PDFs with proper spacing and layout.

Key design principles:
  - Large leading values to prevent line overlap
  - Generous spacing between sections
  - KeepTogether blocks to prevent orphaned headings
  - Direct, assertive IA conclusions (no Q&A format)
  - Professional table styling with alternating rows
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect


# ═══════════════════════════════════════════════════════════════════
# Color palette — Neo-Sousse branding
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    "primary": colors.HexColor("#0f766e"),
    "primary_light": colors.HexColor("#14b8a6"),
    "primary_dark": colors.HexColor("#0d4f4a"),
    "accent": colors.HexColor("#3b82f6"),
    "accent_light": colors.HexColor("#93c5fd"),
    "success": colors.HexColor("#22c55e"),
    "success_bg": colors.HexColor("#f0fdf4"),
    "warning": colors.HexColor("#f59e0b"),
    "warning_bg": colors.HexColor("#fffbeb"),
    "danger": colors.HexColor("#ef4444"),
    "danger_bg": colors.HexColor("#fef2f2"),
    "dark": colors.HexColor("#0f172a"),
    "text": colors.HexColor("#1e293b"),
    "text_light": colors.HexColor("#64748b"),
    "text_muted": colors.HexColor("#94a3b8"),
    "border": colors.HexColor("#e2e8f0"),
    "border_light": colors.HexColor("#f1f5f9"),
    "bg_light": colors.HexColor("#f8fafc"),
    "bg_section": colors.HexColor("#f1f5f9"),
    "white": colors.white,
}


def _get_styles():
    """Professional PDF styles with generous spacing to prevent overlapping."""
    styles = getSampleStyleSheet()

    # ── Cover Page Styles ──
    styles.add(ParagraphStyle(
        name='CoverBrand',
        fontName='Helvetica-Bold',
        fontSize=36,
        textColor=COLORS["primary"],
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=44,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubBrand',
        fontName='Helvetica',
        fontSize=13,
        textColor=COLORS["text_light"],
        alignment=TA_CENTER,
        spaceAfter=35,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name='CoverReportTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=COLORS["dark"],
        alignment=TA_CENTER,
        spaceAfter=14,
        leading=30,
    ))

    # ── Section Styles ──
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=COLORS["primary"],
        spaceBefore=24,
        spaceAfter=10,
        leading=20,
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=COLORS["primary_dark"],
        spaceBefore=16,
        spaceAfter=8,
        leading=16,
    ))

    # ── Body Styles ──
    styles.add(ParagraphStyle(
        name='BodyPro',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["text"],
        alignment=TA_JUSTIFY,
        leading=18,
        spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name='BodyReport',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["text"],
        alignment=TA_LEFT,
        leading=18,
        spaceAfter=14,
        leftIndent=10,
    ))
    styles.add(ParagraphStyle(
        name='BulletItem',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["text"],
        alignment=TA_LEFT,
        leading=18,
        spaceAfter=8,
        leftIndent=20,
        bulletIndent=10,
    ))
    styles.add(ParagraphStyle(
        name='SmallNote',
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        textColor=COLORS["text_light"],
        alignment=TA_LEFT,
        leading=12,
        spaceAfter=4,
    ))

    # ── Badge / Decision Styles ──
    styles.add(ParagraphStyle(
        name='BadgeText',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=COLORS["white"],
        alignment=TA_CENTER,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        name='DecisionApproved',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLORS["success"],
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=8,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name='DecisionConditional',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLORS["warning"],
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=8,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name='DecisionRejected',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLORS["danger"],
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=8,
        leading=18,
    ))

    # ── Metric Styles ──
    styles.add(ParagraphStyle(
        name='MetricValue',
        fontName='Helvetica-Bold',
        fontSize=24,
        alignment=TA_CENTER,
        leading=30,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='MetricLabel',
        fontName='Helvetica',
        fontSize=9,
        textColor=COLORS["text_light"],
        alignment=TA_CENTER,
        leading=12,
    ))

    return styles


def _header_footer(canvas, doc):
    """Professional header and footer on each page."""
    canvas.saveState()
    w, h = A4

    # ── Header line ──
    canvas.setStrokeColor(COLORS["primary"])
    canvas.setLineWidth(2.5)
    canvas.line(36, h - 36, w - 36, h - 36)

    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(COLORS["primary"])
    canvas.drawString(36, h - 30, "NEO-SOUSSE SMART CITY 2030")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(COLORS["text_light"])
    canvas.drawRightString(w - 36, h - 30, f"Rapport IA — {datetime.now().strftime('%d/%m/%Y')}")

    # ── Footer ──
    canvas.setStrokeColor(COLORS["border"])
    canvas.setLineWidth(0.5)
    canvas.line(36, 42, w - 36, 42)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(COLORS["text_light"])
    canvas.drawString(36, 30, "Neo-Sousse Smart City — Plateforme IoT Intelligente — Rapport IA Generatif")
    canvas.drawRightString(w - 36, 30, f"Page {doc.page}")

    canvas.setFont("Helvetica-Oblique", 6)
    canvas.setFillColor(COLORS["text_muted"])
    canvas.drawCentredString(w / 2, 18, "Document confidentiel — Usage interne uniquement — Module IA Generative v2.3")

    canvas.restoreState()


def _sanitize_text(text: str) -> str:
    """Remove emojis and special chars that Helvetica cannot render."""
    if not text:
        return ""
    emoji_chars = [
        '📊', '📋', '📡', '🔧', '🚗', '👥', '💡', '⚠️', '✅', '🔴', '🟢', '🟡',
        '🤖', '📄', '⬇️', '🔄', '🏆', '⭐', '🚨', '⏱️', '📶', '🧠', '⚡',
        '🔵', '🟠', '📈', '📉', '🎯', '🔔', '🌿', '🚙', '🗺️', '🛠️', '🔍', '📝',
        '❌', '✔️', '☑️', '🏙️', '👷',
    ]
    for e in emoji_chars:
        text = text.replace(e, '')
    # Strip markdown formatting artifacts
    text = text.replace('**', '').replace('##', '').replace('###', '')
    text = text.replace('# ', '')
    return text.strip()


def _format_paragraphs(text: str, style, elems: list):
    """Split text into clean paragraphs and append to elems list.
    
    Handles newlines, pipe separators, and cleans up formatting.
    Each paragraph gets proper spacing to avoid overlap.
    """
    if not text or not text.strip():
        return

    clean = _sanitize_text(text)

    # Split by pipe separator (used by validator reasoning)
    if ' | ' in clean:
        parts = clean.split(' | ')
    else:
        parts = clean.split('\n')

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Convert any remaining <br/> tags
        part = part.replace('<br/>', ' ')
        part = part.replace('<br>', ' ')
        # Clean up multiple spaces
        while '  ' in part:
            part = part.replace('  ', ' ')
        if part:
            elems.append(Paragraph(part, style))


def _build_score_badge(score, styles):
    """Build a colored score badge based on numeric value."""
    try:
        s = int(score)
    except (ValueError, TypeError):
        s = 0

    if s >= 75:
        color = COLORS["success"]
        label = "EXCELLENT"
    elif s >= 55:
        color = COLORS["accent"]
        label = "BON"
    elif s >= 35:
        color = COLORS["warning"]
        label = "ACCEPTABLE"
    else:
        color = COLORS["danger"]
        label = "INSUFFISANT"

    return f"{score}/100 ({label})", color


def _build_metric_cell(value: str, label: str, color, styles):
    """Build a single metric cell for embedding in a table."""
    content = (
        f"<font size='20' color='{color.hexval()}'><b>{value}</b></font><br/>"
        f"<font size='8' color='#64748b'>{label}</font>"
    )
    return Paragraph(content, ParagraphStyle(
        f'mc_{label}', fontName='Helvetica',
        fontSize=10, alignment=TA_CENTER, leading=26,
    ))


def generate_ia_pdf(intervention: dict, tech1_report: str, tech2_report: str, validation: dict) -> bytes:
    """
    Generate a professional PDF for IA validation of an intervention.
    
    This PDF includes:
    - Professional cover page with Neo-Sousse branding
    - Key metrics dashboard (scores, confidence)
    - Intervention summary table
    - Technician reports in structured sections
    - IA analysis results (direct conclusions, NO questions)
    - Decision and confidence score
    - Professional conclusion
    
    Returns PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=36, leftMargin=36,
        topMargin=58, bottomMargin=58,
        title=f"Validation IA — Intervention #{intervention.get('IDIn', '')}",
        author="Neo-Sousse Smart City — Module IA Generative v2.3",
    )

    styles = _get_styles()
    w, h = A4
    elems = []

    # ── Extract validation data ──
    conf = validation.get('confidence', 0) if isinstance(validation, dict) else 0
    score1 = validation.get('tech1_score', '—') if isinstance(validation, dict) else '—'
    score2 = validation.get('tech2_score', '—') if isinstance(validation, dict) else '—'
    avg_score = validation.get('average_score', 0) if isinstance(validation, dict) else 0
    quality1 = validation.get('tech1_quality', 'N/A') if isinstance(validation, dict) else 'N/A'
    quality2 = validation.get('tech2_quality', 'N/A') if isinstance(validation, dict) else 'N/A'
    approval = validation.get('approval_level', '—') if isinstance(validation, dict) else '—'
    reasoning = validation.get('reasoning', '') if isinstance(validation, dict) else ''

    # ══════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════

    elems.append(Spacer(1, 80))

    # Decorative top bar
    d = Drawing(w - 72, 5)
    d.add(Rect(0, 0, w - 72, 5, fillColor=COLORS["primary"], strokeColor=None))
    elems.append(d)
    elems.append(Spacer(1, 50))

    # Brand
    elems.append(Paragraph("NEO-SOUSSE", styles['CoverBrand']))
    elems.append(Paragraph("SMART CITY 2030", styles['CoverSubBrand']))

    # Separator line
    d2 = Drawing(220, 2)
    d2.add(Rect(0, 0, 220, 2, fillColor=COLORS["primary_light"], strokeColor=None))
    elems.append(d2)
    elems.append(Spacer(1, 35))

    # Report title
    elems.append(Paragraph(
        f"Validation IA - Intervention #{intervention.get('IDIn', '')}",
        styles['CoverReportTitle']
    ))
    elems.append(Spacer(1, 8))

    # Type badge
    badge_data = [[Paragraph("  VALIDATION INTERVENTION  ", styles['BadgeText'])]]
    badge_tbl = Table(badge_data, colWidths=[220])
    badge_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS["primary"]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    elems.append(badge_tbl)
    elems.append(Spacer(1, 45))

    # Metadata table
    date_str = datetime.now().strftime('%d/%m/%Y a %H:%M')
    intv_date = intervention.get('DateHeure', '')
    if hasattr(intv_date, 'strftime'):
        intv_date = intv_date.strftime('%d/%m/%Y %H:%M')
    else:
        intv_date = str(intv_date)[:16]

    meta_style_label = ParagraphStyle(
        'meta_label', fontName='Helvetica-Bold', fontSize=9,
        textColor=COLORS["text_light"], alignment=TA_RIGHT, leading=14
    )
    meta_style_value = ParagraphStyle(
        'meta_value', fontName='Helvetica', fontSize=9,
        textColor=COLORS["text"], alignment=TA_LEFT, leading=14
    )

    meta_rows = [
        [Paragraph("Date de generation", meta_style_label),
         Paragraph(date_str, meta_style_value)],
        [Paragraph("Genere par", meta_style_label),
         Paragraph("Module IA Generative (v2.3)", meta_style_value)],
        [Paragraph("Plateforme", meta_style_label),
         Paragraph("Neo-Sousse Smart City 2030", meta_style_value)],
        [Paragraph("Intervention", meta_style_label),
         Paragraph(f"#{intervention.get('IDIn', '')} — {_sanitize_text(str(intervention.get('Nature', '')))}", meta_style_value)],
        [Paragraph("Confidentialite", meta_style_label),
         Paragraph("Usage interne", meta_style_value)],
    ]

    meta_tbl = Table(meta_rows, colWidths=[160, 310])
    meta_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLORS["border"]),
    ]))
    elems.append(meta_tbl)
    elems.append(Spacer(1, 50))

    # Bottom bar
    d3 = Drawing(w - 72, 5)
    d3.add(Rect(0, 0, w - 72, 5, fillColor=COLORS["primary"], strokeColor=None))
    elems.append(d3)

    elems.append(PageBreak())

    # ══════════════════════════════════════════════════════════════
    # PAGE 2: KEY METRICS + DECISION
    # ══════════════════════════════════════════════════════════════

    elems.append(Paragraph("Resume de la Validation", styles['SectionTitle']))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=COLORS["primary"]))
    elems.append(Spacer(1, 14))

    # ── Decision badge ──
    clean_approval = _sanitize_text(str(approval))
    approval_upper = clean_approval.upper()

    if 'APPROVED' in approval_upper or 'VALID' in approval_upper:
        if 'CONDITION' in approval_upper:
            dec_text = "INTERVENTION VALIDEE SOUS CONDITIONS"
            bg_col = COLORS["warning"]
        else:
            dec_text = "INTERVENTION VALIDEE"
            bg_col = COLORS["success"]
    elif 'REVIEW' in approval_upper:
        dec_text = "REVISION REQUISE"
        bg_col = COLORS["warning"]
    elif 'REJECT' in approval_upper:
        dec_text = "INTERVENTION NON VALIDEE"
        bg_col = COLORS["danger"]
    else:
        dec_text = f"DECISION: {clean_approval}"
        bg_col = COLORS["warning"]

    dec_data = [[Paragraph(f"<b>  {dec_text}  </b>", ParagraphStyle('DecBadge', fontName='Helvetica', fontSize=13, textColor=COLORS["white"], alignment=TA_CENTER))]]
    dec_tbl = Table(dec_data, colWidths=[300])
    dec_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_col),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    dec_tbl.hAlign = 'CENTER'
    elems.append(dec_tbl)

    elems.append(Spacer(1, 16))

    # ── Key Metrics Row ──
    score1_text, score1_color = _build_score_badge(score1, styles)
    score2_text, score2_color = _build_score_badge(score2, styles)

    conf_pct = f"{conf * 100:.0f}%" if isinstance(conf, (int, float)) else str(conf)
    try:
        conf_val = float(conf)
        conf_color = COLORS["success"] if conf_val >= 0.7 else (COLORS["warning"] if conf_val >= 0.5 else COLORS["danger"])
    except (ValueError, TypeError):
        conf_color = COLORS["text_light"]

    metrics_data = [[
        _build_metric_cell(str(score1), "Score Tech. 1", score1_color, styles),
        _build_metric_cell(str(score2), "Score Tech. 2", score2_color, styles),
        _build_metric_cell(f"{avg_score:.0f}" if isinstance(avg_score, (int, float)) else str(avg_score),
                          "Score Moyen", COLORS["primary"], styles),
        _build_metric_cell(conf_pct, "Confiance", conf_color, styles),
    ]]

    metrics_tbl = Table(metrics_data, colWidths=[(w - 72) / 4] * 4)
    metrics_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS["bg_light"]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS["border"]),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    elems.append(metrics_tbl)
    elems.append(Spacer(1, 20))

    # ── Summary Data Table ──
    elems.append(Paragraph("Informations de l'Intervention", styles['SubSection']))
    elems.append(Spacer(1, 6))

    # Table header style
    hdr_style = ParagraphStyle(
        'tbl_hdr', fontName='Helvetica-Bold', fontSize=9,
        textColor=COLORS["white"], alignment=TA_CENTER, leading=13,
    )
    cell_label_style = ParagraphStyle(
        'cell_lbl', fontName='Helvetica-Bold', fontSize=9,
        textColor=COLORS["text"], alignment=TA_LEFT, leading=13,
    )
    cell_value_style = ParagraphStyle(
        'cell_val', fontName='Helvetica', fontSize=9,
        textColor=COLORS["text"], alignment=TA_LEFT, leading=13,
    )

    summary_data = [
        [Paragraph("Information", hdr_style), Paragraph("Details", hdr_style)],
        [Paragraph("Intervention ID", cell_label_style), Paragraph(str(intervention.get('IDIn', '')), cell_value_style)],
        [Paragraph("Nature", cell_label_style), Paragraph(_sanitize_text(str(intervention.get('Nature', ''))), cell_value_style)],
        [Paragraph("Date de l'Intervention", cell_label_style), Paragraph(intv_date, cell_value_style)],
        [Paragraph("Score Technicien 1", cell_label_style), Paragraph(score1_text, cell_value_style)],
        [Paragraph("Score Technicien 2", cell_label_style), Paragraph(score2_text, cell_value_style)],
        [Paragraph("Score Moyen", cell_label_style), Paragraph(
            f"{avg_score:.1f}/100" if isinstance(avg_score, (int, float)) else str(avg_score), cell_value_style)],
        [Paragraph("Decision", cell_label_style), Paragraph(clean_approval, cell_value_style)],
        [Paragraph("Indice de Confiance", cell_label_style), Paragraph(conf_pct, cell_value_style)],
    ]

    summary_tbl = Table(summary_data, colWidths=[190, 300])
    summary_tbl.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLORS["white"]),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Body
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS["white"], COLORS["bg_light"]]),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS["border"]),
    ]))
    elems.append(summary_tbl)
    elems.append(Spacer(1, 24))

    # ══════════════════════════════════════════════════════════════
    # TECHNICIAN 1 REPORT
    # ══════════════════════════════════════════════════════════════

    tech1_name = intervention.get('tech1_name', 'Technicien 1')
    tech1_section = []
    tech1_section.append(Paragraph(
        f"Rapport Technicien 1 — {_sanitize_text(str(tech1_name))} (Intervenant)",
        styles['SectionTitle']
    ))
    tech1_section.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["border"]))
    tech1_section.append(Spacer(1, 10))

    # Score indicator for Tech 1
    score1_label, score1_clr = _build_score_badge(score1, styles)
    tech1_section.append(Paragraph(
        f"<b>Evaluation IA :</b> {score1_label} — Qualite: {_sanitize_text(str(quality1))}",
        styles['BodyPro']
    ))
    tech1_section.append(Spacer(1, 8))

    if tech1_report and tech1_report.strip():
        tech1_section.append(Paragraph("<b>Contenu du rapport :</b>", styles['BodyPro']))
        tech1_section.append(Spacer(1, 4))
        _format_paragraphs(tech1_report, styles['BodyReport'], tech1_section)
    else:
        tech1_section.append(Paragraph(
            "<i>Aucun rapport fourni par le Technicien 1.</i>", styles['BodyPro']
        ))

    tech1_section.append(Spacer(1, 18))
    elems.append(KeepTogether(tech1_section[:4]))
    elems.extend(tech1_section[4:])

    # ══════════════════════════════════════════════════════════════
    # TECHNICIAN 2 REPORT
    # ══════════════════════════════════════════════════════════════

    tech2_name = intervention.get('tech2_name', 'Technicien 2')
    tech2_section = []
    tech2_section.append(Paragraph(
        f"Rapport Technicien 2 — {_sanitize_text(str(tech2_name))} (Validateur)",
        styles['SectionTitle']
    ))
    tech2_section.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["border"]))
    tech2_section.append(Spacer(1, 10))

    # Score indicator for Tech 2
    score2_label, score2_clr = _build_score_badge(score2, styles)
    tech2_section.append(Paragraph(
        f"<b>Evaluation IA :</b> {score2_label} — Qualite: {_sanitize_text(str(quality2))}",
        styles['BodyPro']
    ))
    tech2_section.append(Spacer(1, 8))

    if tech2_report and tech2_report.strip():
        tech2_section.append(Paragraph("<b>Contenu du rapport :</b>", styles['BodyPro']))
        tech2_section.append(Spacer(1, 4))
        _format_paragraphs(tech2_report, styles['BodyReport'], tech2_section)
    else:
        tech2_section.append(Paragraph(
            "<i>Aucun rapport fourni par le Technicien 2.</i>", styles['BodyPro']
        ))

    tech2_section.append(Spacer(1, 18))
    elems.append(KeepTogether(tech2_section[:4]))
    elems.extend(tech2_section[4:])

    # ══════════════════════════════════════════════════════════════
    # IA ANALYSIS RESULTS — Direct conclusions, NO questions
    # ══════════════════════════════════════════════════════════════

    ia_section = []
    ia_section.append(Paragraph("Analyse et Conclusions de l'IA", styles['SectionTitle']))
    ia_section.append(HRFlowable(width="100%", thickness=1.5, color=COLORS["primary"]))
    ia_section.append(Spacer(1, 12))

    # Always generate professional IA analysis (no questions, only direct statements)
    ia_section.append(Paragraph("<b>Resultats de l'analyse automatisee :</b>", styles['BodyPro']))
    ia_section.append(Spacer(1, 6))

    # Build structured IA analysis as bullet points
    ia_points = []

    # Score analysis
    try:
        s1 = int(score1)
        s2 = int(score2)
        diff = abs(s1 - s2)

        ia_points.append(
            f"Le rapport du technicien intervenant a obtenu un score de {s1}/100 "
            f"({quality1}), confirmant {'une documentation detaillee et conforme aux standards.' if s1 >= 55 else 'un niveau de detail insuffisant necessitant une amelioration.'}"
        )
        ia_points.append(
            f"Le rapport du technicien validateur a obtenu un score de {s2}/100 "
            f"({quality2}), {'validant la qualite de l intervention.' if s2 >= 55 else 'indiquant des lacunes dans la verification.'}"
        )

        if diff < 15:
            ia_points.append(
                f"La coherence entre les deux rapports est excellente (ecart de {diff} points), "
                f"ce qui renforce la fiabilite de l'evaluation."
            )
        elif diff < 30:
            ia_points.append(
                f"Un ecart modere de {diff} points est constate entre les deux rapports. "
                f"Cet ecart reste dans les limites acceptables."
            )
        else:
            ia_points.append(
                f"Un ecart significatif de {diff} points a ete detecte entre les deux rapports. "
                f"Une investigation supplementaire est recommandee."
            )
    except (ValueError, TypeError):
        pass

    # Confidence analysis
    try:
        conf_val = float(conf)
        if conf_val >= 0.8:
            ia_points.append(
                f"L'indice de confiance est eleve ({conf_val * 100:.0f}%), "
                f"indiquant une grande fiabilite de l'evaluation globale."
            )
        elif conf_val >= 0.6:
            ia_points.append(
                f"L'indice de confiance est moderee ({conf_val * 100:.0f}%). "
                f"L'evaluation est globalement fiable avec quelques reserves."
            )
        else:
            ia_points.append(
                f"L'indice de confiance est faible ({conf_val * 100:.0f}%). "
                f"Une validation manuelle complementaire est fortement recommandee."
            )
    except (ValueError, TypeError):
        pass

    # Add any reasoning from the validator
    if reasoning and reasoning.strip():
        clean_reasoning = _sanitize_text(reasoning)
        # Parse pipe-separated or newline-separated reasoning
        if ' | ' in clean_reasoning:
            parts = clean_reasoning.split(' | ')
        else:
            parts = clean_reasoning.split('\n')

        for part in parts:
            part = part.strip()
            if part and not any(q in part for q in ['?', 'Est-ce que', 'Pouvez-vous', 'Pourquoi']):
                # Only include assertive statements, not questions
                ia_points.append(part)

    # Render IA analysis as numbered points
    for i, point in enumerate(ia_points, 1):
        ia_section.append(Paragraph(
            f"<b>{i}.</b> {point}",
            styles['BulletItem']
        ))
        ia_section.append(Spacer(1, 4))

    ia_section.append(Spacer(1, 12))
    elems.append(KeepTogether(ia_section[:3]))
    elems.extend(ia_section[3:])

    # ══════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════

    reco_section = []
    reco_section.append(Paragraph("Recommandations", styles['SectionTitle']))
    reco_section.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["border"]))
    reco_section.append(Spacer(1, 10))

    recommendations = []
    try:
        avg = float(avg_score)
        if avg >= 70:
            recommendations.append(
                "Les scores des rapports techniques sont satisfaisants. "
                "L'intervention peut etre validee et cloturee dans le systeme."
            )
            recommendations.append(
                "Archiver les rapports techniques pour reference future "
                "et mise a jour de la base de connaissances."
            )
        elif avg >= 50:
            recommendations.append(
                "Les rapports techniques presentent un niveau de qualite acceptable. "
                "Il est recommande de completer les details manquants avant la cloture."
            )
            recommendations.append(
                "Planifier une session de retour d'experience avec les techniciens "
                "pour ameliorer la documentation future."
            )
        else:
            recommendations.append(
                "Les rapports techniques necessitent une amelioration significative. "
                "Il est imperatif de demander des complements d'information."
            )
            recommendations.append(
                "Organiser une formation sur les bonnes pratiques de redaction "
                "de rapports techniques pour les equipes concernees."
            )
    except (ValueError, TypeError):
        recommendations.append("Verifier les scores et completer l'evaluation.")

    recommendations.append(
        "Assurer le suivi post-intervention en verifiant le bon fonctionnement "
        "du capteur concerne dans les 48 heures suivantes."
    )

    for i, reco in enumerate(recommendations, 1):
        reco_section.append(Paragraph(f"<b>{i}.</b> {reco}", styles['BulletItem']))
        reco_section.append(Spacer(1, 4))

    reco_section.append(Spacer(1, 12))
    elems.append(KeepTogether(reco_section[:3]))
    elems.extend(reco_section[3:])

    # ══════════════════════════════════════════════════════════════
    # CONCLUSION
    # ══════════════════════════════════════════════════════════════

    concl_section = []
    concl_section.append(Paragraph("Conclusion", styles['SectionTitle']))
    concl_section.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["border"]))
    concl_section.append(Spacer(1, 10))

    conclusion_text = (
        f"L'intervention #{intervention.get('IDIn', '')} de nature "
        f"'{_sanitize_text(str(intervention.get('Nature', '')))}' a ete analysee par le module IA "
        f"de la plateforme Neo-Sousse Smart City 2030. "
    )
    conclusion_text += (
        f"Le technicien intervenant ({_sanitize_text(str(tech1_name))}) a obtenu un score de {score1}/100 "
        f"et le technicien validateur ({_sanitize_text(str(tech2_name))}) un score de {score2}/100. "
    )

    try:
        conf_val = float(conf)
        conclusion_text += f"L'indice de confiance global est de {conf_val * 100:.0f}%. "
    except (ValueError, TypeError):
        pass

    conclusion_text += f"Decision finale : {clean_approval}."

    concl_section.append(Paragraph(conclusion_text, styles['BodyPro']))
    concl_section.append(Spacer(1, 30))
    elems.append(KeepTogether(concl_section))

    # ══════════════════════════════════════════════════════════════
    # FOOTER NOTE
    # ══════════════════════════════════════════════════════════════

    elems.append(HRFlowable(width="100%", thickness=1.5, color=COLORS["primary"]))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(
        f"Rapport genere automatiquement par le Module IA Generative (v2.3) — "
        f"{datetime.now().strftime('%d/%m/%Y a %H:%M:%S')} — "
        f"Neo-Sousse Smart City 2030",
        styles['SmallNote']
    ))

    # Build PDF
    doc.build(elems, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
