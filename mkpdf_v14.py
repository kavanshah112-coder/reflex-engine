# -*- coding: utf-8 -*-
# origin: new for V1.3 -- report PDF
"""Renders V1_4_REPORT.md to a PDF.

A small Markdown subset is enough for the report's own shapes:
headings, paragraphs, bullet and numbered lists, fenced/indented code,
blockquotes, pipe tables, horizontal rules, and inline bold/italic/code.
Anything unrecognised is emitted as plain text rather than dropped, so
the PDF can never be quietly shorter than the source.
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, KeepTogether, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = Path(__file__).resolve().parent
SRC = HERE / "V1_4_REPORT.md"
OUT = HERE / "V1_4_REPORT.pdf"

INK = colors.HexColor("#16181d")
MUTED = colors.HexColor("#5b6270")
RULE = colors.HexColor("#d8dbe2")
ACCENT = colors.HexColor("#8c2f2f")
CODEBG = colors.HexColor("#f4f4f6")
HDRBG = colors.HexColor("#eceef2")

ss = getSampleStyleSheet()


def st(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.4, leading=13.6,
                textColor=INK, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, parent=ss["Normal"], **base)


S = {
    "h1": st("h1", fontName="Helvetica-Bold", fontSize=19, leading=23,
             spaceBefore=2, spaceAfter=8),
    "h2": st("h2", fontName="Helvetica-Bold", fontSize=13.2,
             leading=16.5, spaceBefore=15, spaceAfter=6,
             textColor=ACCENT),
    "h3": st("h3", fontName="Helvetica-Bold", fontSize=10.6,
             leading=14, spaceBefore=10, spaceAfter=4),
    "p": st("p", spaceAfter=6),
    "li": st("li", leftIndent=11, bulletIndent=2, spaceAfter=3.2),
    "code": st("code", fontName="Courier", fontSize=8.0, leading=10.4,
               leftIndent=7, textColor=colors.HexColor("#2a2d34")),
    "quote": st("quote", leftIndent=11, fontName="Helvetica-Oblique",
                textColor=MUTED, spaceAfter=6),
    "cell": st("cell", fontSize=8.2, leading=11),
    "cellh": st("cellh", fontSize=8.2, leading=11,
                fontName="Helvetica-Bold"),
}

INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)"), r"<i>\1</i>"),
    (re.compile(r"`([^`]+?)`"), r'<font face="Courier">\1</font>'),
]


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def inline(t):
    t = esc(t)
    for rx, rep in INLINE:
        t = rx.sub(rep, t)
    return t.replace("—", "&#8212;").replace("→", "&#8594;")


def table_from(rows):
    body = [r for r in rows if not re.match(r"^\|[\s:|-]+\|$", r)]
    grid = []
    for r in body:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        grid.append(cells)
    if not grid:
        return None
    width = max(len(r) for r in grid)
    data = []
    for i, r in enumerate(grid):
        r = r + [""] * (width - len(r))
        sty = S["cellh"] if i == 0 else S["cell"]
        data.append([Paragraph(inline(c), sty) for c in r])
    avail = 170 * mm
    t = Table(data, colWidths=[avail / width] * width, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDRBG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return t


def build():
    lines = SRC.read_text(encoding="utf-8").split("\n")
    flow = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            flow.append(codeblock(buf))
            continue

        if s.startswith("|") and s.endswith("|"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                buf.append(lines[i])
                i += 1
            t = table_from(buf)
            if t is not None:
                flow.append(Spacer(1, 3))
                flow.append(t)
                flow.append(Spacer(1, 7))
            continue

        if ln.startswith("    ") and s:
            buf = []
            while i < len(lines) and (lines[i].startswith("    ")
                                      or not lines[i].strip()):
                if lines[i].strip() or (
                        i + 1 < len(lines)
                        and lines[i + 1].startswith("    ")):
                    buf.append(lines[i][4:])
                    i += 1
                else:
                    break
            flow.append(codeblock(buf))
            continue

        if s.startswith("# "):
            flow.append(Paragraph(inline(s[2:]), S["h1"]))
        elif s.startswith("## "):
            flow.append(Paragraph(inline(s[3:]), S["h2"]))
        elif s.startswith("### "):
            flow.append(Paragraph(inline(s[4:]), S["h3"]))
        elif s in ("---", "***", "___"):
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width="100%", thickness=0.5,
                                   color=RULE))
            flow.append(Spacer(1, 6))
        elif s.startswith("> "):
            flow.append(Paragraph(inline(s[2:]), S["quote"]))
        elif s.startswith("- ") or s.startswith("* "):
            flow.append(Paragraph(inline(s[2:]), S["li"],
                                  bulletText="•"))
        elif re.match(r"^\d+\.\s", s):
            n, rest = s.split(".", 1)
            flow.append(Paragraph(inline(rest.strip()), S["li"],
                                  bulletText=n + "."))
        elif s:
            flow.append(Paragraph(inline(s), S["p"]))
        i += 1
    return flow


def codeblock(buf):
    while buf and not buf[0].strip():
        buf.pop(0)
    while buf and not buf[-1].strip():
        buf.pop()
    txt = "<br/>".join(esc(b).replace(" ", "&nbsp;") for b in buf)
    t = Table([[Paragraph(txt, S["code"])]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODEBG),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 7)])


def footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 7.4)
    canv.setFillColor(MUTED)
    canv.drawString(20 * mm, 12 * mm,
                    "Reflex Engine · V1.4 · INTERIM")
    canv.drawRightString(190 * mm, 12 * mm, "%d" % doc.page)
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.4)
    canv.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
    canv.restoreState()


def main():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title="Reflex Engine V1.3 - Reading Real Language Safely",
        author="Reflex Engine research arc")
    doc.build(build(), onFirstPage=footer, onLaterPages=footer)
    print("wrote", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
