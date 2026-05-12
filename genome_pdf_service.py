"""
Genome Corporation - PDF Generation Microservice v2
Deploy on Render/Railway
Endpoint: POST /generate -> returns branded PDF binary
Logo file: genome_logo_original_clean.png (must be in same folder)
"""

from flask import Flask, request, send_file, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Flowable, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
import io, os

app = Flask(__name__)

# ── Brand Colors ──────────────────────────────────────────────
GOLD        = HexColor('#C8960C')
DARK_GREEN  = HexColor('#2D5016')
MID_GREEN   = HexColor('#3D6B20')
GREEN_LIGHT = HexColor('#EDF4E6')
CHARCOAL    = HexColor('#1C1C1C')
DARK_GREY   = HexColor('#3A3A3A')
MID_GREY    = HexColor('#6B6B6B')
LIGHT_GREY  = HexColor('#F2F2F2')
RULE_GREY   = HexColor('#DEDEDE')
WHITE       = colors.white
RED         = HexColor('#B83232')
AMBER       = HexColor('#D4760A')
GREEN_OK    = HexColor('#2E7D32')
AMBER_LIGHT = HexColor('#FFF3E0')
RED_LIGHT   = HexColor('#FDECEA')
GREEN_BG    = HexColor('#E8F5E9')
LIGHT_GOLD  = HexColor('#F5E9C0')

PAGE_W, PAGE_H = A4
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genome_logo_clean.png')

STATUS_MAP = {
    'Blocked':   (RED,      RED_LIGHT,   'ATTENTION REQUIRED'),
    'On Track':  (AMBER,    AMBER_LIGHT, 'ON TRACK'),
    'Completed': (GREEN_OK, GREEN_BG,    'COMPLETED'),
}


class ProgressBar(Flowable):
    def __init__(self, pct, width, height=8, fill=AMBER):
        Flowable.__init__(self)
        self.pct = pct; self.width = width
        self.height = height; self.fill = fill

    def draw(self):
        self.canv.setFillColor(HexColor('#E5E5E5'))
        self.canv.roundRect(0, 0, self.width, self.height, 3, fill=1, stroke=0)
        fw = max(6, self.width * self.pct / 100)
        self.canv.setFillColor(self.fill)
        self.canv.roundRect(0, 0, fw, self.height, 3, fill=1, stroke=0)


class SectionBar(Flowable):
    def __init__(self, title, width=None):
        Flowable.__init__(self)
        self.title = title
        self.width = width or (PAGE_W - 28*mm)
        self.height = 8*mm

    def draw(self):
        c = self.canv; w = self.width
        c.setFillColor(LIGHT_GREY)
        c.rect(0, 0, w, self.height, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.rect(0, 0, 3, self.height, fill=1, stroke=0)
        c.setFillColor(CHARCOAL)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(8*mm, 2.8*mm, self.title.upper())


class GoldRule(Flowable):
    def __init__(self, width=None):
        Flowable.__init__(self)
        self.width = width or (PAGE_W - 28*mm)
        self.height = 1

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, self.width, 0.8, fill=1, stroke=0)


