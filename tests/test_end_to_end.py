import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.mock_ollama import serve
from siliconbench.run import run
from siliconbench.report import build_report
from siliconbench.tasks import build, parse_last_number

def test_problems_are_paired_and_deterministic():
    a, b = build(4, seed=1), build(4, seed=1)
    assert [t.prompt for t in a] == [t.prompt for t in b]
    en = {t.id: t.answer for t in a if t.lang == "en"}; it = {t.id: t.answer for t in a if t.lang == "it"}
    assert en == it and len(en) == 20

def test_number_parsing():
    assert parse_last_number("montante 3.021,50 euro") == 3021.5
    assert abs(parse_last_number("F = 1,5 × 10^-3 N") - 0.0015) < 1e-12
    assert parse_last_number("Answer: 3,021.5") == 3021.5

def test_checker_accepts_right_and_rejects_wrong():
    t = build(1)[0]
    assert t.check(f"so...\n{t.answer:.6g}") and not t.check(f"so...\n{t.answer * 1.5:.6g}")

def test_run_and_report():
    srv = serve(11500)
    with tempfile.TemporaryDirectory() as d:
        out = run(["mock:1b"], host="http://127.0.0.1:11500", out=d, n_per_subject=2, log=lambda *a: None)
        table = build_report(out)
        assert (Path(d) / "REPORT.md").exists() and abs(table.tok_s.iloc[0] - 50) < 1
    srv.shutdown()

if __name__ == "__main__":
    for f in [test_problems_are_paired_and_deterministic, test_number_parsing, test_checker_accepts_right_and_rejects_wrong, test_run_and_report]:
        f()
    print("all tests passed")
