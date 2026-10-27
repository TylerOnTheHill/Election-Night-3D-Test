import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from stage_callthemap_county_pilots import validate

def fixture(code="TX"):
    return {"schema":"ctm-early-vote-download-v1", "state":code,
            "credit":"Call the Map", "license":"free with credit",
            "summary":{"total":15,"file_as_of":"2026-10-26"},
            "counties":[{"state":code,"county":"Example","total":15,"mail":10,
                         "in_person":5,"dem":4,"rep":6,"unaffiliated_other":5,
                         "file_as_of":"2026-10-26T12:00:00Z",
                         "source_url":"https://example.gov/early","credit":"CTM"}]}

class PilotTests(unittest.TestCase):
    def test_valid_staging_not_published(self):
        r = validate("TX", fixture())
        self.assertEqual(r["county_sum"], 15)
        self.assertFalse(r["fips_verified"])
        self.assertIsNone(r["coverage_complete"])
    def test_county_total_precedence_when_statewide_differs(self):
        f=fixture();f["summary"]["total"]=16
        r=validate("TX",f)
        self.assertEqual(r["county_sum"],15)
        self.assertEqual(r["statewide_total"],16)
        self.assertEqual(r["county_vs_provider_statewide_difference"],-1)
        self.assertFalse(r["fips_verified"])
    def test_rejects_party_mismatch(self):
        f=fixture();f["counties"][0]["dem"]=5
        with self.assertRaises(ValueError):validate("TX",f)
    def test_rejects_method_mismatch(self):
        f=fixture();f["counties"][0]["mail"]=9
        with self.assertRaises(ValueError):validate("TX",f)
    def test_rejects_duplicate(self):
        f=fixture();f["counties"].append(dict(f["counties"][0]));f["summary"]["total"]=30
        with self.assertRaises(ValueError):validate("TX",f)
    def test_rejects_missing_source(self):
        f=fixture();f["counties"][0]["source_url"]="http://example.gov"
        with self.assertRaises(ValueError):validate("TX",f)
    def test_missing_county_cutoff_does_not_discard_verified_count(self):
        f=fixture();f["counties"][0]["file_as_of"]=None
        r=validate("TX",f)
        self.assertEqual(r["county_sum"],15)
        self.assertIsNone(r["counties"][0]["file_as_of"])
    def test_rejects_invalid_supplied_cutoff(self):
        f=fixture();f["counties"][0]["file_as_of"]="not-a-date"
        with self.assertRaises(ValueError):validate("TX",f)
    def test_north_carolina(self):
        self.assertEqual(validate("NC",fixture("NC"))["state"],"NC")

if __name__ == "__main__":
    unittest.main()
