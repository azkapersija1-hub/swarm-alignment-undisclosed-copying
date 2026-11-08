"""Provenance ledger with a SHA-256 hash chain. Integrity != authentication: no signatures are used here."""
import hashlib
import json


def _h(prev, payload):
    return hashlib.sha256((prev + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode("utf-8")).hexdigest()


class Ledger:
    GENESIS = "0" * 64

    def __init__(self, events=None):
        self.events = events or []

    def log(self, kind, agent_id, **data):
        prev = self.events[-1]["hash"] if self.events else self.GENESIS
        payload = {"n": len(self.events), "kind": kind, "agent": agent_id, "data": data}
        self.events.append(dict(payload, prev=prev, hash=_h(prev, payload)))
        return self.events[-1]

    @staticmethod
    def verify(events):
        """Return (ok, first_bad_index). Detects edits, deletions and reordering of earlier events."""
        prev = Ledger.GENESIS
        for i, e in enumerate(events):
            payload = {k: e[k] for k in ("n", "kind", "agent", "data")}
            if e["prev"] != prev or e["hash"] != _h(prev, payload) or e["n"] != i:
                return False, i
            prev = e["hash"]
        return True, None
