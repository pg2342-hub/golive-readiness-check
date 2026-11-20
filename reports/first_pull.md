# Go-live readiness: Northgate University Health (sample data), sample_data/first_pull

8 units: 1 GO, 1 GO WITH FIXES, 6 NO-GO. 26 findings (21 blocking).

## Units

| Hospital | Unit | Verdict | Blocking | Warnings |
|---|---|---|---|---|
| Main Campus | 4 West Med-Surg (MC-4W) | NO-GO | 4 | 0 |
| Main Campus | 5 East Cardiac Stepdown (MC-5E) | NO-GO | 2 | 2 |
| Main Campus | Medical ICU (MC-MICU) | GO | 0 | 0 |
| Main Campus | Emergency Department (MC-ED) | NO-GO | 4 | 0 |
| Main Campus | Labor and Delivery (MC-LD) | NO-GO | 3 | 0 |
| Riverside | 3 North Med-Surg (RV-3N) | GO WITH FIXES | 0 | 1 |
| Riverside | ICU (RV-ICU) | NO-GO | 4 | 0 |
| Riverside | Emergency Department (RV-ED) | NO-GO | 2 | 1 |

## Fix list by team

### HR systems team (8)
- [blocking] Scheduled staff missing from the HR roster (MC-4W): E9001 is on the schedule for MC-4W but is not in the HR roster.
- [blocking] Duplicate employee IDs in the HR roster (MC-5E): Employee ID E1022 appears 2 times in the HR roster, so shifts cannot be tied to one person.
- [blocking] Shifts for staff marked terminated (MC-ED): E1048 is marked Terminated in the HR roster but still has shifts on MC-ED.
- [blocking] Shifts for staff marked terminated (MC-ED): E1059 is marked Terminated in the HR roster but still has shifts on MC-ED.
- [blocking] Scheduled staff missing from the HR roster (MC-LD): E9003 is on the schedule for MC-LD but is not in the HR roster.
- [blocking] Duplicate employee IDs in the HR roster (RV-ICU): Employee ID E1104 appears 2 times in the HR roster, so shifts cannot be tied to one person.
- [blocking] Scheduled staff missing from the HR roster (RV-ICU): E9002 is on the schedule for RV-ICU but is not in the HR roster.
- [warning] Home unit not in the unit list (not tied to a live unit): E1079 has home unit 'LD-OLD', which is not in the unit list.

### Labor relations (5)
- [blocking] Union-covered staff with no union on file (MC-4W): E1010 (Charge Nurse) is in a union-covered job but has no union on file, so contract rules cannot be applied.
- [blocking] Union-covered staff with no union on file (MC-4W): E1015 (Health Unit Coordinator) is in a union-covered job but has no union on file, so contract rules cannot be applied.
- [blocking] Pay code with no contract rule (MC-5E): Pay code 'INCSH' (Incentive extra shift) is used on MC-5E but has no matching contract rule, so it cannot be checked or paid correctly.
- [blocking] Union-covered staff with no union on file (MC-LD): E1069 (Staff Nurse II) is in a union-covered job but has no union on file, so contract rules cannot be applied.
- [blocking] Pay code with no contract rule (RV-ICU): Pay code 'CALLB' (Call-back) is used on RV-ICU but has no matching contract rule, so it cannot be checked or paid correctly.

### EHR interface team (6)
- [blocking] EHR census unit not mapped to a staffing unit (not tied to a live unit): Census unit 'MC 6W OBS' from the EHR does not map to a staffing unit, so its patients are not counted toward demand.
- [blocking] EHR census unit not mapped to a staffing unit (not tied to a live unit): Census unit 'RV ED' from the EHR does not map to a staffing unit, so its patients are not counted toward demand.
- [blocking] Staffing unit with no census feed (MC-LD): MC-LD has no census rows from the EHR, so the unit has no demand signal.
- [blocking] Staffing unit with no census feed (RV-ED): RV-ED has no census rows from the EHR, so the unit has no demand signal.
- [warning] Hours missing from the census feed (MC-5E): MC-5E is missing 10 of 168 census hours in the feed window.
- [warning] Hours missing from the census feed (RV-3N): RV-3N is missing 5 of 168 census hours in the feed window.

### Nursing operations (4)
- [blocking] Job code with no staffing role (MC-4W): E1001 has job code 'RNTRV', which has no staffing role, so they cannot be offered shifts.
- [blocking] No staffing grid for a role on the unit (MC-ED): MC-ED has Clerk shifts but no staffing grid for Clerk, so the number of Clerks needed cannot be computed.
- [blocking] Job code with no staffing role (RV-ED): E1122 has job code 'CNA2', which has no staffing role, so they cannot be offered shifts.
- [blocking] No staffing grid for a role on the unit (RV-ICU): RV-ICU has CNA shifts but no staffing grid for CNA, so the number of CNAs needed cannot be computed.

### Timekeeping admin (3)
- [blocking] Pay code missing from the pay code table (MC-ED): Pay code 'OT2X' is on MC-ED's schedule but missing from the pay code table.
- [warning] Overlapping shifts for one person (MC-5E): E1006 has a shift on MC-5E starting 2027-01-05 23:00 before their shift on MC-4W ends.
- [warning] Overlapping shifts for one person (RV-ED): E1111 has a shift on RV-ED starting 2027-01-05 07:00 before their shift on RV-ED ends.

