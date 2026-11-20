"""Builds a clean, made-up two-hospital health system for the readiness checks.

Nothing here is real hospital data. Unit names, unions, pay codes and contract
rules are illustrative and only shaped like the feeds a staffing rollout uses:
a staff roster from the HR system (HRIS), schedules and pay codes from the
timekeeping system, and hourly unit census from the EHR's admit/discharge/
transfer (ADT) feed.
"""
import csv
import os
import random
from datetime import date, datetime, timedelta

SYSTEM_NAME = "Northgate University Health (sample data)"
START = date(2027, 1, 4)        # first day of the two-week schedule
SCHEDULE_DAYS = 14
CENSUS_DAYS = 7

UNITS = [
    # unit_code, hospital, unit name, EHR unit name, beds
    ("MC-4W", "Main Campus", "4 West Med-Surg", "MC 4W MEDSURG", 32),
    ("MC-5E", "Main Campus", "5 East Cardiac Stepdown", "MC 5E CARD SD", 24),
    ("MC-MICU", "Main Campus", "Medical ICU", "MC MICU", 20),
    ("MC-ED", "Main Campus", "Emergency Department", "MC EMERG", 40),
    ("MC-LD", "Main Campus", "Labor and Delivery", "MC L&D", 16),
    ("RV-3N", "Riverside", "3 North Med-Surg", "RV 3N MEDSURG", 28),
    ("RV-ICU", "Riverside", "ICU", "RV ICU", 12),
    ("RV-ED", "Riverside", "Emergency Department", "RV EMERG", 22),
]

JOB_CODES = [
    # job_code, title, role, union_covered
    ("RN1", "Staff Nurse I", "RN", "Y"),
    ("RN2", "Staff Nurse II", "RN", "Y"),
    ("RNCC", "Critical Care Nurse", "RN", "Y"),
    ("CNA", "Nursing Assistant", "CNA", "Y"),
    ("HUC", "Health Unit Coordinator", "Clerk", "Y"),
    ("CHG", "Charge Nurse", "RN", "Y"),
    ("NM", "Nurse Manager", "Manager", "N"),
]

UNIONS = {"RN": "Nurses Union (sample)", "CNA": "Service Workers Union (sample)",
          "Clerk": "Service Workers Union (sample)"}

CONTRACT_RULES = [
    # rule_id, union, rule text (illustrative, not any real contract)
    ("NU-OT-1", "Nurses Union (sample)", "Time and a half after 40 hours a week or 12 hours in a shift"),
    ("NU-CALL-1", "Nurses Union (sample)", "Call-back paid at time and a half, minimum 3 hours"),
    ("NU-INC-1", "Nurses Union (sample)", "Extra-shift incentive only for shifts posted as critical need"),
    ("NU-FLT-1", "Nurses Union (sample)", "Float only to units on the nurse's competency list"),
    ("SW-OT-1", "Service Workers Union (sample)", "Time and a half after 40 hours a week"),
    ("ALL-REG", "All", "Regular hours"),
    ("ALL-PTO", "All", "Paid time off from accrual"),
]

PAY_CODES = [
    # pay_code, description, contract_rule
    ("REG", "Regular", "ALL-REG"),
    ("OT15", "Overtime 1.5x", "NU-OT-1"),
    ("SWOT", "Service overtime 1.5x", "SW-OT-1"),
    ("CALLB", "Call-back", "NU-CALL-1"),
    ("INCSH", "Incentive extra shift", "NU-INC-1"),
    ("FLOAT", "Floated to another unit", "NU-FLT-1"),
    ("PTO", "Paid time off", "ALL-PTO"),
]

# Patients per staff member by unit type and role (illustrative grid).
GRID = {"Med-Surg": {"RN": 5, "CNA": 10, "Clerk": 32},
        "Stepdown": {"RN": 3, "CNA": 12, "Clerk": 24},
        "ICU": {"RN": 2, "CNA": 10, "Clerk": 20},
        "ED": {"RN": 4, "CNA": 10, "Clerk": 20},
        "LD": {"RN": 2, "CNA": 8, "Clerk": 16}}