def make_canvas_class(d):
    class HFC(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved = []

        def showPage(self):
            self._saved.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            n = len(self._saved)
            for state in self._saved:
                self.__dict__.update(state)
                self._draw(n)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def _draw(self, total):
            w, h = A4
            # White header
            self.setFillColor(WHITE)
            self.rect(0, h-40*mm, w, 40*mm, fill=1, stroke=0)
            # Charcoal top strip
            self.setFillColor(CHARCOAL)
            self.rect(0, h-2*mm, w, 2*mm, fill=1, stroke=0)
            # Logo
            if os.path.exists(LOGO_PATH):
                self.drawImage(LOGO_PATH, 10*mm, h-38*mm,
                    width=55*mm, height=34*mm,
                    preserveAspectRatio=True, mask='auto')
            # Vertical rule
            self.setStrokeColor(RULE_GREY)
            self.setLineWidth(0.5)
            self.line(72*mm, h-36*mm, 72*mm, h-7*mm)
            # Title
            self.setFillColor(CHARCOAL)
            self.setFont('Helvetica-Bold', 14)
            self.drawString(76*mm, h-16*mm, 'Site Progress Report')
            self.setFont('Helvetica', 8)
            self.setFillColor(MID_GREY)
            self.drawString(76*mm, h-22.5*mm, 'Daily Field Update  -  Confidential')
            # Meta right
            items = [
                ('DATE',    d.get('report_date', ''),   True),
                ('SITE ID', d.get('site_id', 'N/A'),    True),
                ('REF',     d.get('report_no', ''),     False),
            ]
            y = h - 13*mm
            for label, val, bold in items:
                self.setFillColor(MID_GREY)
                self.setFont('Helvetica', 7)
                self.drawRightString(w-10*mm, y, label)
                self.setFillColor(CHARCOAL)
                self.setFont('Helvetica-Bold' if bold else 'Helvetica', 8 if bold else 7.5)
                self.drawRightString(w-26*mm, y, str(val))
                y -= 8*mm
            # Gold bottom rule
            self.setFillColor(GOLD)
            self.rect(0, h-40*mm, w, 1.5, fill=1, stroke=0)
            # Footer
            self.setFillColor(CHARCOAL)
            self.rect(0, 0, w, 9*mm, fill=1, stroke=0)
            self.setFillColor(GOLD)
            self.rect(0, 0, 3, 9*mm, fill=1, stroke=0)
            self.setFillColor(HexColor('#AAAAAA'))
            self.setFont('Helvetica-Bold', 6.5)
            self.drawString(8*mm, 5.5*mm, 'GENOME CORPORATION')
            self.setFillColor(HexColor('#777777'))
            self.setFont('Helvetica', 6.5)
            self.drawString(8*mm, 2*mm, 'Auto-generated by Genome AI Operations System  |  Internal use only')
            self.setFillColor(GOLD)
            self.setFont('Helvetica-Bold', 8)
            self.drawRightString(w-10*mm, 3.5*mm, str(self._pageNumber) + ' / ' + str(total))
    return HFC


def build_pdf(d):
    buf = io.BytesIO()

    sc, sbg, sl = STATUS_MAP.get(d.get('status', 'On Track'), STATUS_MAP['On Track'])
    pct = int(d.get('progress_pct', 0) or 0)
    CWIDTH = PAGE_W - 28*mm

    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=45*mm, bottomMargin=15*mm,
        leftMargin=14*mm, rightMargin=14*mm)

    def S(name, **kw): return ParagraphStyle(name, **kw)
    slb  = S('LB', fontName='Helvetica-Bold', fontSize=7,   textColor=MID_GREY,  leading=10, spaceAfter=2)
    svl  = S('VL', fontName='Helvetica',      fontSize=9.5, textColor=CHARCOAL,  leading=14)
    svb  = S('VB', fontName='Helvetica-Bold', fontSize=9.5, textColor=CHARCOAL,  leading=14)
    sbd  = S('BD', fontName='Helvetica',      fontSize=9.5, textColor=DARK_GREY, leading=16)
    ssm  = S('SM', fontName='Helvetica',      fontSize=7.5, textColor=MID_GREY,  leading=11)

    story = [Spacer(1, 3*mm)]

    # ── Identity strip ────────────────────────────────────────
    it = Table([
        [Paragraph('CLIENT', slb), Paragraph('SITE / PHASE', slb), Paragraph('SUPERVISOR', slb)],
        [Paragraph(str(d.get('client_name', 'N/A')), svb),
         Paragraph(str(d.get('work_phase', 'N/A')), svl),
         Paragraph(str(d.get('supervisor_name', 'N/A')), svl)],
    ], colWidths=[68*mm, 88*mm, 27*mm])
    it.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 4),
        ('LINEBELOW',     (0,1),(-1,1),  0.5, RULE_GREY),
        ('LINEBELOW',     (0,0),(-1,0),  0.3, RULE_GREY),
        ('VALIGN',        (0,0),(-1,-1), 'BOTTOM'),
    ]))
    story += [it, Spacer(1, 6*mm)]

    # ── Status & Progress ─────────────────────────────────────
    story += [SectionBar('Status & Progress'), Spacer(1, 5*mm)]

    pill = Table([[Paragraph('  ' + sl + '  ',
        S('PL', fontName='Helvetica-Bold', fontSize=8.5, textColor=WHITE, leading=12))]],
        colWidths=[48*mm])
    pill.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), sc),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
    ]))

    lc = Table([
        [Paragraph('COMPLETION', slb)],
        [Spacer(1, 2*mm)],
        [ProgressBar(pct, 102*mm, 9, sc)],
        [Spacer(1, 2*mm)],
        [Paragraph(str(pct) + '%',
            S('PC', fontName='Helvetica-Bold', fontSize=28, textColor=sc, leading=32))],
    ], colWidths=[108*mm])
    lc.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ]))

    rc = Table([
        [Paragraph('STATUS', slb)], [pill], [Spacer(1, 4*mm)],
        [Paragraph('DATE', slb)],   [Paragraph(str(d.get('report_date', '')), svl)], [Spacer(1, 3*mm)],
        [Paragraph('TYPE', slb)],   [Paragraph('Daily EOD Update', svl)],
    ], colWidths=[69*mm])
    rc.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ]))

    sr = Table([[lc, rc]], colWidths=[112*mm, 71*mm])
    sr.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('LINEBEFORE',   (1,0),(1,0),   0.5, RULE_GREY),
        ('LEFTPADDING',  (1,0),(1,0),   10),
    ]))
    story += [sr, Spacer(1, 7*mm)]

    # ── Work Done ─────────────────────────────────────────────
    story += [SectionBar('Work Completed Today'), Spacer(1, 5*mm),
              Paragraph(str(d.get('raw_text', 'No details provided')), sbd),
              Spacer(1, 7*mm)]

    # ── Blockers ──────────────────────────────────────────────
    story.append(SectionBar('Blockers & Issues'))
    story.append(Spacer(1, 5*mm))
    bl = str(d.get('blockers', '')).strip()
    if bl and bl.lower() not in ('none', 'none reported', '', 'n/a'):
        story.append(Paragraph('WARNING - ISSUE IDENTIFIED',
            S('BH', fontName='Helvetica-Bold', fontSize=7.5,
              textColor=AMBER, leading=10, spaceAfter=4)))
        story.append(Table([[Paragraph(bl, sbd)]],
            colWidths=[CWIDTH - 6*mm],
            style=TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), AMBER_LIGHT),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
                ('RIGHTPADDING',  (0,0),(-1,-1), 8),
                ('TOPPADDING',    (0,0),(-1,-1), 10),
                ('BOTTOMPADDING', (0,0),(-1,-1), 10),
                ('LINEBEFORE',    (0,0),(0,-1),  3, AMBER),
            ])))
    else:
        story.append(Table([[Paragraph('No blockers reported for this update period.', sbd)]],
            colWidths=[CWIDTH - 6*mm],
            style=TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), GREEN_BG),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
                ('RIGHTPADDING',  (0,0),(-1,-1), 8),
                ('TOPPADDING',    (0,0),(-1,-1), 10),
                ('BOTTOMPADDING', (0,0),(-1,-1), 10),
                ('LINEBEFORE',    (0,0),(0,-1),  3, GREEN_OK),
            ])))
    story.append(Spacer(1, 7*mm))

    # ── Next Actions ──────────────────────────────────────────
    story.append(SectionBar('Next Actions Required'))
    story.append(Spacer(1, 5*mm))
    story.append(Table([[Paragraph(str(d.get('next_steps', 'N/A')), sbd)]],
        colWidths=[CWIDTH - 6*mm],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), GREEN_LIGHT),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('RIGHTPADDING',  (0,0),(-1,-1), 8),
            ('TOPPADDING',    (0,0),(-1,-1), 10),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('LINEBEFORE',    (0,0),(0,-1),  3, DARK_GREEN),
        ])))
    story += [Spacer(1, 9*mm), GoldRule(), Spacer(1, 3*mm)]

    # ── Bottom meta ───────────────────────────────────────────
    report_no = str(d.get('report_no', ''))
    bm = Table([[
        Paragraph('<b>Report No.</b>  ' + report_no, ssm),
        Paragraph('<b>Generated by</b>  Genome AI Operations System', ssm),
        Paragraph('<b>Classification</b>  Confidential',
            S('CR', fontName='Helvetica', fontSize=7.5,
              textColor=MID_GREY, leading=11, alignment=2)),
    ]], colWidths=[65*mm, 85*mm, 33*mm])
    bm.setStyle(TableStyle([
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ]))
    story.append(bm)

    doc.build(story, canvasmaker=make_canvas_class(d))
    buf.seek(0)
    return buf


@app.route('/generate', methods=['POST'])
def generate():
    try:
        d = request.get_json(force=True)
        if not d:
            return jsonify({'error': 'No JSON body received'}), 400
        buf = build_pdf(d)
        site_id = d.get('site_id', 'report')
        report_date = d.get('report_date', '').replace(' ', '-')
        filename = 'Genome-' + str(site_id) + '-' + report_date + '.pdf'
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True,
                         download_name=filename)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/health', methods=['GET'])
def health():
    logo_exists = os.path.exists(LOGO_PATH)
    return jsonify({
        'status': 'ok',
        'service': 'Genome PDF Service v2',
        'logo_found': logo_exists,
        'logo_path': LOGO_PATH
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
