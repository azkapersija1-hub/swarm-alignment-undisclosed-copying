"""Minimal Markdown -> DOCX converter (headings, paragraphs, bullet lists, pipe tables, images, bold/code spans). Usage: md_to_docx.py in.md out.docx"""
import os
import re
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")


def add_runs(par, text):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9)
        else:
            par.add_run(part)


def convert(src, dst):
    d = docx.Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    base = os.path.dirname(os.path.abspath(src))
    lines = open(src, encoding="utf-8").read().split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
            body = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                body.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = d.add_table(rows=1, cols=len(hdr))
            t.style = "Light Grid Accent 1"
            for j, h in enumerate(hdr):
                c = t.rows[0].cells[j]
                c.text = ""
                add_runs(c.paragraphs[0], h)
                for r in c.paragraphs[0].runs:
                    r.bold = True
                    r.font.size = Pt(8.5)
            for row in body:
                cells = t.add_row().cells
                for j in range(len(hdr)):
                    cells[j].text = ""
                    add_runs(cells[j].paragraphs[0], row[j] if j < len(row) else "")
                    for r in cells[j].paragraphs[0].runs:
                        r.font.size = Pt(8.5)
            d.add_paragraph()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            d.add_heading(m.group(2), level=len(m.group(1)))
        elif re.match(r"^!\[.*\]\(.*\)", ln):
            path = re.match(r"^!\[.*\]\((.*)\)", ln).group(1)
            p = path if os.path.isabs(path) else os.path.join(base, path)
            if os.path.isfile(p):
                d.add_picture(p, width=Inches(6.4))
                d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif re.match(r"^\s*[-*]\s+", ln):
            add_runs(d.add_paragraph(style="List Bullet"), re.sub(r"^\s*[-*]\s+", "", ln))
        elif re.match(r"^\s*\d+\.\s+", ln):
            add_runs(d.add_paragraph(style="List Number"), re.sub(r"^\s*\d+\.\s+", "", ln))
        elif ln.startswith(">"):
            p = d.add_paragraph()
            add_runs(p, ln.lstrip("> ").strip())
            p.paragraph_format.left_indent = Inches(0.3)
        elif ln.strip():
            add_runs(d.add_paragraph(), ln)
        i += 1
    d.save(dst)


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
    print("saved", sys.argv[2])
