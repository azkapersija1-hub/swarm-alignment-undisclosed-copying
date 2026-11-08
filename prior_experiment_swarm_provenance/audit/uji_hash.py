"""Menguji apakah temukan_kembar_global (kode lama) memberi pasangan sama di proses Python berbeda.
Pemakaian: uji_hash.py <folder_kode> <berkas_potongan.json> <keluar.json>"""
import hashlib, json, os, sys, time
sys.path.insert(0, sys.argv[1])
import jalankan as J
t = time.time()
if not os.path.isfile(sys.argv[2]):
    json.dump(J._semua_potongan(), open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
semua = json.load(open(sys.argv[2], encoding="utf-8"))
pas = J.temukan_kembar_global(semua)
ids = sorted((semua[x]["id"], semua[y]["id"]) for x, y in pas)
json.dump(ids, open(sys.argv[3], "w"))
print(os.environ.get("PYTHONHASHSEED"), len(ids), hashlib.sha1(json.dumps(ids).encode()).hexdigest()[:10], "%.0fs" % (time.time() - t))
