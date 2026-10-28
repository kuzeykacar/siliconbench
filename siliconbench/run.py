"""Ask every model every problem (English and Italian versions) and save the raw answers as JSON lines.
Speed is recorded on the same answers (tokens per second while the model writes), not with a separate load test."""
import json, time
from pathlib import Path
from .backends import BACKENDS
from .tasks import build
from . import system

def run(models, backend="ollama", host=None, out="results/run", n_per_subject=12, seed=0, subjects=None, log=print):
    be = BACKENDS[backend](host) if host else BACKENDS[backend]()
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    tasks = build(n_per_subject, seed, subjects)
    meta = dict(system=system.info(), backend=backend, models=models, started=time.strftime("%Y-%m-%d %H:%M:%S"),
                n_per_subject=n_per_subject, seed=seed, n_tasks=len(tasks))
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    with open(out / "raw.jsonl", "a") as raw:
        for model in models:
            log(f"== {model}  ({len(tasks)} questions)")
            be.generate(model, "Say OK.", max_tokens=4)                  # load the weights first
            mem = be.memory(model); score = {}
            for t in tasks:
                res = be.generate(model, t.prompt, max_tokens=t.max_tokens)
                ok = bool(t.check(res.text)); score.setdefault((t.subject, t.lang), []).append(ok)
                raw.write(json.dumps(dict(model=model, subject=t.subject, task=t.id, lang=t.lang, passed=ok,
                                          answer=t.answer, output=res.text, ttft_s=res.ttft_s, decode_tps=res.decode_tps,
                                          output_tokens=res.output_tokens, seconds=res.total_s, **mem), ensure_ascii=False) + "\n")
                raw.flush()
            log("   " + "  ".join(f"{s}/{l} {sum(v)}/{len(v)}" for (s, l), v in sorted(score.items())))
            be.unload(model)
    return out
