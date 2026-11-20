import unittest

from eval.planted import ISSUES, planted_system, single_issue_system
from readiness.checks import CHECKS, run_checks, unit_verdicts
from readiness.sample import build, read_csvs, write_csvs


class ReadinessTests(unittest.TestCase):
    def test_clean_system_has_no_findings(self):
        self.assertEqual(run_checks(build()), [])

    def test_clean_system_is_all_go(self):
        d = build()
        self.assertTrue(all(v["verdict"] == "GO" for v in unit_verdicts(d, run_checks(d)).values()))

    def test_each_issue_alone_is_caught_with_nothing_extra(self):
        for i in range(len(ISSUES)):
            d, exp = single_issue_system(i)
            got = {(f["check"], f["key"]) for f in run_checks(d)}
            self.assertEqual(got, set(exp), ISSUES[i][1])

    def test_every_check_is_exercised_by_a_planted_issue(self):
        _, expected = planted_system()
        used = {c for _, _, ks in expected for c, _ in ks}
        self.assertEqual(used, set(CHECKS))

    def test_blocking_finding_makes_unit_no_go(self):
        d, _ = single_issue_system(0)  # agency nurse missing from HR on 4 West
        self.assertEqual(unit_verdicts(d, run_checks(d))["MC-4W"]["verdict"], "NO-GO")

    def test_warning_only_unit_is_go_with_fixes(self):
        d, _ = single_issue_system(20)  # Riverside med-surg census gap
        self.assertEqual(unit_verdicts(d, run_checks(d))["RV-3N"]["verdict"], "GO WITH FIXES")

    def test_small_census_gap_is_tolerated(self):
        d = build()
        rows = [c for c in d["ehr_census"] if c["ehr_unit"] == "RV ICU"][10:12]
        d["ehr_census"] = [c for c in d["ehr_census"] if c not in rows]
        self.assertEqual(run_checks(d), [])

    def test_csv_round_trip_gives_same_findings(self):
        import tempfile
        d, _ = planted_system()
        with tempfile.TemporaryDirectory() as tmp:
            write_csvs(d, tmp)
            back = read_csvs(tmp)
        key = lambda fs: sorted((f["check"], f["key"]) for f in fs)
        self.assertEqual(key(run_checks(back)), key(run_checks(d)))


if __name__ == "__main__":
    unittest.main()
