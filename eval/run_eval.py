"""Runs the checker on the clean system, each planted issue alone, and all 25 together.

Usage: python3 -m eval.run_eval
"""
import json
import os
import sys

from readiness.checks import run_checks, unit_verdicts
from readiness.sample import build
from eval.planted import ISSUES, planted_system, single_issue_system


def keys(findings):
    return {(f["check"], f["key"]) for f in findings}


def evaluate(seed=7):
    clean = run_checks(build(seed))
    alone = []
    for i, (fn, label) in enumerate(ISSUES):
        d, exp = single_issue_system(i, seed)
        got = keys(run_checks(d))
        alone.append(dict(issue=fn.__name__, label=label, caught=set(exp) <= got,
                          extra=sorted(got - set(exp))))
    d, expected = planted_system(seed)
    f_all = run_checks(d)
    got = keys(f_all)
    exp_all = set(k for _, _, ks in expected for k in ks)
    together = [dict(issue=n, label=l, caught=set(ks) <= got) for n, l, ks in expected]
    verdicts = unit_verdicts(d, f_all)
    return dict(
        clean_findings=len(clean),
        alone_caught=sum(a["caught"] for a in alone),
        alone_with_extra=[a["issue"] for a in alone if a["extra"]],
        together_caught=sum(t["caught"] for t in together),
        together_false_positives=sorted(got - exp_all),
        total_issues=len(ISSUES),
        findings_together=len(f_all),
        no_go_units=sum(v["verdict"] == "NO-GO" for v in verdicts.values()),
        units=len(verdicts),
        detail=together,
    )


if __name__ == "__main__":
    r = evaluate()
    print(f"Clean system: {r['clean_findings']} findings (expect 0)")
    print(f"Each issue alone: {r['alone_caught']} of {r['total_issues']} caught; "
          f"issues that raised anything extra: {r['alone_with_extra'] or 'none'}")
    print(f"All 25 together: {r['together_caught']} of {r['total_issues']} caught, "
          f"{len(r['together_false_positives'])} false positives, {r['findings_together']} findings")
    print(f"Units NO-GO before fixes: {r['no_go_units']} of {r['units']}")
    for t in r["detail"]:
        if not t["caught"]:
            print("  MISSED", t["issue"], t["label"])
    os.makedirs("eval/results", exist_ok=True)
    with open("eval/results/eval_results.json", "w") as f:
        json.dump({k: v for k, v in r.items()}, f, indent=2, default=list)
    ok = (r["clean_findings"] == 0 and r["alone_caught"] == r["total_issues"]
          and r["together_caught"] == r["total_issues"] and not r["together_false_positives"])
    sys.exit(0 if ok else 1)
