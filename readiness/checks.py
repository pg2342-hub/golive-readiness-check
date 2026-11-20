"""Go-live readiness checks across the HR roster, timekeeping schedule and EHR census feeds.

Each check returns findings. A finding names the unit it blocks, how serious it
is (blocking or warning), which team fixes it, and a plain-language message.
A unit is NO-GO if it has any blocking finding, GO WITH FIXES if it has only
warnings, and GO otherwise.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BLOCKING, WARNING = "blocking", "warning"

# check id -> (name shown to people, severity, team that fixes it)
CHECKS = {
    "scheduled_not_in_roster": ("Scheduled staff missing from the HR roster", BLOCKING, "HR systems team"),
    "scheduled_after_termination": ("Shifts for staff marked terminated", BLOCKING, "HR systems team"),
    "duplicate_employee_id": ("Duplicate employee IDs in the HR roster", BLOCKING, "HR systems team"),
    "home_unit_unknown": ("Home unit not in the unit list", WARNING, "HR systems team"),
    "job_code_unmapped": ("Job code with no staffing role", BLOCKING, "Nursing operations"),
    "union_missing": ("Union-covered staff with no union on file", BLOCKING, "Labor relations"),
    "pay_code_unknown": ("Pay code missing from the pay code table", BLOCKING, "Timekeeping admin"),
    "pay_code_no_rule": ("Pay code with no contract rule", BLOCKING, "Labor relations"),
    "ehr_unit_unmapped": ("EHR census unit not mapped to a staffing unit", BLOCKING, "EHR interface team"),
    "unit_no_census": ("Staffing unit with no census feed", BLOCKING, "EHR interface team"),
    "census_gaps": ("Hours missing from the census feed", WARNING, "EHR interface team"),
    "grid_missing": ("No staffing grid for a role on the unit", BLOCKING, "Nursing operations"),
    "shift_overlap": ("Overlapping shifts for one person", WARNING, "Timekeeping admin"),
}

CENSUS_GAP_LIMIT = 2  # missing hours in the census window before it is flagged


def _f(check, unit, key, message):
    name, severity, owner = CHECKS[check]
    return dict(check=check, check_name=name, severity=severity, owner=owner,
                unit=unit, key=key, message=message)


def run_checks(data):
    findings = []
    units = {u["unit_code"] for u in data["units"]}
    roster = data["hris_roster"]
    by_id = {}
    counts = Counter(e["employee_id"] for e in roster)
    for e in roster:
        by_id.setdefault(e["employee_id"], e)
    jobs = {j["job_code"]: j for j in data["job_skills"]}
    pay = {p["pay_code"]: p for p in data["pay_codes"]}
    rules = {r["rule_id"] for r in data["contract_rules"]}
    schedule = data["timekeeping_schedule"]

    # HR roster checks
    for eid, c in sorted(counts.items()):
        if c > 1:
            unit_list = sorted({e["home_unit"] for e in roster if e["employee_id"] == eid})
            for u in unit_list:
                findings.append(_f("duplicate_employee_id", u, eid,
                                   f"Employee ID {eid} appears {c} times in the HR roster, so shifts cannot be tied to one person."))
    for e in roster:
        if e["home_unit"] not in units:
            findings.append(_f("home_unit_unknown", e["home_unit"], e["employee_id"],
                               f"{e['employee_id']} has home unit '{e['home_unit']}', which is not in the unit list."))
        job = jobs.get(e["job_code"])
        if job is None or not job.get("role"):
            findings.append(_f("job_code_unmapped", e["home_unit"], e["job_code"] + ":" + e["employee_id"],
                               f"{e['employee_id']} has job code '{e['job_code']}', which has no staffing role, so they cannot be offered shifts."))
        elif job["union_covered"] == "Y" and e["status"] == "Active" and not e["union"].strip():
            findings.append(_f("union_missing", e["home_unit"], e["employee_id"],
                               f"{e['employee_id']} ({job['title']}) is in a union-covered job but has no union on file, so contract rules cannot be applied."))

    # Schedule against roster
    term_seen, missing_seen = set(), set()
    for s in schedule:
        e = by_id.get(s["employee_id"])
        if e is None:
            if (s["employee_id"], s["unit_code"]) not in missing_seen:
                missing_seen.add((s["employee_id"], s["unit_code"]))
                findings.append(_f("scheduled_not_in_roster", s["unit_code"], s["employee_id"],
                                   f"{s['employee_id']} is on the schedule for {s['unit_code']} but is not in the HR roster."))
        elif e["status"] != "Active":
            if (s["employee_id"], s["unit_code"]) not in term_seen:
                term_seen.add((s["employee_id"], s["unit_code"]))
                findings.append(_f("scheduled_after_termination", s["unit_code"], s["employee_id"],
                                   f"{s['employee_id']} is marked {e['status']} in the HR roster but still has shifts on {s['unit_code']}."))

    # Pay codes used on each unit
    used = defaultdict(set)
    for s in schedule:
        used[s["pay_code"]].add(s["unit_code"])
    for code, unit_set in sorted(used.items()):
        if code not in pay:
            for u in sorted(unit_set):
                findings.append(_f("pay_code_unknown", u, code,
                                   f"Pay code '{code}' is on {u}'s schedule but missing from the pay code table."))
        elif pay[code]["contract_rule"] not in rules:
            for u in sorted(unit_set):
                findings.append(_f("pay_code_no_rule", u, code,
                                   f"Pay code '{code}' ({pay[code]['description']}) is used on {u} but has no matching contract rule, so it cannot be checked or paid correctly."))

    # EHR census mapping and coverage
    mapping = {}
    for m in data["unit_map"]:
        mapping[m["ehr_unit"]] = m["unit_code"]
    hours_by_unit = defaultdict(set)
    ehr_units = set()
    for c in data["ehr_census"]:
        ehr_units.add(c["ehr_unit"])
        if c["ehr_unit"] in mapping:
            hours_by_unit[mapping[c["ehr_unit"]]].add(c["hour"])
    for eu in sorted(ehr_units):
        if eu not in mapping or mapping[eu] not in units:
            findings.append(_f("ehr_unit_unmapped", mapping.get(eu, "(unmapped)"), eu,
                               f"Census unit '{eu}' from the EHR does not map to a staffing unit, so its patients are not counted toward demand."))
    all_hours = sorted({c["hour"] for c in data["ehr_census"]})
    if all_hours:
        first = datetime.fromisoformat(all_hours[0])
        last = datetime.fromisoformat(all_hours[-1])
        expected = int((last - first) / timedelta(hours=1)) + 1
    else:
        expected = 0
    for u in sorted(units):
        got = len(hours_by_unit.get(u, ()))
        if got == 0:
            findings.append(_f("unit_no_census", u, u,
                               f"{u} has no census rows from the EHR, so the unit has no demand signal."))
        elif expected - got > CENSUS_GAP_LIMIT:
            findings.append(_f("census_gaps", u, u,
                               f"{u} is missing {expected - got} of {expected} census hours in the feed window."))

    # Staffing grid for every role scheduled on each unit
    grid = {(g["unit_code"], g["role"]) for g in data["staffing_grid"]}
    need = set()
    for s in schedule:
        e = by_id.get(s["employee_id"])
        if e and e["job_code"] in jobs and jobs[e["job_code"]].get("role") not in (None, "", "Manager"):
            need.add((s["unit_code"], jobs[e["job_code"]]["role"]))
    for u, role in sorted(need):
        if (u, role) not in grid:
            findings.append(_f("grid_missing", u, f"{u}:{role}",
                               f"{u} has {role} shifts but no staffing grid for {role}, so the number of {role}s needed cannot be computed."))

    # Overlapping shifts per person
    per = defaultdict(list)
    for s in schedule:
        per[s["employee_id"]].append(s)
    for eid, shifts in sorted(per.items()):
        shifts.sort(key=lambda s: s["shift_start"])
        for a, b in zip(shifts, shifts[1:]):
            if b["shift_start"] < a["shift_end"]:
                findings.append(_f("shift_overlap", b["unit_code"], f"{eid}@{b['shift_start']}",
                                   f"{eid} has a shift on {b['unit_code']} starting {b['shift_start'].replace('T', ' ')} before their shift on {a['unit_code']} ends."))
    return findings


def unit_verdicts(data, findings):
    out = {}
    for u in data["units"]:
        f = [x for x in findings if x["unit"] == u["unit_code"]]
        if any(x["severity"] == BLOCKING for x in f):
            v = "NO-GO"
        elif f:
            v = "GO WITH FIXES"
        else:
            v = "GO"
        out[u["unit_code"]] = dict(unit_code=u["unit_code"], hospital=u["hospital"], unit_name=u["unit_name"],
                                   verdict=v, blocking=sum(x["severity"] == BLOCKING for x in f),
                                   warnings=sum(x["severity"] == WARNING for x in f))
    return out


def fix_list(findings):
    """Groups findings by the team that fixes them, blocking first."""
    groups = defaultdict(list)
    for f in findings:
        groups[f["owner"]].append(f)
    order = sorted(groups, key=lambda o: (-sum(x["severity"] == BLOCKING for x in groups[o]), o))
    return [(o, sorted(groups[o], key=lambda x: (x["severity"] != BLOCKING, x["unit"], x["check"]))) for o in order]
