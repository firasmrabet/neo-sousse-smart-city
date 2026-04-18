"""
Professional PDF Report Generator — Module IA Générative (§2.3)
Génère des rapports PDF professionnels, structurés et visuellement 
impressionnants à partir des données de la base.

Features:
  - Page de couverture avec branding Neo-Sousse
  - Résumé exécutif
  - Tableaux de données stylisés
  - Graphiques intégrés (matplotlib → PDF)
  - Pied de page avec pagination
  - Support multi-types: capteurs, interventions, véhicules, citoyens, custom
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available — PDF generation disabled")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# Color Palette
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    "primary": colors.HexColor("#0f766e"),
    "primary_light": colors.HexColor("#14b8a6"),
    "primary_dark": colors.HexColor("#0d4f4a"),
    "accent": colors.HexColor("#3b82f6"),
    "accent_light": colors.HexColor("#93c5fd"),
    "success": colors.HexColor("#22c55e"),
    "warning": colors.HexColor("#f59e0b"),
    "danger": colors.HexColor("#ef4444"),
    "info": colors.HexColor("#06b6d4"),
    "dark": colors.HexColor("#0f172a"),
    "dark2": colors.HexColor("#1e293b"),
    "text": colors.HexColor("#1e293b"),
    "text_light": colors.HexColor("#64748b"),
    "border": colors.HexColor("#e2e8f0"),
    "bg_light": colors.HexColor("#f8fafc"),
    "white": colors.white,
}


def _sanitize_text(text: str) -> str:
    """Remove emojis and special chars that Helvetica cannot render."""
    if not text:
        return ""
    emoji_chars = [
        '\U0001f4ca', '\U0001f4cb', '\U0001f4e1', '\U0001f527', '\U0001f697', '\U0001f465',
        '\U0001f4a1', '\u26a0\ufe0f', '\u2705', '\U0001f534', '\U0001f7e2', '\U0001f7e1',
        '\U0001f916', '\U0001f4c4', '\u2b07\ufe0f', '\U0001f504', '\U0001f3c6', '\u2b50',
        '\U0001f6a8', '\u23f1\ufe0f', '\U0001f4f6', '\U0001f9e0', '\u26a1', '\U0001f535',
        '\U0001f7e0', '\U0001f4c8', '\U0001f4c9', '\U0001f3af', '\U0001f514', '\U0001f33f',
        '\U0001f699', '\U0001f5fa\ufe0f', '\U0001f6e0\ufe0f', '\U0001f50d', '\U0001f4dd',
    ]
    # Also strip by common emoji text representations
    text_emojis = [
        '📊', '📋', '📡', '🔧', '🚗', '👥', '💡', '⚠️', '✅', '🔴', '🟢', '🟡',
        '🤖', '📄', '⬇️', '🔄', '🏆', '⭐', '🚨', '⏱️', '📶', '🧠', '⚡',
        '🔵', '🟠', '📈', '📉', '🎯', '🔔', '🌿', '🚙', '🗺️', '🛠️', '🔍', '📝',
    ]
    for e in emoji_chars + text_emojis:
        text = text.replace(e, '')
    # Strip markdown formatting artifacts
    text = text.replace('**', '').replace('##', '').replace('###', '')
    text = text.replace('# ', '')
    return text.strip()


def _get_styles():
    """Custom professional styles with proper leading to prevent overlapping"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=COLORS["white"],
        alignment=TA_CENTER,
        spaceAfter=12,
        leading=34,
    ))
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=14,
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=18,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLORS["primary"],
        spaceBefore=20,
        spaceAfter=8,
        leading=18,
        borderWidth=0,
        borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=COLORS["primary_dark"],
        spaceBefore=12,
        spaceAfter=6,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name='BodyPro',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["text"],
        alignment=TA_JUSTIFY,
        leading=15,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='SmallNote',
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        textColor=COLORS["text_light"],
        alignment=TA_LEFT,
        leading=10,
    ))
    styles.add(ParagraphStyle(
        name='MetricValue',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=COLORS["primary"],
        alignment=TA_CENTER,
        leading=26,
    ))
    styles.add(ParagraphStyle(
        name='MetricLabel',
        fontName='Helvetica',
        fontSize=9,
        textColor=COLORS["text_light"],
        alignment=TA_CENTER,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        name='AlertCritical',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=COLORS["danger"],
        spaceBefore=4,
        spaceAfter=4,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        name='AlertWarning',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=COLORS["warning"],
        spaceBefore=4,
        spaceAfter=4,
        leading=13,
    ))
    styles.add(ParagraphStyle(
        name='AlertInfo',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLORS["info"],
        spaceBefore=4,
        spaceAfter=4,
        leading=13,
    ))

    return styles


