import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_georgia_counties import stage

def fixture():
    return {"metadata":{"election":{"date":"2026-11-03","year":2026,"type":"general"},
            "asOf":"2026-10-26","dataGeneratedAt":"2026-10-27T12:00:00Z"},
            "statewide":{"ballots":120},"counties":[
                {"county_fips":"13001","county":"Appling","ballots":70,"in_person":60,"mail":10,"as_of":"2026-10-26"},
                {"county_fips":"13003","county":"Atkinson","ballots":30,"in_person":20,"mail":10,"as_of":"2026-10-26"}]}

class GeorgiaTests(unittest.TestCase):
    def test_partial_counties_are_shown_without_zero_filling(self):
        s=stage(fixture())
        ga=s["states"]["GA"]
        self.assertEqual(ga["county_count"],2)
        self.assertEqual(ga["total"],100)
        self.assertEqual(ga["provider_statewide_total"],120)
        self.assertEqual(ga["reporting_label"],"Partially reported")
        self.assertFalse(s["publication_approved"])
        self.assertFalse(ga["statewide_reconciled"])
    def test_reject_duplicate_fips(self):
        d=fixture()
        d["counties"][1]["county_fips"]="13001"
        with self.assertRaisesRegex(ValueError,"FIPS"):
            stage(d)
    def test_reject_method_double_count(self):
        d=fixture()
        d["counties"][0]["mail"]=11
        with self.assertRaisesRegex(ValueError,"reconciliation"):
            stage(d)
    def test_reject_county_exceeding_statewide(self):
        d=fixture()
        d["statewide"]["ballots"]=99
        with self.assertRaisesRegex(ValueError,"exceed"):
            stage(d)
    def test_reject_wrong_election(self):
        d=fixture()
        d["metadata"]["election"]["year"]=2024
        with self.assertRaisesRegex(ValueError,"2026"):
            stage(d)

if __name__=="__main__":
    unittest.main()
