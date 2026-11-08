"""Mengisi templat resmi Apart Research dengan teks + angka dari metrik.py. Keluaran: laporan/Swarm_Provenance_Report.docx"""
import copy
import os
import re
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lab  # noqa: E402
import metrik  # noqa: E402
from teks_laporan import isi_laporan  # noqa: E402

TEMPLAT = os.environ.get("APART_TEMPLATE_DOCX", "apart_submission_template.docx")   # download the official template from the Apart page
KELUAR = os.path.join(HERE, "laporan", "Swarm_Provenance_Report.docx")
FONT = "Old Standard TT"
UKURAN = Pt(10.5)


def set_font(run, nama=FONT, ukuran=UKURAN, bold=None, italic=None):
    run.font.name = nama
    run.font.size = ukuran
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), nama)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


SIMBOL = re.compile(r"([\u0370-\u03ff\u2212\u2229\u221a\u00b7]+)")
TOKEN = re.compile(r"(\*\*.+?\*\*|~~.+?~~|_\{.+?\}|\^\{.+?\})")


def tambah_run(par, teks, ukuran=UKURAN, nama=FONT):
    """Markup mini: **tebal**, ~~miring~~, _{subskrip}, ^{superskrip}."""
    for bagian in TOKEN.split(teks):
        if not bagian:
            continue
        if bagian.startswith("**"):
            set_font(par.add_run(bagian[2:-2]), nama, ukuran, bold=True)
        elif bagian.startswith("~~"):
            set_font(par.add_run(bagian[2:-2]), nama, ukuran, italic=True)
        elif bagian.startswith("_{"):
            r = par.add_run(bagian[2:-1])
            set_font(r, nama, ukuran)
            r.font.subscript = True
        elif bagian.startswith("^{"):
            r = par.add_run(bagian[2:-1])
            set_font(r, nama, ukuran)
            r.font.superscript = True
        else:
            for sub in SIMBOL.split(bagian):
                if not sub:
                    continue
                set_font(par.add_run(sub), "Cambria Math" if SIMBOL.fullmatch(sub) else nama, ukuran)


class Penyusun:
    def __init__(self, doc):
        self.doc = doc
        body = list(doc.element.body)
        self.proto = {}
        for el in body:
            if el.tag != qn("w:p"):
                continue
            teks = "".join(t.text or "" for t in el.iter(qn("w:t")))
            if teks.startswith("1. Introduction"):
                self.proto["h2"] = copy.deepcopy(el)
            elif teks.strip() == "Limitations":
                self.proto["h3"] = copy.deepcopy(el)
            elif teks.startswith("[First contribution"):
                self.proto["num"] = copy.deepcopy(el)
            elif teks.startswith("Code repository"):
                self.proto["bullet"] = copy.deepcopy(el)
            elif teks.startswith("[Reference 1]"):
                self.proto["ref"] = copy.deepcopy(el)
        self.normal = next(s for s in doc.styles if s.name == "normal")
        # buang kotak petunjuk + semua isi panduan setelahnya
        tabel_petunjuk = list(doc.element.body.iterchildren(qn("w:tbl")))[1]
        mulai = list(doc.element.body).index(tabel_petunjuk)
        sect = doc.element.body.find(qn("w:sectPr"))
        for el in list(doc.element.body)[mulai:]:
            if el is not sect:
                doc.element.body.remove(el)
        self.sect = sect

    def _taruh(self, el):
        self.sect.addprevious(el)
        return el

    def _klon(self, kunci, teks, ukuran=None):
        el = copy.deepcopy(self.proto[kunci])
        runs = el.findall(qn("w:r"))
        for r in runs[1:]:
            el.remove(r)
        t = runs[0].find(qn("w:t"))
        t.text = teks
        for extra in runs[0].findall(qn("w:br")):
            runs[0].remove(extra)
        return self._taruh(el)

    def h2(self, teks):
        self._klon("h2", teks)

    def h3(self, teks):
        self._klon("h3", teks)

    def par(self, teks, rata="justify", sesudah=6, ukuran=UKURAN, nama=FONT, miring_blok=False):
        p = self.doc.add_paragraph(style=self.normal)
        p.paragraph_format.space_after = Pt(sesudah)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.08
        p.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER}[rata]
        tambah_run(p, teks, ukuran, nama)
        return p

    def rumus(self, teks, nomor):
        from docx.enum.text import WD_TAB_ALIGNMENT
        p = self.doc.add_paragraph(style=self.normal)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.keep_together = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.tab_stops.add_tab_stop(Inches(3.25), WD_TAB_ALIGNMENT.CENTER)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
        set_font(p.add_run("\t"), "Cambria Math", Pt(10.5))
        tambah_run(p, teks, Pt(10.5), "Cambria Math")
        set_font(p.add_run("\t(%d)" % nomor), FONT, Pt(10))
        return p

    def daftar(self, kunci, item):
        for teks in item:
            el = copy.deepcopy(self.proto[kunci])
            runs = el.findall(qn("w:r"))
            for r in runs[1:]:
                el.remove(r)
            runs[0].find(qn("w:t")).text = ""
            self._taruh(el)
            from docx.text.paragraph import Paragraph
            p = Paragraph(el, self.doc._body)
            for r in list(p.runs):
                r._element.getparent().remove(r._element)
            tambah_run(p, teks, Pt(10))
            p.paragraph_format.space_after = Pt(3)

    def gambar(self, path, lebar, keterangan):
        p = self.doc.add_paragraph(style=self.normal)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Inches(lebar))
        self.par(keterangan, rata="justify", sesudah=8, ukuran=Pt(9))

    def tabel(self, baris, lebar_kolom, ukuran=Pt(8), judul=None, tebal_baris=()):
        if judul:
            self.par(judul, rata="justify", sesudah=3, ukuran=Pt(9)).paragraph_format.keep_with_next = True
        t = self.doc.add_table(rows=len(baris), cols=len(baris[0]))
        t.alignment = 1
        t.autofit = False
        tblPr = t._tbl.tblPr
        borders = tblPr.makeelement(qn("w:tblBorders"), {})
        for sisi in ("top", "bottom"):
            b = borders.makeelement(qn("w:" + sisi), {qn("w:val"): "single", qn("w:sz"): "8", qn("w:color"): "000000"})
            borders.append(b)
        tblPr.append(borders)
        for row_obj in t.rows:
            trPr = row_obj._tr.get_or_add_trPr()
            trPr.append(trPr.makeelement(qn("w:cantSplit"), {}))
        for i, row in enumerate(baris):
            for j, teks in enumerate(row):
                c = t.cell(i, j)
                c.width = Inches(lebar_kolom[j])
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.keep_with_next = i < len(baris) - 1
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                set_font(p.add_run(str(teks)), FONT, ukuran, bold=True if (i == 0 or i in tebal_baris) else None)
                if i == 0:
                    tcPr = c._tc.get_or_add_tcPr()
                    bt = tcPr.makeelement(qn("w:tcBorders"), {})
                    bb = bt.makeelement(qn("w:bottom"), {qn("w:val"): "single", qn("w:sz"): "6", qn("w:color"): "000000"})
                    bt.append(bb)
                    tcPr.append(bt)
        self.par("", sesudah=4, ukuran=Pt(4))
        return t


