"""Generate the frozen synthetic source corpus (fictional field briefings) with gemma4:31b-cloud.
No copyrighted text is used. Output: data/sources.json (+ SHA-256 in data/sources.sha256)."""
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import llm  # noqa: E402

MODEL = "gemma4:31b-cloud"
DOMAINS = ["river hydrology", "crop pathology", "coastal erosion", "urban transit logistics", "alloy fatigue testing",
           "rural telemedicine", "volcanic seismology", "fisheries stock assessment", "solar microgrids",
           "soil microbiology", "avalanche forecasting", "library archiving", "glacier mass balance", "wastewater epidemiology"]
REGIONS = ["Veldmoor", "Karsund", "Tamerlin", "Oskavik", "Brennhaven", "Quillara", "Dunmarrow", "Sathreya"]
SYSTEM = "You write concise, internally consistent FICTIONAL field briefings. Output valid JSON only."
PROMPT = ("Write a fictional field briefing about {domain} in the invented region '{region}' (document #{i}). "
          "Return JSON with keys: title (string), findings (list of exactly 8 sentences, each stating ONE distinct specific fact "
          "with a concrete number, date, or invented named entity; no sentence may repeat another), methodology (list of exactly 2 sentences "
          "describing how the evidence was gathered). Use plain English. Everything must be invented.")


def one(job):
    d, i, region = job
    for attempt in range(3):
        r = llm.chat(MODEL, SYSTEM, PROMPT.format(domain=d, region=region, i=i), temperature=0.8, seed=1000 + i, max_tokens=900, json_mode=True)
        try:
            obj = llm.parse_json(r["text"])
            f, m = obj["findings"], obj["methodology"]
            if len(f) == 8 and len(m) == 2 and all(isinstance(s, str) and 30 <= len(s) <= 400 for s in f + m):
                return {"domain": d, "region": region, "title": obj["title"].strip(), "findings": [s.strip() for s in f],
                        "methodology": [s.strip() for s in m]}
        except Exception:
            pass
    raise RuntimeError("generation failed for %s #%d" % (d, i))


def main():
    jobs = [(d, i, REGIONS[(k * 4 + i) % len(REGIONS)]) for k, d in enumerate(DOMAINS) for i in range(4)]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        docs = list(ex.map(one, jobs))
    for n, d in enumerate(docs):
        d["doc_id"] = "S%03d" % n
    path = os.path.join(os.path.dirname(HERE), "data", "sources.json")
    json.dump({"model": MODEL, "docs": docs}, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    open(path.replace(".json", ".sha256"), "w").write(h + "\n")
    print(len(docs), "docs", h[:16])


if __name__ == "__main__":
    main()
