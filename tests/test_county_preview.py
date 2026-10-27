import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_county_preview import build

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for code, count in (("TX", 254), ("NC", 100)):
            prefix = "48" if code == "TX" else "37"
            rows = [{"fips": prefix + str(i).zfill(3), "county": "County " + str(i),
                     "total": 1, "mail": None, "in_person": None,
                     "registered_dem": None, "registered_rep": None,
                     "registered_unaffiliated_other": None, "file_as_of": "2026-10-27",
                     "source_url": "https://example.org", "credit": "Test"} for i in range(count)]
            payload = {"state": code, "status": "staging_only_fips_and_coverage_verified",
                       "fips_verified": True, "coverage_complete": True,
                       "provider": "Call the Map", "credit": "Test", "statewide_total": count,
                       "census_geography_source": "Test reference",
                       "census_geography_url": "https://example.org", "counties": rows}
            Path(self.temp.name, code + ".json").write_text(json.dumps(payload))
    def test_build_preview_is_not_publication_approved(self):
        preview = build(self.temp.name)
        self.assertIs(preview["publication_approved"], False)
        self.assertEqual(len(preview["states"]["TX"]["counties"]), 254)
        self.assertEqual(len(preview["states"]["NC"]["counties"]), 100)
        self.assertIn("registration", preview["party_counts_mean"])
    def test_reject_unverified(self):
        p = Path(self.temp.name, "TX.json")
        d = json.loads(p.read_text())
        d["fips_verified"] = False
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):
            build(self.temp.name)
    def test_reject_bad_total(self):
        p = Path(self.temp.name, "NC.json")
        d = json.loads(p.read_text())
        d["statewide_total"] += 1
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):
            build(self.temp.name)
    def test_reject_duplicate_fips(self):
        p = Path(self.temp.name, "TX.json")
        d = json.loads(p.read_text())
        d["counties"][1]["fips"] = d["counties"][0]["fips"]
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):
            build(self.temp.name)

if __name__ == "__main__":
    unittest.main()
