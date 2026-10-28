import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_battleground_release_readiness import audit

def fixture():
    return {"schema": "electionhq-watchlist-readiness-v1",
            "publication_approved": False,
            "states": [{"state": code, "county_staged": True,
                        "county_reported": 2, "county_expected": 2,
                        "county_ballots": 100, "county_cutoff": "2026-10-27",
                        "county_publication_approved": False,
                        "county_vs_statewide_cutoff": "matching"}
                       for code in ("AK","AZ","FL","GA","IA","KS","ME","MI","MN",
                                    "MS","NE","NV","NH","NC","OH","SC","TX","VA","WI")]}

class BattlegroundReleaseGateTests(unittest.TestCase):
    def test_nh_excluded_without_deleting_original_record(self):
        original = fixture()
        result = audit(original)
        self.assertEqual(result["states_assessed"], 18)
        self.assertNotIn("NH", [s["state"] for s in result["states"]])
        self.assertEqual(len(original["states"]), 19)
        self.assertEqual(result["excluded_from_battleground_assessment"], ["NH"])

    def test_all_staged_is_not_automatically_release_ready(self):
        result = audit(fixture())
        self.assertFalse(result["release_ready"])
        self.assertEqual(result["ready_count"], 0)
        self.assertTrue(all("publication_not_approved" in s["blockers"] for s in result["states"]))

    def test_missing_data_is_explicitly_blocked(self):
        doc = fixture()
        tx = next(s for s in doc["states"] if s["state"] == "TX")
        tx.update(county_staged=False, county_ballots=None)
        result = audit(doc)
        tx_result = next(s for s in result["states"] if s["state"] == "TX")
        self.assertIn("county_source_not_staged", tx_result["blockers"])

    def test_nh_status_does_not_change_release_gate(self):
        doc = fixture()
        baseline = audit(doc)
        nh = next(s for s in doc["states"] if s["state"] == "NH")
        nh.update(county_staged=False, county_ballots=None)
        self.assertEqual(audit(doc), baseline)

    def test_unverified_county_freshness_blocks_release(self):
        doc = fixture()
        va = next(s for s in doc["states"] if s["state"] == "VA")
        va["county_vs_statewide_cutoff"] = "mixed_or_unknown"
        row = next(s for s in audit(doc)["states"] if s["state"] == "VA")
        self.assertIn("county_source_freshness_not_verified", row["blockers"])

    def test_missing_cutoff_blocks_staged_state(self):
        doc = fixture()
        ak = next(s for s in doc["states"] if s["state"] == "AK")
        ak["county_cutoff"] = None
        result = audit(doc)
        row = next(s for s in result["states"] if s["state"] == "AK")
        self.assertIn("unverified_reporting_cutoff", row["blockers"])

    def test_county_sum_zero_is_valid_observation_not_missing(self):
        doc = fixture()
        tx = next(s for s in doc["states"] if s["state"] == "TX")
        tx["county_ballots"] = 0
        row = next(s for s in audit(doc)["states"] if s["state"] == "TX")
        self.assertNotIn("invalid_county_total", row["blockers"])

    def test_rejects_county_count_over_denominator(self):
        doc = fixture()
        tx = next(s for s in doc["states"] if s["state"] == "TX")
        tx["county_reported"] = 3
        row = next(s for s in audit(doc)["states"] if s["state"] == "TX")
        self.assertIn("invalid_county_coverage", row["blockers"])

    def test_no_mutation_of_source_readiness(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        audit(doc)
        self.assertEqual(doc, before)

    def test_rejects_missing_nh_from_original_watchlist(self):
        doc = fixture()
        doc["states"] = [s for s in doc["states"] if s["state"] != "NH"]
        with self.assertRaises(ValueError):
            audit(doc)

if __name__ == "__main__":
    unittest.main()
