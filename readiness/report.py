"""Prints a go/no-go readiness report for a folder of feed CSVs.

Usage: python3 -m readiness.report sample_data/first_pull
"""
import sys

from readiness.checks import BLOCKING, fix_list, run_checks, unit_verdicts
from readiness.sample import SYSTEM_NAME, read_csvs


def render(data, title):
    findings = run_checks(data)
    verdicts = unit_verdicts(data, findings)
    known = set(verdicts)
    lines = [f"# Go-live readiness: {title}", ""]
    n_go = sum(v["verdict"] == "GO" for v in verdicts.values())
    n_fix = sum(v["verdict"] == "GO WITH FIXES" for v in verdicts.values())
    n_no = sum(v["verdict"] == "NO-GO" for v in verdicts.values())
    lines.append(f"{len(verdicts)} units: {n_go} GO, {n_fix} GO WITH FIXES, {n_no} NO-GO. "
                 f"{len(findings)} findings ({sum(f['severity'] == BLOCKING for f in findings)} blocking).")
    lines += ["", "## Units", "", "| Hospital | Unit | Verdict | Blocking | Warnings |", "|---|---|---|---|---|"]
    for v in verdicts.values():
        lines.append(f"| {v['hospital']} | {v['unit_name']} ({v['unit_code']}) | {v['verdict']} | {v['blocking']} | {v['warnings']} |")
    lines += ["", "## Fix list by team", ""]
    if not findings:
        lines.append("Nothing to fix.")
    for owner, items in fix_list(findings):
        lines.append(f"### {owner} ({len(items)})")
        for f in items:
            where = f["unit"] if f["unit"] in known else "not tied to a live unit"
            lines.append(f"- [{f['severity']}] {f['check_name']} ({where}): {f['message']}")
        lines.append("")
    return "\n".join(lines), findings, verdicts


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "sample_data/first_pull"
    text, _, verdicts = render(read_csvs(folder), f"{SYSTEM_NAME}, {folder}")
    print(text)
    sys.exit(1 if any(v["verdict"] == "NO-GO" for v in verdicts.values()) else 0)
