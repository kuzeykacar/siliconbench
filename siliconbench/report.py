"""raw.jsonl -> summary tables, two charts and REPORT.md."""
import json, random
from pathlib import Path
import pandas as pd

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))

def lang_gap(df, n=2000, seed=0):
    """Paired bootstrap of accuracy(EN) - accuracy(IT) over the same problems."""
    p = df.pivot_table(index="task", columns="lang", values="passed", aggfunc="first").dropna()
    if not {"en", "it"} <= set(p.columns) or len(p) == 0:
        return float("nan"), (float("nan"), float("nan"))
    d = (p["en"].astype(float) - p["it"].astype(float)).tolist(); rng = random.Random(seed); bs = []
    for _ in range(n):
        s = [d[rng.randrange(len(d))] for _ in d]; bs.append(sum(s) / len(s))
    bs.sort(); return sum(d) / len(d), (bs[int(.025 * n)], bs[int(.975 * n)])

def summarize(run_dir):
    run_dir = Path(run_dir); df = pd.DataFrame([json.loads(l) for l in open(run_dir / "raw.jsonl")])
    rows = []
    for m, g in df.groupby("model", sort=False):
        k, n = int(g.passed.sum()), len(g); lo, hi = wilson(k, n); gap, (glo, ghi) = lang_gap(g)
        rows.append(dict(model=m, accuracy=k / n, lo=lo, hi=hi, acc_en=g[g.lang == "en"].passed.mean(),
                         acc_it=g[g.lang == "it"].passed.mean(), gap=gap, gap_lo=glo, gap_hi=ghi,
                         tok_s=g.decode_tps.median(), ttft_s=g.ttft_s.median(), sec_per_answer=g.seconds.median(),
                         mem_gb=(g.size_bytes.max() / 2**30) if "size_bytes" in g and g.size_bytes.notna().any() else None))
    table = pd.DataFrame(rows)
    subj = df.groupby(["model", "subject", "lang"]).passed.mean().unstack(["subject", "lang"])
    table.to_csv(run_dir / "summary.csv", index=False); subj.to_csv(run_dir / "by_subject.csv")
    return table, df

def charts(run_dir, table, df):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    run_dir = Path(run_dir)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.errorbar(table.tok_s, table.accuracy * 100, yerr=[(table.accuracy - table.lo) * 100, (table.hi - table.accuracy) * 100],
                fmt="o", capsize=3)
    for _, r in table.iterrows():
        ax.annotate(r["model"], (r.tok_s, r.accuracy * 100), textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.set_xlabel("writing speed (tokens per second)"); ax.set_ylabel("problems solved (%)")
    ax.set_title("Is the faster model good enough?"); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(run_dir / "speed_vs_accuracy.png", dpi=150)
    s = df.groupby(["model", "subject"]).passed.mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 4.2)); (s * 100).plot.bar(ax=ax)
    ax.set_ylabel("solved (%)"); ax.set_title("By subject (English + Italian)"); ax.legend(fontsize=7, ncol=3)
    ax.tick_params(axis="x", rotation=20); fig.tight_layout(); fig.savefig(run_dir / "by_subject.png", dpi=150); plt.close("all")

def markdown(run_dir, table):
    run_dir = Path(run_dir); meta = json.loads((run_dir / "meta.json").read_text()); s = meta["system"]
    L = [f"# Results on {s.get('chip', s.get('machine'))}, {s.get('ram_gb', '?')} GB RAM", "",
         f"{meta['n_tasks']} problems per model ({meta['n_tasks'] // 2} in English + the same in Italian), backend {meta['backend']}, "
         f"started {meta['started']}{' (on battery)' if s.get('on_battery') else ''}.", "",
         "| model | solved | 95% interval | English | Italian | EN − IT gap (95% CI) | tokens/s | memory GB |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in table.sort_values("accuracy", ascending=False).iterrows():
        mem = f"{r.mem_gb:.1f}" if pd.notna(r.mem_gb) else "–"
        L.append(f"| {r['model']} | {r.accuracy:.0%} | {r.lo:.0%}–{r.hi:.0%} | {r.acc_en:.0%} | {r.acc_it:.0%} | "
                 f"{r.gap:+.0%} ({r.gap_lo:+.0%} to {r.gap_hi:+.0%}) | {r.tok_s:.1f} | {mem} |")
    L += ["", "![speed vs accuracy](speed_vs_accuracy.png)", "", "![by subject](by_subject.png)", ""]
    (run_dir / "REPORT.md").write_text("\n".join(L))

def build_report(run_dir):
    table, df = summarize(run_dir)
    try:
        charts(run_dir, table, df)
    except ImportError:
        pass
    markdown(run_dir, table); return table
