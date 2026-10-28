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
                        "county_publication_approved": False}
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

    def test_rejects_missing_nh_from_original_watchlist(self):
        doc = fixture()
        doc["states"] = [s for s in doc["states"] if s["state"] != "NH"]
        with self.assertRaises(ValueError):
            audit(doc)

if __name__ == "__main__":
    unittest.main()
