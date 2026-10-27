import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_national_early_vote import audit
from test_refresh_early_vote import snapshot

class NationalAuditTests(unittest.TestCase):
    def test_missing_watchlist_states_are_unknown(self):
        doc=snapshot()
        result=audit(doc)
        self.assertEqual(result["national_reporting_states"],30)
        self.assertEqual(result["national_observed_ballots"],doc["national"]["total"])
        self.assertEqual(result["watchlist_reported_states"],0)
        self.assertEqual(len(result["watchlist_missing_states"]),19)
        self.assertTrue(all(s["ballots"] is None for s in result["watchlist_states"]))
        self.assertFalse(result["missing_counts_are_zero"])

    def test_watchlist_is_not_national_total(self):
        doc=snapshot()
        doc["states"][0]["state"]="TX"
        result=audit(doc)
        self.assertEqual(result["watchlist_reported_states"],1)
        self.assertEqual(result["watchlist_observed_ballots"],100)
        self.assertGreater(result["national_observed_ballots"],result["watchlist_observed_ballots"])
        self.assertFalse(result["county_totals_added_to_national"])

    def test_invalid_national_sum_rejected(self):
        doc=snapshot()
        doc["national"]["total"]+=1
        with self.assertRaisesRegex(ValueError,"National sum mismatch"):
            audit(doc)

if __name__=="__main__":
    unittest.main()
