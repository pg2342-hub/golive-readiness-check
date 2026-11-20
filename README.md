# golive-readiness-check

Demo page: https://pg2342-hub.github.io/golive-readiness-check/

A unit-by-unit go/no-go check for rolling a staffing system out across hospital units. Before a unit can go live, three feeds have to agree: the staff roster from the HR system, the schedule and pay codes from the timekeeping system, and the hourly patient census from the EHR's admit/discharge/transfer feed. This tool reads all three, finds the data problems that usually delay a go-live, says which units are ready, and groups every fix by the team that owns it (HR systems, timekeeping admin, EHR interface, labor relations, nursing operations).

All data here is made up. Unit names, unions, pay codes, staffing grids and contract rules are illustrative and do not describe any real hospital or contract.

## Run it

Python 3.9+, standard library only.

```
python3 -m readiness.report sample_data/first_pull    # the first data pull, with 25 planted problems
python3 -m readiness.report sample_data/after_fixes   # the same system after the fixes
python3 -m eval.run_eval                              # the eval below
python3 -m unittest                                   # 8 tests
```

To check your own extract, put CSVs with the same columns as `sample_data/after_fixes/` in a folder and point the report at it.

## What it checks

| Check | Severity | Team that fixes it |
|---|---|---|
| Scheduled staff missing from the HR roster | blocking | HR systems team |
| Shifts for staff marked terminated | blocking | HR systems team |
| Duplicate employee IDs in the HR roster | blocking | HR systems team |
| Home unit not in the unit list | warning | HR systems team |
| Job code with no staffing role | blocking | Nursing operations |
| Union-covered staff with no union on file | blocking | Labor relations |
| Pay code missing from the pay code table | blocking | Timekeeping admin |
| Pay code with no contract rule | blocking | Labor relations |
| EHR census unit not mapped to a staffing unit | blocking | EHR interface team |
| Staffing unit with no census feed | blocking | EHR interface team |
| Hours missing from the census feed (more than 2 in the window) | warning | EHR interface team |
| No staffing grid for a role on the unit | blocking | Nursing operations |
| Overlapping shifts for one person | warning | Timekeeping admin |

A unit is NO-GO if it has any blocking finding, GO WITH FIXES if it has only warnings, and GO otherwise.

## Eval

`eval/planted.py` plants 25 problems of the kind that delay go-lives (an agency nurse set up in timekeeping but never added to HR, a census unit renamed by the EHR interface, a pay code pointing to a contract rule that does not exist, and so on) into a clean two-hospital, eight-unit system.

| Run | Result |
|---|---|
| Clean system | 0 findings |
| Each problem planted alone | 25 of 25 caught, nothing extra reported |
| All 25 planted together | 25 of 25 caught, 0 false positives (26 findings, because one renamed census unit both breaks a mapping and leaves a unit with no census) |
| Verdicts before fixes | 6 of 8 units NO-GO, 1 GO WITH FIXES, 1 GO |
| Verdicts after fixes | 8 of 8 GO |

Results are written to `eval/results/eval_results.json`.

## Layout

```
readiness/sample.py   builds the made-up health system and reads/writes the CSVs
readiness/checks.py   the 13 checks, unit verdicts, fix list by team
readiness/report.py   prints the readiness report
eval/                 planted problems and the eval runner
docs/                 the demo page (built from real checker output by docs/build_page.py)
sample_data/          first_pull/ (25 problems) and after_fixes/ (clean)
reports/              the two reports as Markdown
```
