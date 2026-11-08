"""Build data/tls_sources.json from the researcher's own TLS course materials (authored by the researcher; AI-assisted drafts).
Each material -> one source document: title + 8 evenly spaced declarative sentences (findings). Deterministic; SHA-256 recorded.
No student data is involved. Usage: py -3.12 -I -B -X utf8 build_tls_sources.py [max_docs]"""
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TLS = r"D:\proyek sekloah"
PATTERNS = [os.path.join(TLS, "alat", "prototipe", "question_engine", "kaidah", "materi_*.md"),
            os.path.join(TLS, "proses", "gemma_materi", "*", "draft", "materi_*.md")]
KEY = re.compile(r"materi_([a-z]+)_(\d+)_", re.I)
SENT = re.compile(r"(?<=[.!?])\s+")


def clean(line):
    line = re.sub(r"\*\*|__|`", "", line)
    line = re.sub(r"\[\[.*?\]\]", "", line)
    return line.strip()


def extract(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), os.path.basename(path))
    title = re.sub(r"^Materi\s+[^:]+:\s*", "", title)
    sents = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith(("#", "|", "[[", "*(Sumber", "Sumber:", "Status:", "---", "$$", "!", ">", "<")):
            continue
        for s in SENT.split(clean(line)):
            s = s.strip(" -*")
            letters = sum(c.isalpha() or c.isspace() for c in s)
            if 50 <= len(s) <= 350 and "$" not in s and "hlm" not in s.lower() and letters / len(s) > 0.88 and s[0].isupper():
                sents.append(s)
    return title, list(dict.fromkeys(sents))


def extract_docx(path):
    import docx
    ps = [p.text.strip() for p in docx.Document(path).paragraphs if p.text.strip()]
    title = next((p for p in ps[1:6] if len(p) < 90 and not p.startswith(("Ilmu", "AUDIT", "Gambar"))), os.path.basename(path))
    sents = []
    for p in ps:
        if len(p) < 200 or p.startswith(("(Sumber", "AUDIT", "Ilmu Pengetahuan", "Gambar", "Sumber")):
            continue
        for s in SENT.split(clean(p)):
            s = s.strip(" -*")
            letters = sum(c.isalpha() or c.isspace() for c in s)
            if 50 <= len(s) <= 350 and "$" not in s and "hlm" not in s.lower() and letters / len(s) > 0.88 and s[0].isupper():
                sents.append(s)
    return title, list(dict.fromkeys(sents))


def main():
    max_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    seen, cands = {}, []
    for pat in PATTERNS:
        for path in sorted(glob.glob(pat)):
            m = KEY.search(os.path.basename(path))
            if not m or (m.group(1).lower(), int(m.group(2))) in seen:
                continue
            title, sents = extract(path)
            if len(sents) >= 8:
                idx = [round(i * (len(sents) - 1) / 7) for i in range(8)]
                seen[(m.group(1).lower(), int(m.group(2)))] = True
                cands.append({"domain": m.group(1).lower(), "title": title, "findings": [sents[i] for i in idx], "methodology": [],
                              "region": "TLS", "src_file": os.path.relpath(path, TLS)})
    BIO = os.path.join(TLS, "laporan", "materi_tls", "biologi", "export_samples")
    seen_titles = set()
    for path in sorted(glob.glob(os.path.join(BIO, "*_sub*.docx"))):
        title, sents = extract_docx(path)
        dom = "biologi-" + os.path.basename(path).split("_sub")[0]
        if len(sents) >= 8 and (dom, title) not in seen_titles:
            seen_titles.add((dom, title))
            idx = [round(i * (len(sents) - 1) / 7) for i in range(8)]
            cands.append({"domain": dom, "title": title, "findings": [sents[i] for i in idx], "methodology": [], "region": "TLS",
                          "src_file": os.path.relpath(path, TLS)})
    by = {}
    for c in cands:
        by.setdefault(c["domain"], []).append(c)
    keep = [c for d, v in by.items() if len(v) >= 4 for c in v]
    keep.sort(key=lambda c: hashlib.sha256(c["src_file"].encode()).hexdigest())
    keep = sorted(keep[:max_docs], key=lambda c: (c["domain"], c["src_file"]))
    for i, c in enumerate(keep):
        c["doc_id"] = "S%03d" % i
    path = os.path.join(ROOT, "data", "tls_sources.json")
    json.dump({"model": "none (researcher-authored TLS materials; sentences extracted deterministically)", "docs": keep}, open(path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    open(path.replace(".json", ".sha256"), "w").write(h + "\n")
    print(len(keep), "docs;", {d: sum(1 for c in keep if c["domain"] == d) for d in sorted({c["domain"] for c in keep})}, h[:16])


if __name__ == "__main__":
    main()
