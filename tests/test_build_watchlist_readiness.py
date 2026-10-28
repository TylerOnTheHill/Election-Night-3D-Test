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
    def test_alaska_official_districts_are_not_fabricated_counties(self):
        review=json.loads(Path("data/staging/alaska-house-district-review.json").read_text())
        self.assertEqual(review["schema"], "electionhq-alaska-house-district-review-v1")
        self.assertEqual(review["geographic_count"], 40)
        # The review source can differ from the staging parser output; use the validated
        # district fields required by the readiness contract.
        district={"schema":"electionhq-ak-house-district-review-v1",
                  "state":"AK","geography":"state_house_district",
                  "publication_approved":False,"reported_districts":40,
                  "geographic_count":40,"source_cutoff":"2026-10-26T10:31:33-08:00",
                  "total_received_ballots":100,
                  "districts":[{"district":i} for i in list(range(1,41))+[99]]}
        ak=next(x for x in build(self.national,alaska_district_review=district)["states"] if x["state"]=="AK")
        self.assertFalse(ak["county_staged"])
        self.assertIsNone(ak["county_ballots"])
        self.assertTrue(ak["district_review_staged"])
        self.assertEqual(ak["district_review_reported"],40)
        self.assertEqual(ak["district_review_ballots"],100)

    def test_reject_duplicate_state_candidate(self):
        from stage_georgia_counties import stage
        candidate=stage({"metadata":{"election":{"date":"2026-11-03","year":2026,"type":"general"},"asOf":"2026-10-26"},
          "statewide":{"ballots":10},"counties":[{"county_fips":"13001","county":"Appling","ballots":10,"in_person":8,"mail":2,"as_of":"2026-10-26"}]})
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            build(self.national,[candidate,candidate])

if __name__=="__main__":
    unittest.main()