def unit_type(unit_code):
    if "ICU" in unit_code:
        return "ICU"
    if unit_code.endswith("ED"):
        return "ED"
    if unit_code.endswith("LD"):
        return "LD"
    if unit_code == "MC-5E":
        return "Stepdown"
    return "Med-Surg"


def build(seed=7):
    """Returns a dict of feed name -> list of row dicts. No problems in it."""
    rng = random.Random(seed)
    units = [dict(unit_code=u, hospital=h, unit_name=n, ehr_unit=e, beds=b) for u, h, n, e, b in UNITS]
    job_skills = [dict(job_code=j, title=t, role=r, union_covered=c) for j, t, r, c in JOB_CODES]
    contract_rules = [dict(rule_id=i, union=u, rule=t) for i, u, t in CONTRACT_RULES]
    pay_codes = [dict(pay_code=p, description=d, contract_rule=r) for p, d, r in PAY_CODES]
    unit_map = [dict(ehr_unit=u["ehr_unit"], unit_code=u["unit_code"]) for u in units]
    grid = []
    for u in units:
        for role, ratio in GRID[unit_type(u["unit_code"])].items():
            grid.append(dict(unit_code=u["unit_code"], role=role, patients_per_staff=ratio))

    roster, n = [], 1000
    for u in units:
        icu = "ICU" in u["unit_code"]
        mix = (["RNCC"] * 8 if icu else ["RN1"] * 5 + ["RN2"] * 4) + ["CHG"] * 2 + ["CNA"] * 3 + ["HUC"] + ["NM"]
        for job in mix:
            n += 1
            role = next(r for j, _, r, _ in JOB_CODES if j == job)
            roster.append(dict(employee_id=f"E{n}", last_name=f"Staff{n}", job_code=job,
                               home_unit=u["unit_code"], fte=rng.choice(["0.9", "0.9", "0.6", "1.0"]),
                               status="Active", union=UNIONS.get(role, ""),
                               hire_date=str(date(2015 + rng.randrange(11), rng.randrange(1, 13), 1))))

    schedule = []
    for e in roster:
        if e["job_code"] == "NM":
            continue
        days = sorted(rng.sample(range(SCHEDULE_DAYS), 6))
        night = rng.random() < 0.4
        for d in days:
            day = START + timedelta(days=d)
            start = datetime.combine(day, datetime.min.time()) + timedelta(hours=19 if night else 7)
            end = start + timedelta(hours=12)
            union = e["union"]
            code = "REG"
            r = rng.random()
            if r < 0.06:
                code = "OT15" if union.startswith("Nurses") else "SWOT"
            elif r < 0.08:
                code = "PTO"
            schedule.append(dict(employee_id=e["employee_id"], unit_code=e["home_unit"],
                                 shift_start=start.isoformat(timespec="minutes"),
                                 shift_end=end.isoformat(timespec="minutes"), pay_code=code))

    census = []
    t0 = datetime.combine(START - timedelta(days=CENSUS_DAYS), datetime.min.time())
    for u in units:
        base = u["beds"] * 0.82
        for h in range(CENSUS_DAYS * 24):
            ts = t0 + timedelta(hours=h)
            val = max(0, min(u["beds"], round(base + rng.uniform(-3, 3))))
            census.append(dict(ehr_unit=u["ehr_unit"], hour=ts.isoformat(timespec="minutes"), census=val))

    return dict(units=units, job_skills=job_skills, contract_rules=contract_rules, pay_codes=pay_codes,
                unit_map=unit_map, staffing_grid=grid, hris_roster=roster,
                timekeeping_schedule=schedule, ehr_census=census)


def write_csvs(data, folder):
    os.makedirs(folder, exist_ok=True)
    for name, rows in data.items():
        if not rows:
            continue
        with open(os.path.join(folder, f"{name}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def read_csvs(folder):
    data = {}
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".csv"):
            with open(os.path.join(folder, fn), newline="") as f:
                data[fn[:-4]] = list(csv.DictReader(f))
    return data
