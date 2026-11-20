"""25 planted data problems, each the kind that delays a staffing go-live.

Each issue is a small edit to the clean sample system plus the findings the
checker must raise for it, as (check id, key) pairs.
"""
import copy

from readiness.sample import build


def _emp(d, unit, job):
    return next(e for e in d["hris_roster"] if e["home_unit"] == unit and e["job_code"] == job)


def _shift(d, eid):
    return next(s for s in d["timekeeping_schedule"] if s["employee_id"] == eid)


def _add_shift(d, eid, unit, start, end, code="REG"):
    d["timekeeping_schedule"].append(dict(employee_id=eid, unit_code=unit, shift_start=start,
                                          shift_end=end, pay_code=code))


def i01(d):
    _add_shift(d, "E9001", "MC-4W", "2027-01-05T07:00", "2027-01-05T19:00")
    return [("scheduled_not_in_roster", "E9001")]


def i02(d):
    _add_shift(d, "E9002", "RV-ICU", "2027-01-06T19:00", "2027-01-07T07:00")
    return [("scheduled_not_in_roster", "E9002")]


def i03(d):
    _add_shift(d, "E9003", "MC-LD", "2027-01-08T07:00", "2027-01-08T19:00")
    return [("scheduled_not_in_roster", "E9003")]


def i04(d):
    e = _emp(d, "MC-ED", "RN1"); e["status"] = "Terminated"
    return [("scheduled_after_termination", e["employee_id"])]


def i05(d):
    e = _emp(d, "MC-ED", "CNA"); e["status"] = "Terminated"
    return [("scheduled_after_termination", e["employee_id"])]


def i06(d):
    e = _emp(d, "MC-5E", "RN2"); d["hris_roster"].append(dict(e, last_name="Duplicate"))
    return [("duplicate_employee_id", e["employee_id"])]


def i07(d):
    e = _emp(d, "RV-ICU", "CHG"); d["hris_roster"].append(dict(e, fte="0.6"))
    return [("duplicate_employee_id", e["employee_id"])]


def i08(d):
    e = _emp(d, "MC-LD", "NM"); e["home_unit"] = "LD-OLD"
    return [("home_unit_unknown", e["employee_id"])]


def i09(d):
    e = _emp(d, "MC-4W", "RN1"); e["job_code"] = "RNTRV"
    return [("job_code_unmapped", "RNTRV:" + e["employee_id"])]


def i10(d):
    e = _emp(d, "RV-ED", "CNA"); e["job_code"] = "CNA2"
    return [("job_code_unmapped", "CNA2:" + e["employee_id"])]


def i11(d):
    e = _emp(d, "MC-4W", "CHG"); e["union"] = ""
    return [("union_missing", e["employee_id"])]


def i12(d):
    e = _emp(d, "MC-LD", "RN2"); e["union"] = ""
    return [("union_missing", e["employee_id"])]


def i13(d):
    e = _emp(d, "MC-4W", "HUC"); e["union"] = ""
    return [("union_missing", e["employee_id"])]


def i14(d):
    e = _emp(d, "MC-ED", "RN2"); _shift(d, e["employee_id"])["pay_code"] = "OT2X"
    return [("pay_code_unknown", "OT2X")]


def i15(d):
    next(p for p in d["pay_codes"] if p["pay_code"] == "CALLB")["contract_rule"] = "NU-CALL-2"
    e = _emp(d, "RV-ICU", "RNCC"); _shift(d, e["employee_id"])["pay_code"] = "CALLB"
    return [("pay_code_no_rule", "CALLB")]


def i16(d):
    next(p for p in d["pay_codes"] if p["pay_code"] == "INCSH")["contract_rule"] = ""
    e = _emp(d, "MC-5E", "RN1"); _shift(d, e["employee_id"])["pay_code"] = "INCSH"
    return [("pay_code_no_rule", "INCSH")]


def i17(d):
    for c in d["ehr_census"]:
        if c["ehr_unit"] == "RV EMERG":
            c["ehr_unit"] = "RV ED"
    return [("ehr_unit_unmapped", "RV ED"), ("unit_no_census", "RV-ED")]


def i18(d):
    first = next(c for c in d["ehr_census"] if c["ehr_unit"] == "MC 4W MEDSURG")
    d["ehr_census"].append(dict(ehr_unit="MC 6W OBS", hour=first["hour"], census=9))
    return [("ehr_unit_unmapped", "MC 6W OBS")]


