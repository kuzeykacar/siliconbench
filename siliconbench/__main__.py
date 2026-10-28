"""  python -m siliconbench run --models qwen2.5:3b llama3.2:3b --out results/m5-16gb
     python -m siliconbench report results/m5-16gb
     python -m siliconbench show 5            # print a few generated problems"""
import argparse
from .run import run
from .report import build_report
from .tasks import build

def main():
    ap = argparse.ArgumentParser(prog="siliconbench"); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--models", nargs="+", required=True)
    r.add_argument("--backend", default="ollama", choices=["ollama", "openai"]); r.add_argument("--host")
    r.add_argument("--out", default="results/run"); r.add_argument("--n", type=int, default=12, help="problems per subject")
    r.add_argument("--seed", type=int, default=0); r.add_argument("--subjects", nargs="*")
    p = sub.add_parser("report"); p.add_argument("run_dir")
    s = sub.add_parser("show"); s.add_argument("n", type=int, nargs="?", default=3)
    a = ap.parse_args()
    if a.cmd == "run":
        out = run(a.models, a.backend, a.host, a.out, a.n, a.seed, a.subjects)
        print(build_report(out).to_string(index=False)); print("report:", out / "REPORT.md")
    elif a.cmd == "report":
        print(build_report(a.run_dir).to_string(index=False))
    else:
        for t in build(a.n):
            print(f"[{t.subject}/{t.lang}] answer={t.answer}\n{t.prompt}\n")

if __name__ == "__main__":
    main()
