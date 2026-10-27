import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_county_preview import build, build_publication_candidate

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
    def test_candidate_requires_separate_publication_approval(self):
        candidate = build_publication_candidate(self.temp.name)
        self.assertIs(candidate["publication_approved"], False)
        self.assertIs(candidate["review_required"], True)
        self.assertEqual(candidate["states"]["TX"]["status"], "candidate_pending_publication_approval")
        self.assertEqual(candidate["states"]["NC"]["total"], 100)
    def test_reject_unverified(self):
        p = Path(self.temp.name, "TX.json")
        d = json.loads(p.read_text())
        d["fips_verified"] = False
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):
            build(self.temp.name)
    def test_complete_county_sum_takes_precedence_over_statewide_headline(self):
        p = Path(self.temp.name, "NC.json")
        d = json.loads(p.read_text())
        d["statewide_total"] -= 10
        p.write_text(json.dumps(d))
        result = build(self.temp.name)["states"]["NC"]
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["provider_statewide_total"], 90)
        self.assertEqual(result["county_vs_provider_statewide_difference"], 10)
        self.assertEqual(result["total_basis"], "sum_of_complete_county_reports")
    def test_reject_invalid_county_total(self):
        p = Path(self.temp.name, "NC.json")
        d = json.loads(p.read_text())
        d["counties"][0]["total"] = -1
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
