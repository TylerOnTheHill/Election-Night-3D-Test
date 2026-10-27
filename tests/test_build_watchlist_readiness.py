import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_watchlist_readiness import build

class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.national=json.loads(Path("data/early-vote/US.json").read_text())
    def test_every_state_included_and_missing_not_zero(self):
        result=build(self.national)
        self.assertEqual(len(result["states"]),19)
        self.assertEqual(len({x["state"] for x in result["states"]}),19)
        self.assertFalse(result["county_totals_added_to_statewide"])
        self.assertTrue(all(s["county_ballots"] is None for s in result["states"]))
    def test_missing_statewide_stays_null(self):
        result=build(self.national)
        missing=[s for s in result["states"] if not s["statewide_reporting"]]
        self.assertTrue(all(s["statewide_ballots"] is None for s in missing))
    def test_reject_duplicate_state_candidate(self):
        from stage_georgia_counties import stage
        candidate=stage({"metadata":{"election":{"date":"2026-11-03","year":2026,"type":"general"},"asOf":"2026-10-26"},
          "statewide":{"ballots":10},"counties":[{"county_fips":"13001","county":"Appling","ballots":10,"in_person":8,"mail":2,"as_of":"2026-10-26"}]})
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            build(self.national,[candidate,candidate])

if __name__=="__main__":
    unittest.main()