def i19(d):
    d["ehr_census"] = [c for c in d["ehr_census"] if c["ehr_unit"] != "MC L&D"]
    return [("unit_no_census", "MC-LD")]


def i20(d):
    rows = [c for c in d["ehr_census"] if c["ehr_unit"] == "MC 5E CARD SD"][50:60]
    d["ehr_census"] = [c for c in d["ehr_census"] if c not in rows]
    return [("census_gaps", "MC-5E")]


def i21(d):
    rows = [c for c in d["ehr_census"] if c["ehr_unit"] == "RV 3N MEDSURG"][100:105]
    d["ehr_census"] = [c for c in d["ehr_census"] if c not in rows]
    return [("census_gaps", "RV-3N")]


def i22(d):
    d["staffing_grid"] = [g for g in d["staffing_grid"] if not (g["unit_code"] == "MC-ED" and g["role"] == "Clerk")]
    return [("grid_missing", "MC-ED:Clerk")]


def i23(d):
    d["staffing_grid"] = [g for g in d["staffing_grid"] if not (g["unit_code"] == "RV-ICU" and g["role"] == "CNA")]
    return [("grid_missing", "RV-ICU:CNA")]


def i24(d):
    e = _emp(d, "MC-4W", "RN2"); s = _shift(d, e["employee_id"])
    start = s["shift_start"][:11] + "%02d:00" % ((int(s["shift_start"][11:13]) + 4) % 24)
    if start <= s["shift_start"]:
        start = s["shift_start"][:11] + "11:00"
    _add_shift(d, e["employee_id"], "MC-5E", start, s["shift_end"], "FLOAT")
    return [("shift_overlap", f"{e['employee_id']}@{start}")]


def i25(d):
    e = _emp(d, "RV-ED", "RN1"); s = _shift(d, e["employee_id"])
    _add_shift(d, e["employee_id"], "RV-ED", s["shift_start"], s["shift_end"])
    return [("shift_overlap", f"{e['employee_id']}@{s['shift_start']}")]


ISSUES = [
    (i01, "Agency nurse set up in timekeeping but never added to the HR roster (4 West)"),
    (i02, "Traveler scheduled on the Riverside ICU with no HR record"),
    (i03, "New hire scheduled on Labor and Delivery before HR onboarding finished"),
    (i04, "ED nurse terminated in HR but still on next week's schedule"),
    (i05, "ED nursing assistant terminated in HR but still scheduled"),
    (i06, "Stepdown nurse loaded twice in the HR roster after a job change"),
    (i07, "Riverside ICU charge nurse duplicated with a different FTE"),
    (i08, "L&D manager's home unit still uses a retired unit code"),
    (i09, "Travel-nurse job code with no staffing role (4 West)"),
    (i10, "New nursing assistant job code not mapped to a role (Riverside ED)"),
    (i11, "4 West charge nurse with no union on file"),
    (i12, "L&D nurse with no union on file"),
    (i13, "4 West unit coordinator with no union on file"),
    (i14, "Double-time pay code used in the ED but missing from the pay code table"),
    (i15, "Call-back pay code points to a contract rule that does not exist (Riverside ICU)"),
    (i16, "Incentive-shift pay code has no contract rule (Stepdown)"),
    (i17, "EHR interface renamed the Riverside ED census unit, breaking the mapping"),
    (i18, "New observation unit in the EHR census with no staffing unit"),
    (i19, "Census feed never turned on for Labor and Delivery"),
    (i20, "Stepdown census feed dropped 10 hours"),
    (i21, "Riverside med-surg census feed dropped 5 hours"),
    (i22, "ED has unit coordinator shifts but no staffing grid for them"),
    (i23, "Riverside ICU has nursing assistant shifts but no grid for them"),
    (i24, "4 West nurse floated to Stepdown on an overlapping shift"),
    (i25, "Riverside ED nurse double-booked on the same shift"),
]


def planted_system(seed=7):
    """Clean system with all 25 issues applied. Returns (data, expected list per issue)."""
    d = build(seed)
    expected = []
    for fn, label in ISSUES:
        expected.append((fn.__name__, label, fn(d)))
    return d, expected


def single_issue_system(index, seed=7):
    d = build(seed)
    fn, label = ISSUES[index]
    return d, fn(d)
