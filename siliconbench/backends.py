"""Backends: talk to a local model server and return timing information for one generation.

Ollama is the default (https://ollama.com). Any OpenAI-compatible local server (llama.cpp `llama-server`,
LM Studio, mlx_lm.server) works through the `openai` backend. Only the Python standard library is used."""
import json, time, urllib.request
from dataclasses import dataclass, field

@dataclass
class Result:
    text: str
    ttft_s: float                 # time to first token (prompt processing + first step)
    total_s: float                # wall time for the whole request
    prompt_tokens: int = 0
    output_tokens: int = 0
    prompt_tps: float = 0.0       # prompt tokens per second (prefill)
    decode_tps: float = 0.0       # generated tokens per second (after the first token)
    extra: dict = field(default_factory=dict)

def _post_stream(url, payload, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)

class Ollama:
    name = "ollama"
    def __init__(self, host="http://localhost:11434"):
        self.host = host.rstrip("/")
    def generate(self, model, prompt, max_tokens=256, temperature=0.0, seed=0, num_ctx=4096):
        payload = dict(model=model, prompt=prompt, stream=True,
                       options=dict(temperature=temperature, seed=seed, num_predict=max_tokens, num_ctx=num_ctx))
        t0 = time.perf_counter(); first = None; parts = []; final = {}
        with _post_stream(f"{self.host}/api/generate", payload) as r:
            for line in r:
                if not line.strip():
                    continue
                ev = json.loads(line)
                if ev.get("response"):
                    if first is None:
                        first = time.perf_counter()
                    parts.append(ev["response"])
                if ev.get("done"):
                    final = ev
        t1 = time.perf_counter()
        ns = 1e-9
        pc, pd = final.get("prompt_eval_count", 0), final.get("prompt_eval_duration", 0) * ns
        ec, ed = final.get("eval_count", 0), final.get("eval_duration", 0) * ns
        return Result(text="".join(parts), ttft_s=(first or t1) - t0, total_s=t1 - t0, prompt_tokens=pc, output_tokens=ec,
                      prompt_tps=pc / pd if pd else 0.0, decode_tps=ec / ed if ed else 0.0,
                      extra=dict(load_s=final.get("load_duration", 0) * ns))
    def memory(self, model):
        """Bytes the server reports for the loaded model (weights + KV cache), from /api/ps."""
        try:
            with urllib.request.urlopen(f"{self.host}/api/ps", timeout=10) as r:
                for m in json.load(r).get("models", []):
                    if m.get("name") == model or m.get("model") == model:
                        return dict(size_bytes=m.get("size", 0), vram_bytes=m.get("size_vram", 0))
        except OSError:
            pass
        return {}
    def unload(self, model):
        try:
            _post_stream(f"{self.host}/api/generate", dict(model=model, keep_alive=0)).read()
        except OSError:
            pass

class OpenAICompat:
    """Any server with POST /v1/chat/completions and streaming (llama.cpp, LM Studio, mlx_lm.server)."""
    name = "openai"
    def __init__(self, host="http://localhost:8080"):
        self.host = host.rstrip("/")
    def generate(self, model, prompt, max_tokens=256, temperature=0.0, seed=0, num_ctx=None):
        payload = dict(model=model, messages=[{"role": "user", "content": prompt}], stream=True, max_tokens=max_tokens,
                       temperature=temperature, seed=seed, stream_options={"include_usage": True})
        t0 = time.perf_counter(); first = None; parts = []; usage = {}
        with _post_stream(f"{self.host}/v1/chat/completions", payload) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data:") or line.endswith("[DONE]"):
                    continue
                ev = json.loads(line[5:])
                usage = ev.get("usage") or usage
                for ch in ev.get("choices", []):
                    piece = (ch.get("delta") or {}).get("content")
                    if piece:
                        if first is None:
                            first = time.perf_counter()
                        parts.append(piece)
        t1 = time.perf_counter(); first = first or t1
        out = usage.get("completion_tokens") or max(1, len("".join(parts)) // 4)
        pin = usage.get("prompt_tokens", 0)
        return Result(text="".join(parts), ttft_s=first - t0, total_s=t1 - t0, prompt_tokens=pin, output_tokens=out,
                      prompt_tps=pin / (first - t0) if first > t0 else 0.0,
                      decode_tps=(out - 1) / (t1 - first) if t1 > first and out > 1 else 0.0)
    def memory(self, model):
        return {}
    def unload(self, model):
        pass

BACKENDS = {"ollama": Ollama, "openai": OpenAICompat}
