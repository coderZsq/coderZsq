"""Render the editable Markdown resume with the visual system in DESIGN.md."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT
SOURCE = OUTPUT / '朱双泉-全栈工程师.md'
TARGET = OUTPUT / '朱双泉-全栈工程师.pdf'
pdfmetrics.registerFont(TTFont('ResumeSC', '/System/Library/Fonts/STHeiti Light.ttc', subfontIndex=1))
pdfmetrics.registerFont(TTFont('ResumeSCBold', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))
pdfmetrics.registerFontFamily('ResumeSC', normal='ResumeSC', bold='ResumeSCBold', italic='ResumeSC', boldItalic='ResumeSCBold')
INK = colors.HexColor('#272622')
MUTED = colors.HexColor('#66635d')
ACCENT = colors.HexColor('#98543f')
LINE = colors.HexColor('#e3e0da')
WIDTH = A4[0] - 100
styles = {}
for key, settings in {
    'name': dict(fontSize=28, leading=34, fontName='ResumeSCBold'),
    'role': dict(fontSize=14, leading=22, textColor=ACCENT),
    'meta': dict(fontSize=8.6, leading=14, textColor=MUTED),
    'section': dict(fontSize=11.4, leading=17, fontName='ResumeSCBold', spaceBefore=17, spaceAfter=6),
    'company': dict(fontSize=11, leading=16, fontName='ResumeSCBold'),
    'date': dict(fontSize=9, leading=16, textColor=MUTED, alignment=TA_RIGHT),
    'position': dict(fontSize=9.3, leading=15, textColor=MUTED, spaceAfter=6, keepWithNext=True),
    'project': dict(fontSize=10.5, leading=17, fontName='ResumeSCBold', spaceBefore=10, spaceAfter=7, keepWithNext=True),
    'body': dict(fontSize=11, leading=19, spaceAfter=9),
    'bullet': dict(fontSize=11, leading=19, leftIndent=9, firstLineIndent=-9, spaceAfter=8),
    'skill': dict(fontSize=9.6, leading=16, spaceAfter=4),
}.items():
    defaults = dict(fontName='ResumeSC', textColor=INK, wordWrap='CJK', splitLongWords=False)
    defaults.update(settings)
    styles[key] = ParagraphStyle(key, **defaults)


def inline(value):
    value = escape(value.strip())
    value = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#98543f">\1</link>', value)
    value = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', value)
    # Give Latin copy native metrics instead of the CJK font's substitute glyphs.
    parts = re.split(r'(<[^>]+>)', value)
    bold = False
    for i, part in enumerate(parts):
        if part == '<b>': bold = True
        elif part == '</b>': bold = False
        elif not part.startswith('<'):
            face = 'Helvetica-Bold' if bold else 'Helvetica'
            parts[i] = re.sub(r'[A-Za-z0-9][A-Za-z0-9 .+/@_-]*', lambda m: f'<font name="{face}">{m.group(0)}</font>', part)
    return ''.join(parts)


def para(text, key='body'):
    return Paragraph(inline(text), styles[key])


def section(text):
    return [para(text, 'section'), HRFlowable(width='100%', thickness=.55, color=LINE, spaceAfter=8)]


def page(canvas, doc):
    w, h = A4
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont('ResumeSC', 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(50, h-29, '朱双泉  /  全栈工程师')
    canvas.setStrokeColor(LINE)
    canvas.line(50, 31, w-50, 31)
    canvas.setFillColor(MUTED)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(50, 19, 'ZHU SHUANGQUAN')
    canvas.drawRightString(w-50, 19, f'{doc.page} / 2')
    canvas.restoreState()


lines = [line.strip() for line in SOURCE.read_text(encoding='utf-8').splitlines() if line.strip()]
story = []
header = Table([[para('朱双泉', 'name'), para('全栈工程师', 'role')]], colWidths=[108, WIDTH-108])
header.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),('VALIGN',(0,0),(-1,-1),'BOTTOM')]))
story += [header, Spacer(1, 9)]
for line in lines[1:4]:
    if line.startswith('求职意向：'):
        line = line.split('|',1)[1].strip()
    story.append(para(line, 'meta'))
story.append(Spacer(1, 1))
in_skills = False
continued = False
i = 4
while i < len(lines):
    line = lines[i]
    if line == '## 工作与项目经历（续）':
        continued = True
        story.append(PageBreak())
    if line.startswith('## '):
        title=line[3:]
        in_skills = title == '技术实践'
        story += section(title)
    elif line.startswith('### '):
        company, position = line[4:].split(' | ',1)
        date = lines[i+1]
        row=Table([[para(company,'company'),para(date,'date')]],colWidths=[WIDTH-120,120])
        row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),('VALIGN',(0,0),(-1,-1),'TOP')]))
        row.keepWithNext = True
        story += [Spacer(1,22 if continued else 10),row,para(position,'position')]
        i += 1
    elif line.startswith('**项目：'):
        story.append(para(line.replace('项目：','',1),'project'))
    elif line.startswith('**') and line.endswith('**'):
        story.append(para(line, 'project'))
    elif line.startswith('- '):
        if in_skills:
            story.append(para(line[2:], 'skill'))
        else:
            story.append(Paragraph('<font color="#98543f">&#8226;</font> '+inline(line[2:]),styles['bullet']))
    else:
        story.append(para(line))
    i += 1

doc=SimpleDocTemplate(str(TARGET), pagesize=A4, leftMargin=44, rightMargin=44, topMargin=40, bottomMargin=45, title='朱双泉 - 全栈工程师',author='朱双泉')
doc.build(story,onFirstPage=page,onLaterPages=page)
