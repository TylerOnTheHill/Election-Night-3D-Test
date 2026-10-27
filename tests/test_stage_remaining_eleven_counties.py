"""Verify batch ingestion produces real partial totals and explicit gaps."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from stage_remaining_eleven_counties import GEOIDS, build, geography

class ElevenStateBatchTests(unittest.TestCase):
    def test_batch_stages_observed_counties_without_filling_missing(self):
        features = []
        payloads = {}
        for code, (prefix, expected) in GEOIDS.items():
            for i in range(expected):
                features.append({"id": prefix + str(i).zfill(3),
                                 "properties": {"NAME": "County" + str(i)}})
            rows = []
            if code == "AZ":
                rows.append({"state": code, "county": "County0", "total": 125,
                             "source_url": "https://example.org/az", "credit": "Fixture",
                             "file_as_of": "2026-10-27"})
            payloads[code] = {"schema": "ctm-early-vote-download-v1", "state": code,
                              "credit": "Fixture", "license": "Fixture", "counties": rows,
                              "summary": {"total": 200}}
        result, gaps = build(payloads, {"features": features})
        self.assertEqual(set(result["states"]), {"AZ"})
        self.assertEqual(result["states"]["AZ"]["total"], 125)
        self.assertEqual(result["states"]["AZ"]["reporting_label"], "Partially reported")
        self.assertEqual(result["states"]["AZ"]["county_count"], 1)
        self.assertEqual(len(gaps), 10)
        self.assertFalse(result["publication_approved"])

    def test_missing_fips_is_not_assigned(self):
        rows = geography({"features": [{"properties": {"STATE": "04", "COUNTY": "001", "NAME": "Apache"}}]}, "04")
        self.assertEqual(rows[1], ["Apache", "04", "001"])

if __name__ == "__main__":
    unittest.main()
