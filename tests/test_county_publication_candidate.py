import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_county_publication_candidate import validate

def candidate():
    states = {}
    for code, expected, prefix in (("TX", 254, "48"), ("NC", 100, "37")):
        rows = [{"fips": prefix + str(i).zfill(3), "name": "County " + str(i),
                 "total": 2, "file_as_of": "2026-10-27",
                 "source_url": "https://example.org", "credit": "Fixture"} for i in range(expected)]
        states[code] = {
            "status": "candidate_pending_publication_approval", "counties": rows,
            "county_count": expected, "geographic_count": expected,
            "coverage_complete": True, "reporting_label": "Fully reported",
            "total_basis": "sum_of_reported_counties", "total": 2 * expected,
            "provider": "Fixture", "credit": "Fixture",
            "census_geography_source": "Fixture", "census_geography_url": "https://example.org"}
    return {"schema": "electionhq-county-preview-v1",
            "publication_approved": False, "review_required": True, "states": states}

class CandidateGateTests(unittest.TestCase):
    def test_valid_unapproved_candidate(self):
        self.assertEqual(validate(candidate())["TX"]["reported_counties"], 254)

    def test_refuses_approved_flag(self):
        c = candidate()
        c["publication_approved"] = True
        with self.assertRaises(ValueError):
            validate(c)

    def test_accepts_partial_with_explicit_label(self):
        c = candidate()
        tx = c["states"]["TX"]
        tx["counties"] = tx["counties"][:150]
        tx.update(county_count=150, coverage_complete=False,
                  reporting_label="Partially reported", total=300)
        self.assertEqual(validate(c)["TX"]["reported_counties"], 150)

    def test_rejects_partial_as_complete(self):
        c = candidate()
        c["states"]["TX"]["counties"] = c["states"]["TX"]["counties"][:150]
        with self.assertRaises(ValueError):
            validate(c)

    def test_rejects_duplicate_fips(self):
        c = candidate()
        c["states"]["NC"]["counties"][1]["fips"] = c["states"]["NC"]["counties"][0]["fips"]
        with self.assertRaises(ValueError):
            validate(c)

    def test_rejects_missing_provenance(self):
        c = candidate()
        c["states"]["TX"]["counties"][0]["source_url"] = ""
        with self.assertRaises(ValueError):
            validate(c)

    def test_rejects_bad_aggregation(self):
        c = candidate()
        c["states"]["TX"]["total"] += 1
        with self.assertRaises(ValueError):
            validate(c)

if __name__ == "__main__":
    unittest.main()
