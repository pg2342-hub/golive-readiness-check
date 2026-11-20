"""Builds docs/index.html (the GitHub Pages demo) from the checker's real output.

Usage: python3 docs/build_page.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.planted import ISSUES  # noqa: E402
from eval.run_eval import evaluate  # noqa: E402
from readiness.checks import CHECKS, run_checks, unit_verdicts  # noqa: E402
from readiness.sample import read_csvs, SYSTEM_NAME  # noqa: E402

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
views = {}
for key, folder in (("first", "first_pull"), ("fixed", "after_fixes")):
    d = read_csvs(os.path.join(root, "sample_data", folder))
    f = run_checks(d)
    views[key] = dict(findings=f, verdicts=list(unit_verdicts(d, f).values()),
                      feeds={k: len(v) for k, v in d.items()})
os.chdir(root)
ev = evaluate()
payload = dict(system=SYSTEM_NAME, views=views,
               checks=[dict(id=k, name=v[0], severity=v[1], owner=v[2]) for k, v in CHECKS.items()],
               issues=[label for _, label in ISSUES],
               eval=dict(clean=ev["clean_findings"], alone=ev["alone_caught"], together=ev["together_caught"],
                         fp=len(ev["together_false_positives"]), total=ev["total_issues"]))

template = open(os.path.join(root, "docs", "template.html")).read()
out = template.replace("/*DATA*/null", json.dumps(payload))
open(os.path.join(root, "docs", "index.html"), "w").write(out)
print("wrote docs/index.html", len(out), "bytes")
