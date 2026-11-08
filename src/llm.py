"""Thin Ollama client (local server localhost:11434). Cloud-tagged models are served through the same API
but run on remote hardware (NOT the local GPU); embeddings run on the local GPU. English only."""
import json
import time
import urllib.request

URL = "http://localhost:11434"


def _post(path, payload, timeout):
    req = urllib.request.Request(URL + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(model, system, user, temperature=0.0, seed=0, max_tokens=900, timeout=240, retries=3, json_mode=False):
    """Return dict(text, seconds, model, eval_count). Raises RuntimeError after retries."""
    payload = {"model": model, "stream": False, "think": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens}}
    if json_mode:
        payload["format"] = "json"
    last = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            r = _post("/api/chat", payload, timeout)
            return {"text": r["message"]["content"], "seconds": round(time.time() - t0, 2), "model": r.get("model", model),
                    "eval_count": r.get("eval_count"), "prompt_eval_count": r.get("prompt_eval_count")}
        except Exception as exc:  # network / server errors: retry with backoff
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("chat failed for %s: %r" % (model, last))


def embed(model, texts, timeout=300):
    """Return list of L2-normalised float vectors (computed by the local Ollama server, GPU when available)."""
    r = _post("/api/embed", {"model": model, "input": texts}, timeout)
    out = []
    for v in r["embeddings"]:
        n = sum(x * x for x in v) ** 0.5 or 1.0
        out.append([x / n for x in v])
    return out


# ---- OpenAI-compatible provider (Alibaba DashScope / Qwen). Key comes ONLY from the environment; never logged. ----
import os

DASHSCOPE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"


def chat_dashscope(model, system, user, temperature=0.0, seed=0, max_tokens=900, timeout=240, retries=3):
    key = os.environ.get("DASHSCOPE_API_KEY")
    if not key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set")
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "temperature": temperature, "seed": seed, "max_tokens": max_tokens, "enable_thinking": False}
    last = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(DASHSCOPE_URL, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                r = json.loads(resp.read().decode("utf-8"))
            return {"text": r["choices"][0]["message"]["content"], "seconds": round(time.time() - t0, 2),
                    "model": r.get("model", model), "eval_count": r.get("usage", {}).get("completion_tokens"),
                    "prompt_eval_count": r.get("usage", {}).get("prompt_tokens")}
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("dashscope chat failed for %s: %s" % (model, type(last).__name__ + " " + str(getattr(last, "code", ""))))


# ---- Alibaba Model Studio TOKEN PLAN (key format sk-sp-). Must be paired with its own base URL; the pay-as-you-go URL above
# answers 401 for these keys. Key source: env TOKENPLAN_API_KEY, else the file named by env TOKENPLAN_KEY_FILE. Never logged. ----
TOKENPLAN_URL = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1/chat/completions"


def _tokenplan_key():
    key = os.environ.get("TOKENPLAN_API_KEY", "").strip()
    if not key and os.environ.get("TOKENPLAN_KEY_FILE"):
        with open(os.environ["TOKENPLAN_KEY_FILE"], encoding="utf-8") as fh:
            key = fh.read().strip()
    if not key.startswith("sk-sp-"):
        raise RuntimeError("Token Plan key missing: set TOKENPLAN_API_KEY or TOKENPLAN_KEY_FILE (key must start with sk-sp-)")
    return key


def chat_tokenplan(model, system, user, temperature=0.0, seed=0, max_tokens=900, timeout=240, retries=3):
    key = _tokenplan_key()
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "temperature": temperature, "seed": seed, "max_tokens": max_tokens, "enable_thinking": False}
    last = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(TOKENPLAN_URL, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                r = json.loads(resp.read().decode("utf-8"))
            return {"text": r["choices"][0]["message"]["content"], "seconds": round(time.time() - t0, 2),
                    "model": r.get("model", model), "eval_count": r.get("usage", {}).get("completion_tokens"),
                    "prompt_eval_count": r.get("usage", {}).get("prompt_tokens")}
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("tokenplan chat failed for %s: %s" % (model, type(last).__name__ + " " + str(getattr(last, "code", ""))))


def chat_any(model, system, user, **kw):
    """Route by model prefix: 'tp:<id>' -> Token Plan, 'ds:<id>' -> DashScope pay-as-you-go, otherwise Ollama."""
    if model.startswith("tp:"):
        return chat_tokenplan(model[3:], system, user, **{k: v for k, v in kw.items() if k != "json_mode"})
    if model.startswith("ds:"):
        return chat_dashscope(model[3:], system, user, **{k: v for k, v in kw.items() if k != "json_mode"})
    return chat(model, system, user, **kw)


def parse_json(text):
    """Tolerant JSON extraction: strips markdown fences, takes the outermost {...}. Raises ValueError if absent."""
    s = text.strip()
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object in model output")
    return json.loads(s[a:b + 1])
