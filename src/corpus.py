"""Frozen synthetic corpus: base sources, honest twins (identical body, other publisher) and near-duplicates."""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("SWARM_DATASET", "synthetic")           # "synthetic" (default) or "tls"
SUFFIX = "" if DATASET == "synthetic" else "_" + DATASET            # keeps result folders separate
DATA = os.path.join(os.path.dirname(HERE), "data", "sources.json" if DATASET == "synthetic" else "%s_sources.json" % DATASET)
PUBLISHERS = {"base": "Regional Survey Office", "twin": "Continental Data Archive", "near": "Field Digest Quarterly"}


def _rank(doc_id):
    return hashlib.sha256(("rank|" + doc_id).encode()).hexdigest()


def load_catalog():
    """Return (catalog, families). catalog[id] = dict(id, kind, base, domain, title, findings, methodology, publisher)."""
    docs = json.load(open(DATA, encoding="utf-8"))["docs"]
    order = sorted(docs, key=lambda d: _rank(d["doc_id"]))
    n_twin, n_near = (24, 12) if DATASET == "synthetic" else (round(0.4 * len(docs)), round(0.2 * len(docs)))
    twin_set = {d["doc_id"] for d in order[:n_twin]}
    near_set = {d["doc_id"] for d in order[n_twin:n_twin + n_near]}
    cat, fam = {}, {}
    for d in docs:
        cat[d["doc_id"]] = {"id": d["doc_id"], "kind": "base", "base": d["doc_id"], "domain": d["domain"], "title": d["title"],
                            "findings": d["findings"], "methodology": d["methodology"], "publisher": PUBLISHERS["base"]}
        fam[d["doc_id"]] = [d["doc_id"]]
        if d["doc_id"] in twin_set:
            tid = "T" + d["doc_id"][1:]
            cat[tid] = dict(cat[d["doc_id"]], id=tid, kind="twin", publisher=PUBLISHERS["twin"])
            fam[d["doc_id"]].append(tid)
        if d["doc_id"] in near_set:
            f = list(d["findings"])
            f[0], f[1] = f[1], f[0]
            f = [x for i, x in enumerate(f) if i not in (3, 6)]
            nid = "N" + d["doc_id"][1:]
            cat[nid] = dict(cat[d["doc_id"]], id=nid, kind="near", findings=f, publisher=PUBLISHERS["near"])
            fam[d["doc_id"]].append(nid)
    return cat, fam


def render(src):
    f = "\n".join("%d. %s" % (i + 1, s) for i, s in enumerate(src["findings"]))
    m = "\n".join("- " + s for s in src["methodology"])
    return "SOURCE %s | %s\nTITLE: %s\nFINDINGS:\n%s\nMETHODOLOGY:\n%s" % (src["id"], src["publisher"], src["title"], f, m)


def body_hash(src):
    """Hash of the content body only (publisher and id excluded): equal for honest twins."""
    body = "\n".join(src["findings"] + src["methodology"]).lower()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