def _header_footer(canvas, doc):
    """Professional header and footer on each page"""
    canvas.saveState()
    w, h = A4

    # Header line
    canvas.setStrokeColor(COLORS["primary"])
    canvas.setLineWidth(2)
    canvas.line(36, h - 36, w - 36, h - 36)

    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(COLORS["primary"])
    canvas.drawString(36, h - 30, "NEO-SOUSSE SMART CITY 2030")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(COLORS["text_light"])
    canvas.drawRightString(w - 36, h - 30, f"Rapport IA — {datetime.now().strftime('%d/%m/%Y')}")

    # Footer
    canvas.setStrokeColor(COLORS["border"])
    canvas.setLineWidth(0.5)
    canvas.line(36, 40, w - 36, 40)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(COLORS["text_light"])
    canvas.drawString(36, 28, "Neo-Sousse Smart City — Plateforme IoT Intelligente — Rapport généré par IA")
    canvas.drawRightString(w - 36, 28, f"Page {doc.page}")

    # Confidentiality
    canvas.setFont("Helvetica-Oblique", 6)
    canvas.drawCentredString(w / 2, 18, "Document confidentiel — Usage interne uniquement — Module IA 2.3")

    canvas.restoreState()


def _build_cover_page(styles, report_title: str, report_type: str, 
                       report_date: str = None, extra_info: str = "") -> list:
    """Build a professional cover page with proper spacing (no overlap)"""
    elems = []
    w, h = A4

    elems.append(Spacer(1, 80))

    # Decorative top bar
    d = Drawing(w - 72, 4)
    d.add(Rect(0, 0, w - 72, 4, fillColor=COLORS["primary"], strokeColor=None))
    elems.append(d)
    elems.append(Spacer(1, 50))

    # Brand text — proper leading and spacing to prevent overlap
    elems.append(Paragraph("NEO-SOUSSE", ParagraphStyle(
        'brand1', fontName='Helvetica-Bold', fontSize=32,
        textColor=COLORS["primary"], alignment=TA_CENTER,
        spaceAfter=4, leading=38,
    )))
    elems.append(Paragraph("SMART CITY 2030", ParagraphStyle(
        'brand2', fontName='Helvetica', fontSize=13,
        textColor=COLORS["text_light"], alignment=TA_CENTER,
        spaceAfter=30, leading=16,
    )))

    # Separator
    d2 = Drawing(200, 2)
    d2.add(Rect(0, 0, 200, 2, fillColor=COLORS["primary_light"], strokeColor=None))
    elems.append(d2)
    elems.append(Spacer(1, 30))

    # Report title — sanitized
    clean_title = _sanitize_text(report_title)
    elems.append(Paragraph(clean_title, ParagraphStyle(
        'rtitle', fontName='Helvetica-Bold', fontSize=20,
        textColor=COLORS["dark"], alignment=TA_CENTER,
        spaceAfter=10, leading=26,
    )))

    # Report type badge — sanitized
    clean_type = _sanitize_text(report_type)
    badge_data = [[Paragraph(f"  {clean_type}  ", ParagraphStyle(
        'badge', fontName='Helvetica-Bold', fontSize=9,
        textColor=COLORS["white"], alignment=TA_CENTER
    ))]]
    badge_tbl = Table(badge_data, colWidths=[200])
    badge_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS["primary"]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    elems.append(badge_tbl)
    elems.append(Spacer(1, 40))

    # Metadata table
    date_str = report_date or datetime.now().strftime('%d/%m/%Y a %H:%M')
    meta_data = [
        ['Date de generation', date_str],
        ['Genere par', 'Module IA Generative (v2.3)'],
        ['Plateforme', 'Neo-Sousse Smart City 2030'],
        ['Confidentialite', 'Usage interne'],
    ]
    if extra_info:
        clean_extra = _sanitize_text(extra_info)
        meta_data.append(['Details', clean_extra])

    meta_tbl = Table(meta_data, colWidths=[150, 320])
    meta_tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COLORS["text_light"]),
        ('TEXTCOLOR', (1, 0), (1, -1), COLORS["text"]),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, COLORS["border"]),
    ]))
    elems.append(meta_tbl)

    elems.append(Spacer(1, 50))

    # Bottom decorative
    d3 = Drawing(w - 72, 4)
    d3.add(Rect(0, 0, w - 72, 4, fillColor=COLORS["primary"], strokeColor=None))
    elems.append(d3)

    elems.append(PageBreak())
    return elems


