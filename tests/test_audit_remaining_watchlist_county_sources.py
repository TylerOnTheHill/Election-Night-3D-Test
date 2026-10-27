import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_remaining_watchlist_county_sources import inspect,discover,STATES

def payload(code):
    return {"schema":"ctm-early-vote-download-v1","state":code,
            "credit":"Test provider","license":"Test license",
            "summary":{"total":100},"counties":[
                {"state":code,"county":"Alpha","total":7,
                 "source_url":"https://example.org/source","credit":"Test",
                 "file_as_of":"2026-10-27"},
                {"state":code,"county":"Beta","total":None}]}

class SourceDiscoveryTests(unittest.TestCase):
    def test_all_remaining_states_are_checked_without_zero_fill(self):
        result=discover({code:payload(code) for code in STATES})
        self.assertEqual(len(result["states"]),11)
        self.assertEqual(set(result["states_with_county_observations"]),set(STATES))
        for state in result["states"].values():
            self.assertEqual(state["county_rows_with_observed_totals"],1)
            self.assertEqual(state["observed_county_ballots"],7)
            self.assertFalse(state["fips_verified"])
            self.assertFalse(state["publication_approved"])

    def test_missing_counts_do_not_become_zero(self):
        doc=payload("NH")
        doc["counties"][0]["total"]=None
        result=inspect("NH",doc)
        self.assertEqual(result["county_rows_with_observed_totals"],0)
        self.assertFalse(result["ready_for_fips_crosswalk"])

    def test_duplicate_county_rejected(self):
        doc=payload("AZ")
        doc["counties"].append(dict(doc["counties"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            inspect("AZ",doc)

    def test_missing_provenance_rejected(self):
        doc=payload("KS")
        doc["counties"][0]["source_url"]=""
        with self.assertRaisesRegex(ValueError,"provenance"):
            inspect("KS",doc)

if __name__=="__main__":
    unittest.main()
