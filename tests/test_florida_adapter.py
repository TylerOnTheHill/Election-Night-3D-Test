import copy
import unittest
from scripts.florida_county_adapter import normalize

BASE = {
    "source_url": "https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats",
    "election_id": "49894", "reported_through": "2026-10-26",
    "rows": [
        {"county": "Alachua", "category": "voted_mail", "republican": 2,
         "democrat": 3, "other": 0, "no_party_affiliation": 1, "total": 6},
        {"county": "Alachua", "category": "voted_early", "republican": 5,
         "democrat": 3, "other": 1, "no_party_affiliation": 1, "total": 10},
    ],
}

class FloridaAdapterTests(unittest.TestCase):
    def test_valid_and_partial_coverage(self):
        result = normalize(copy.deepcopy(BASE))
        self.assertEqual(len(result["records"]), 2)
        self.assertFalse(result["coverage"]["complete_both_categories"])
        self.assertEqual(result["state_fips"], "12")

    def test_rejects_double_counting(self):
        data = copy.deepcopy(BASE)
        data["rows"].append(copy.deepcopy(data["rows"][0]))
        with self.assertRaises(AssertionError):
            normalize(data)

    def test_rejects_inconsistent_totals(self):
        data = copy.deepcopy(BASE)
        data["rows"][0]["total"] = 100
        with self.assertRaises(AssertionError):
            normalize(data)

    def test_rejects_negative_counts(self):
        data = copy.deepcopy(BASE)
        data["rows"][0]["republican"] = -1
        with self.assertRaises(AssertionError):
            normalize(data)

    def test_rejects_statewide_reconciliation_on_partial_coverage(self):
        data = copy.deepcopy(BASE)
        data["statewide"] = {
            "voted_mail": {"total": 6, "republican": 2, "democrat": 3,
                           "other": 0, "no_party_affiliation": 1},
            "voted_early": {"total": 10, "republican": 5, "democrat": 3,
                            "other": 1, "no_party_affiliation": 1},
        }
        with self.assertRaises(AssertionError):
            normalize(data)

    def test_rejects_mismatched_compilation_times(self):
        data = copy.deepcopy(BASE)
        data["county_compiled_at"] = "2026-10-26T08:06:00-04:00"
        data["statewide_compiled_at"] = "2026-10-25T08:06:00-04:00"
        data["statewide"] = {
            "voted_mail": {"total": 6, "republican": 2, "democrat": 3,
                           "other": 0, "no_party_affiliation": 1},
            "voted_early": {"total": 10, "republican": 5, "democrat": 3,
                            "other": 1, "no_party_affiliation": 1},
        }
        with self.assertRaisesRegex(AssertionError, "Different county and statewide snapshots"):
            normalize(data)

    def test_rejects_reporting_date_outside_election_window(self):
        data = copy.deepcopy(BASE)
        data["reported_through"] = "2025-10-26"
        with self.assertRaises(AssertionError):
            normalize(data)

    def test_rejects_wrong_election(self):
        data = copy.deepcopy(BASE)
        data["election_id"] = "other"
        with self.assertRaises(AssertionError):
            normalize(data)

if __name__ == "__main__":
    unittest.main()