def _build_metrics_row(metrics: List[Dict[str, str]], styles) -> list:
    """Build a row of metric cards"""
    if not metrics:
        return []

    cols = len(metrics)
    col_width = (A4[0] - 72) / cols

    row_data = []
    for m in metrics:
        cell_content = (
            f"<font size='18'><b>{m.get('value', '—')}</b></font><br/>"
            f"<font size='8' color='#64748b'>{m.get('label', '')}</font>"
        )
        row_data.append(Paragraph(cell_content, ParagraphStyle(
            f'mc_{m.get("label", "")}', fontName='Helvetica',
            fontSize=10, alignment=TA_CENTER, leading=22,
        )))

    tbl = Table([row_data], colWidths=[col_width] * cols)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS["bg_light"]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS["border"]),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))

    return [tbl, Spacer(1, 12)]


def _build_data_table(headers: List[str], rows: List[List[str]], 
                       title: str = "", styles=None) -> list:
    """Build a styled data table with proper text wrapping"""
    elems = []
    if title and styles:
        elems.append(Paragraph(_sanitize_text(title), styles['SubSection']))

    if not rows:
        if styles:
            elems.append(Paragraph("Aucune donnee disponible.", styles['BodyPro']))
        return elems

    # Wrap header and body cells in Paragraph for proper text wrapping
    header_style = ParagraphStyle(
        'tbl_header', fontName='Helvetica-Bold', fontSize=8.5,
        textColor=COLORS["white"], alignment=TA_CENTER, leading=11,
    )
    body_style = ParagraphStyle(
        'tbl_body', fontName='Helvetica', fontSize=8,
        textColor=COLORS["text"], alignment=TA_LEFT, leading=11,
    )

    wrapped_headers = [Paragraph(_sanitize_text(str(h)), header_style) for h in headers]
    wrapped_rows = []
    for row in rows:
        wrapped_row = [Paragraph(_sanitize_text(str(cell)), body_style) for cell in row]
        wrapped_rows.append(wrapped_row)

    data = [wrapped_headers] + wrapped_rows
    n_cols = len(headers)
    col_width = (A4[0] - 72) / n_cols

    tbl = Table(data, colWidths=[col_width] * n_cols, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), COLORS["primary"]),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Body
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS["white"], COLORS["bg_light"]]),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS["border"]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 12))


    return elems


def _build_alert_section(alerts: List[Dict], styles) -> list:
    """Build compact alerts summary as a table"""
    elems = []
    elems.append(Paragraph("Alertes Automatiques", styles['SectionTitle']))
    elems.append(HRFlowable(width="100%", thickness=1, color=COLORS["primary"]))
    elems.append(Spacer(1, 6))

    if not alerts:
        elems.append(Paragraph("Aucune alerte active.", styles['BodyPro']))
        return elems

    # Compact: show alerts as a single styled table
    elems.append(Paragraph(f"{len(alerts)} alerte(s) detectee(s).", styles['BodyPro']))

    headers = ["Severite", "Type", "Message"]
    rows = []
    for a in alerts[:15]:  # max 15 in PDF
        msg = str(a.get('message', ''))[:60]
        rows.append([
            str(a.get('severity', '')),
            str(a.get('entity_type', '')),
            msg,
        ])

    elems.extend(_build_data_table(headers, rows, styles=styles))
    return elems