def isi_judul_penulis(doc, judul, abstrak):
    t0 = doc.tables[0]._tbl
    for tb in t0.iter(qn("w:tbl")):
        if tb.find(".//" + qn("w:tbl")) is not None:
            continue                                   # lewati tabel luar; ambil tabel terdalam
        if any((tt.text or "") == "Author name 1" for tt in tb.iter(qn("w:t"))):
            lebar = "3600"
            for tag in ("w:tblW", "w:tcW"):
                for e in tb.iter(qn(tag)):
                    e.set(qn("w:w"), lebar)
                    e.set(qn("w:type"), "dxa")
            for e in tb.iter(qn("w:gridCol")):
                e.set(qn("w:w"), lebar)
            break
    nodes = list(t0.iter(qn("w:t")))
    peta = {"PROJECT TITLE": judul, "Author name 1": "[Name]", "Affiliation": ""}
    for n in nodes:
        if n.text in peta:
            n.text = peta[n.text]
        elif re.match(r"Author name [2-6]$", n.text or ""):
            n.text = ""
    nodes[2].text = "[Affiliation]"
    # abstrak: ganti teks panduan (tiga node terakhir) dengan abstrak, tanpa miring
    teks_abs = [n for n in nodes if n.text and (n.text.startswith("Summarize your project") or n.text.startswith("Make sure to cover") or n.text.startswith(". Polish"))]
    teks_abs[0].text = abstrak
    for n in teks_abs[1:]:
        n.text = ""
    for r in t0.iter(qn("w:r")):
        if any(tt in teks_abs for tt in r.iter(qn("w:t"))):
            rpr = r.find(qn("w:rPr"))
            if rpr is not None:
                for tag in ("w:sz", "w:szCs"):
                    e = rpr.find(qn(tag))
                    if e is None:
                        e = rpr.makeelement(qn(tag), {})
                        rpr.append(e)
                    e.set(qn("w:val"), "20")
                for tag in ("w:i", "w:iCs"):
                    e = rpr.find(qn(tag))
                    if e is not None:
                        rpr.remove(e)


def perbaiki_catatan_kaki(path):
    """Templat bawaan menyebut sprint lain di catatan kaki; ganti ke sprint ini (teks + tautan)."""
    import shutil
    import zipfile
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = data.decode("utf-8").replace("AI x Epistemics Research Sprint", "Swarm Alignment Hackathon").encode("utf-8")
            elif item.filename == "word/_rels/footnotes.xml.rels":
                data = re.sub(rb'Target="https?://[^"]*"', b'Target="https://apartresearch.com/sprints/swarm-alignment-2026"', data)
            zout.writestr(item, data)
    shutil.move(tmp, path)


def main():
    M = metrik.hitung()
    doc = docx.Document(TEMPLAT)
    S = Penyusun(doc)
    judul, abstrak = isi_laporan(S, M, os.path.join(HERE, "laporan"))
    isi_judul_penulis(doc, judul, abstrak)
    doc.save(KELUAR)
    perbaiki_catatan_kaki(KELUAR)
    print("ditulis", KELUAR, "| kata abstrak:", len(abstrak.split()))


if __name__ == "__main__":
    main()
