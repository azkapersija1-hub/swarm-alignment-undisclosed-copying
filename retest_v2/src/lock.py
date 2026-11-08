"""Pre-registration lock: record and verify SHA-256 hashes of files that must not change after a stage is locked.
Usage: lock.py write <stage> <file> [<file> ...]   |   lock.py verify <stage>"""
import datetime
import hashlib
import json
import os
import sys

RT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(RT, "prereg")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lock_path(stage):
    return os.path.join(PREREG, "PREREG_LOCK_%s.json" % stage)


def write(stage, files):
    def inside(f):
        try:
            return os.path.commonpath([os.path.normcase(os.path.abspath(f)), os.path.normcase(RT)]) == os.path.normcase(RT)
        except ValueError:          # different drives
            return False
    entries = {os.path.relpath(f, RT) if inside(f) else os.path.abspath(f): sha(f) for f in files}
    doc = {"stage": stage, "locked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "files": entries}
    with open(lock_path(stage), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return doc


def verify(stage):
    doc = json.load(open(lock_path(stage), encoding="utf-8"))
    bad = []
    for rel, digest in doc["files"].items():
        path = rel if os.path.isabs(rel) else os.path.join(RT, rel)
        if not os.path.isfile(path) or sha(path) != digest:
            bad.append(rel)
    return bad


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "write":
        d = write(sys.argv[2], [os.path.abspath(f) for f in sys.argv[3:]])
        print("locked", d["stage"], "at", d["locked_at_utc"], "files:", len(d["files"]))
    else:
        bad = verify(sys.argv[2])
        print("OK: all hashes match" if not bad else "CHANGED AFTER LOCK: %s" % bad)
        sys.exit(1 if bad else 0)