def _make_chart_image(chart_type: str, data: Dict, title: str = "") -> Optional[BytesIO]:
    """Generate chart as image for PDF embedding"""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=120)
        fig.patch.set_facecolor('#ffffff')

        if chart_type == "bar":
            labels = data.get("labels", [])
            values = data.get("values", [])
            bar_colors = data.get("colors", ['#0f766e'] * len(labels))
            bars = ax.bar(labels, values, color=bar_colors, edgecolor='white', linewidth=0.5)
            ax.set_ylabel(data.get("ylabel", ""), fontsize=9, color='#64748b')
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.5,
                        f'{val}', ha='center', va='bottom', fontsize=8, fontweight='bold',
                        color='#1e293b')

        elif chart_type == "pie":
            labels = data.get("labels", [])
            values = data.get("values", [])
            pie_colors = data.get("colors", ['#0f766e', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7'])
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, colors=pie_colors[:len(labels)],
                autopct='%1.1f%%', startangle=90,
                textprops={'fontsize': 8},
            )
            for text in autotexts:
                text.set_fontweight('bold')
                text.set_fontsize(8)

        elif chart_type == "line":
            x = data.get("x", [])
            y = data.get("y", [])
            ax.plot(x, y, color='#0f766e', linewidth=2, marker='o', markersize=4)
            ax.fill_between(x, y, alpha=0.1, color='#0f766e')
            ax.set_ylabel(data.get("ylabel", ""), fontsize=9, color='#64748b')

        if title:
            ax.set_title(title, fontsize=11, fontweight='bold', color='#1e293b', pad=10)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e2e8f0')
        ax.spines['bottom'].set_color('#e2e8f0')
        ax.tick_params(colors='#64748b', labelsize=8)

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        plt.close('all')
        return None


# ═══════════════════════════════════════════════════════════════════
# MAIN GENERATOR CLASS
# ═══════════════════════════════════════════════════════════════════

class ProfessionalPDFGenerator:
    """
    Générateur de rapports PDF professionnels.
    Supporte tous les types d'entités de la base de données.
    """

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab required for PDF generation. Install: pip install reportlab")
        self.styles = _get_styles()

    def generate_custom_report(self, title: str, report_type: str,
                                summary_text: str, sections: List[Dict],
                                alerts: List[Dict] = None,
                                metrics: List[Dict] = None,
                                extra_info: str = "") -> bytes:
        """
        Generate a fully custom professional PDF report.

        Args:
            title: Report title
            report_type: Category (e.g., "QUALITÉ DE L'AIR", "CAPTEURS")
            summary_text: Executive summary paragraph
            sections: List of dicts with keys:
                - title (str)
                - content (str) - paragraph text
                - table (dict) - optional: {headers: [...], rows: [[...], ...]}
                - chart (dict) - optional: {type: "bar"|"pie"|"line", data: {...}, title: "..."}
            alerts: Optional list of alert dicts
            metrics: Optional list of {value, label} dicts
            extra_info: Additional info for cover page
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=36, leftMargin=36,
            topMargin=50, bottomMargin=50,
            title=title,
            author="Neo-Sousse Smart City — IA Module",
        )

        elems = []

        # ── Cover Page ──
        elems.extend(_build_cover_page(self.styles, title, report_type, extra_info=extra_info))

        # ── Executive Summary ──
        elems.append(Paragraph("Resume Executif", self.styles['SectionTitle']))
        elems.append(HRFlowable(width="100%", thickness=1, color=COLORS["primary"]))
        elems.append(Spacer(1, 8))
        # Clean text: remove all emojis and replace newlines
        clean_summary = _sanitize_text(summary_text).replace('\n', '<br/>')
        elems.append(Paragraph(clean_summary, self.styles['BodyPro']))
        elems.append(Spacer(1, 12))

        # ── Key Metrics ──
        if metrics:
            elems.append(Paragraph("Indicateurs Cles", self.styles['SectionTitle']))
            elems.extend(_build_metrics_row(metrics, self.styles))

        # ── Alerts ──
        if alerts:
            elems.extend(_build_alert_section(alerts, self.styles))
            elems.append(Spacer(1, 12))

        # ── Sections ──
        for section in sections:
            sec_title = _sanitize_text(section.get('title', ''))
            if not sec_title:
                sec_title = 'Section'
            elems.append(Paragraph(sec_title, self.styles['SectionTitle']))
            elems.append(HRFlowable(width="100%", thickness=0.5, color=COLORS["border"]))
            elems.append(Spacer(1, 6))

            if section.get('content'):
                clean_c = _sanitize_text(section['content'])
                if clean_c:
                    # Split into paragraphs for proper spacing
                    for para in clean_c.split('\n'):
                        para = para.strip()
                        if para:
                            if para.startswith("DECISION:"):
                                if "VALIDEE" in para.upper():
                                    para = f"<font color='#22c55e'><b>{para}</b></font>"
                                elif "REJETEE" in para.upper() or "REVISION" in para.upper():
                                    para = f"<font color='#ef4444'><b>{para}</b></font>"
                                else:
                                    para = f"<b>{para}</b>"
                            elems.append(Paragraph(para, self.styles['BodyPro']))

            if section.get('table'):
                tbl = section['table']
                elems.extend(_build_data_table(
                    tbl.get('headers', []),
                    tbl.get('rows', []),
                    styles=self.styles,
                ))

            if section.get('chart') and MATPLOTLIB_AVAILABLE:
                chart = section['chart']
                img_buf = _make_chart_image(
                    chart.get('type', 'bar'),
                    chart.get('data', {}),
                    chart.get('title', ''),
                )
                if img_buf:
                    img = Image(img_buf, width=14 * cm, height=8 * cm)
                    elems.append(img)
                    elems.append(Spacer(1, 8))

            elems.append(Spacer(1, 8))

        # ── Footer note ──
        elems.append(Spacer(1, 20))
        elems.append(HRFlowable(width="100%", thickness=1, color=COLORS["primary"]))
        elems.append(Spacer(1, 6))
        elems.append(Paragraph(
            f"Rapport généré automatiquement par le Module IA Générative (§2.3) — "
            f"{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')} — "
            f"Neo-Sousse Smart City 2030",
            self.styles['SmallNote']
        ))

        # Build PDF
        doc.build(elems, onFirstPage=_header_footer, onLaterPages=_header_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_sensor_report(self, sensors: List[Dict], measures: List[Dict] = None,
                                alerts: List[Dict] = None) -> bytes:
        """Generate comprehensive sensor status report"""
        total = len(sensors)
        actifs = len([s for s in sensors if s.get('Statut') == 'Actif'])
        hs = len([s for s in sensors if s.get('Statut') == 'Hors Service'])
        maint = len([s for s in sensors if s.get('Statut') == 'En Maintenance'])

        metrics = [
            {"value": str(total), "label": "Total Capteurs"},
            {"value": str(actifs), "label": "Actifs"},
            {"value": str(hs), "label": "Hors Service"},
            {"value": f"{(actifs/total*100):.0f}%" if total > 0 else "—", "label": "Taux Disponibilité"},
        ]

        # Type distribution
        types = {}
        for s in sensors:
            t = s.get('Type', 'N/A')
            types[t] = types.get(t, 0) + 1

        sensor_rows = []
        for s in sensors:
            sensor_rows.append([
                str(s.get('UUID', ''))[:12] + '...',
                str(s.get('Type', 'N/A')),
                str(s.get('Statut', 'N/A')),
                str(s.get('Date Installation', 'N/A'))[:10],
            ])

        sections = [
            {
                "title": "📡 Distribution par Type",
                "content": f"Les {total} capteurs déployés sont répartis en {len(types)} catégories.",
                "chart": {
                    "type": "pie",
                    "data": {
                        "labels": list(types.keys()),
                        "values": list(types.values()),
                    },
                    "title": "Répartition des Capteurs par Type",
                },
            },
            {
                "title": "📊 État des Capteurs",
                "content": "",
                "chart": {
                    "type": "bar",
                    "data": {
                        "labels": ["Actif", "En Maintenance", "Hors Service"],
                        "values": [actifs, maint, hs],
                        "colors": ["#22c55e", "#f59e0b", "#ef4444"],
                    },
                    "title": "Distribution par État",
                },
            },
            {
                "title": "📋 Liste Détaillée des Capteurs",
                "table": {
                    "headers": ["UUID", "Type", "Statut", "Installation"],
                    "rows": sensor_rows[:30],
                },
            },
        ]

        summary = (
            f"Ce rapport présente l'état complet du réseau de capteurs IoT de Neo-Sousse. "
            f"Sur {total} capteurs déployés, {actifs} sont actifs ({(actifs/total*100):.0f}% de disponibilité), "
            f"{maint} en maintenance et {hs} hors service. "
            + (f"⚠️ {hs} capteurs nécessitent une attention immédiate." if hs > 0 else
               "✅ Tous les capteurs sont opérationnels.")
        )

        return self.generate_custom_report(
            title="Rapport d'État des Capteurs IoT",
            report_type="CAPTEURS — MONITORING",
            summary_text=summary,
            sections=sections,
            alerts=alerts or [],
            metrics=metrics,
        )

    def generate_intervention_report(self, interventions: List[Dict],
                                      technicians: List[Dict] = None) -> bytes:
        """Generate intervention analytics report"""
        total = len(interventions)
        types_count = {}
        for i in interventions:
            n = i.get('Nature', 'N/A')
            types_count[n] = types_count.get(n, 0) + 1

        terminées = len([i for i in interventions if i.get('statut') == 'Terminée'])
        en_cours = total - terminées

        metrics = [
            {"value": str(total), "label": "Total Interventions"},
            {"value": str(terminées), "label": "Terminées"},
            {"value": str(en_cours), "label": "En Cours"},
            {"value": f"{(terminées/total*100):.0f}%" if total > 0 else "—", "label": "Taux Complétion"},
        ]

        intv_rows = []
        for i in interventions[:25]:
            intv_rows.append([
                str(i.get('IDIn', '')),
                str(i.get('Nature', 'N/A')),
                str(i.get('DateHeure', ''))[:16],
                str(i.get('statut', 'N/A')),
                str(i.get('Durée', 'N/A')),
            ])

        sections = [
            {
                "title": "📊 Répartition par Nature",
                "chart": {
                    "type": "bar",
                    "data": {
                        "labels": list(types_count.keys()),
                        "values": list(types_count.values()),
                        "colors": ["#3b82f6", "#f59e0b", "#a855f7"],
                    },
                    "title": "Interventions par Nature",
                },
            },
            {
                "title": "📋 Détail des Interventions",
                "table": {
                    "headers": ["ID", "Nature", "Date", "Statut", "Durée (min)"],
                    "rows": intv_rows,
                },
            },
        ]

        summary = (
            f"Ce rapport analyse {total} interventions enregistrées. "
            f"{terminées} sont terminées ({(terminées/total*100):.0f}% de complétion) "
            f"et {en_cours} sont en cours de traitement. "
            + ", ".join([f"{v} {k}" for k, v in types_count.items()]) + "."
        )

        return self.generate_custom_report(
            title="Rapport d'Analyse des Interventions",
            report_type="INTERVENTIONS — ANALYTICS",
            summary_text=summary,
            sections=sections,
            metrics=metrics,
        )

    def generate_vehicle_report(self, vehicles: List[Dict], trips: List[Dict]) -> bytes:
        """Generate vehicle and trips report"""
        total_v = len(vehicles)
        total_t = len(trips)
        total_co2 = sum(float(t.get('ÉconomieCO2', 0) or 0) for t in trips)

        energy_count = {}
        for v in vehicles:
            e = v.get('Énergie Utilisée', 'N/A')
            energy_count[e] = energy_count.get(e, 0) + 1

        metrics = [
            {"value": str(total_v), "label": "Véhicules"},
            {"value": str(total_t), "label": "Trajets"},
            {"value": f"{total_co2:.1f} kg", "label": "CO₂ Économisé"},
        ]

        sections = [
            {
                "title": "⚡ Répartition par Énergie",
                "chart": {
                    "type": "pie",
                    "data": {
                        "labels": list(energy_count.keys()),
                        "values": list(energy_count.values()),
                        "colors": ["#22c55e", "#3b82f6", "#a855f7"],
                    },
                    "title": "Types d'Énergie",
                },
            },
        ]

        summary = (
            f"Flotte de {total_v} véhicules avec {total_t} trajets enregistrés. "
            f"Économie totale de CO₂: {total_co2:.1f} kg. "
            + ", ".join([f"{v} {k}" for k, v in energy_count.items()]) + "."
        )

        return self.generate_custom_report(
            title="Rapport Mobilité & Véhicules",
            report_type="VÉHICULES — MOBILITÉ DURABLE",
            summary_text=summary,
            sections=sections,
            metrics=metrics,
        )

    def generate_citizen_report(self, citizens: List[Dict]) -> bytes:
        """Generate citizen engagement report"""
        total = len(citizens)
        avg_score = sum(c.get('Score', 0) or 0 for c in citizens) / max(total, 1)

        score_ranges = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
        for c in citizens:
            s = c.get('Score', 0) or 0
            if s <= 25: score_ranges["0-25"] += 1
            elif s <= 50: score_ranges["26-50"] += 1
            elif s <= 75: score_ranges["51-75"] += 1
            else: score_ranges["76-100"] += 1

        metrics = [
            {"value": str(total), "label": "Total Citoyens"},
            {"value": f"{avg_score:.0f}/100", "label": "Score Moyen"},
        ]

        citizen_rows = []
        for c in sorted(citizens, key=lambda x: x.get('Score', 0) or 0, reverse=True)[:20]:
            citizen_rows.append([
                str(c.get('Nom', 'N/A')),
                str(c.get('Email', 'N/A')),
                str(c.get('Score', 'N/A')),
                str(c.get('Préférences', 'N/A'))[:30],
            ])

        sections = [
            {
                "title": "📊 Distribution des Scores",
                "chart": {
                    "type": "bar",
                    "data": {
                        "labels": list(score_ranges.keys()),
                        "values": list(score_ranges.values()),
                        "colors": ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"],
                    },
                    "title": "Répartition des Scores d'Engagement",
                },
            },
            {
                "title": "🏆 Top 20 Citoyens Engagés",
                "table": {
                    "headers": ["Nom", "Email", "Score", "Préférences"],
                    "rows": citizen_rows,
                },
            },
        ]

        summary = (
            f"Ce rapport analyse l'engagement de {total} citoyens de Neo-Sousse. "
            f"Le score moyen d'engagement est de {avg_score:.0f}/100. "
            f"{score_ranges.get('76-100', 0)} citoyens ont un score excellent (>75)."
        )

        return self.generate_custom_report(
            title="Rapport Engagement Citoyen",
            report_type="CITOYENS — ENGAGEMENT",
            summary_text=summary,
            sections=sections,
            metrics=metrics,
        )

    def generate_global_analytics_report(self, data: Dict[str, Any]) -> bytes:
        """Generate comprehensive global analytics report"""
        sensors = data.get("sensors", [])
        interventions = data.get("interventions", [])
        vehicles = data.get("vehicles", [])
        trips = data.get("trips", [])
        citizens = data.get("citizens", [])
        alerts = data.get("alerts", [])

        metrics = [
            {"value": str(len(sensors)), "label": "Capteurs"},
            {"value": str(len(interventions)), "label": "Interventions"},
            {"value": str(len(vehicles)), "label": "Véhicules"},
            {"value": str(len(citizens)), "label": "Citoyens"},
        ]

        # Sensor status distribution
        sensor_status = {}
        for s in sensors:
            st = s.get('Statut', 'N/A')
            sensor_status[st] = sensor_status.get(st, 0) + 1

        intv_nature = {}
        for i in interventions:
            n = i.get('Nature', 'N/A')
            intv_nature[n] = intv_nature.get(n, 0) + 1

        sections = [
            {
                "title": "📡 Capteurs IoT",
                "content": f"{len(sensors)} capteurs déployés dans la ville de Neo-Sousse.",
                "chart": {
                    "type": "pie",
                    "data": {
                        "labels": list(sensor_status.keys()),
                        "values": list(sensor_status.values()),
                        "colors": ["#22c55e", "#f59e0b", "#ef4444", "#3b82f6"],
                    },
                    "title": "État des Capteurs",
                },
            },
            {
                "title": "🔧 Interventions",
                "content": f"{len(interventions)} interventions enregistrées.",
                "chart": {
                    "type": "bar",
                    "data": {
                        "labels": list(intv_nature.keys()),
                        "values": list(intv_nature.values()),
                        "colors": ["#3b82f6", "#f59e0b", "#a855f7"],
                    },
                    "title": "Interventions par Nature",
                },
            },
            {
                "title": "🚗 Mobilité",
                "content": (
                    f"{len(vehicles)} véhicules et {len(trips)} trajets. "
                    f"CO₂ économisé: {sum(float(t.get('ÉconomieCO2', 0) or 0) for t in trips):.1f} kg."
                ),
            },
            {
                "title": "👥 Citoyens",
                "content": (
                    f"{len(citizens)} citoyens enregistrés. "
                    f"Score moyen: {sum(c.get('Score', 0) or 0 for c in citizens) / max(len(citizens), 1):.0f}/100."
                ),
            },
        ]

        summary = (
            f"Rapport analytique global de la plateforme Neo-Sousse Smart City 2030. "
            f"Infrastructure: {len(sensors)} capteurs, {len(interventions)} interventions, "
            f"{len(vehicles)} véhicules, {len(citizens)} citoyens. "
            f"{'⚠️ ' + str(len(alerts)) + ' alertes actives nécessitant attention.' if alerts else '✅ Aucune alerte active.'}"
        )

        return self.generate_custom_report(
            title="Rapport Analytique Global",
            report_type="ANALYTICS — VUE D'ENSEMBLE",
            summary_text=summary,
            sections=sections,
            alerts=alerts,
            metrics=metrics,
        )
