"""End-to-end county candidate creation using real vendored geography and synthetic provider reports."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_tx_nc_county_pipeline import run
from verify_tx_nc_fips import fetch_vendored


class IntegratedCountyPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "provider"
        self.input.mkdir()
        for code, reported in (("TX", 150), ("NC", 100)):
            geography, _ = fetch_vendored(code, str(ROOT / "data/sources/tx-nc-county-fips-reference.json"))
            rows = [
                {"state": code, "county": name, "total": 3,
                 "mail": 1, "in_person": 2, "dem": None, "rep": None,
                 "unaffiliated_other": None, "file_as_of": None,
                 "source_url": "https://example.org/early", "credit": "Fixture"}
                for name, _, _ in geography[1:reported + 1]
            ]
            payload = {
                "schema": "ctm-early-vote-download-v1", "state": code,
                "license": "Fixture", "credit": "Fixture",
                "summary": {"total": 5000, "file_as_of": None},
                "counties": rows,
            }
            (self.input / (code + ".json")).write_text(json.dumps(payload))

    def test_full_pipeline_partial_tx_complete_nc_without_publication(self):
        output = self.root / "candidate.json"
        summary = run(self.input, output)
        self.assertEqual(summary["TX"]["reported_counties"], 150)
        self.assertEqual(summary["TX"]["reported_ballots"], 450)
        self.assertEqual(summary["NC"]["reported_counties"], 100)
        self.assertEqual(summary["NC"]["reported_ballots"], 300)
        candidate = json.loads(output.read_text())
        self.assertIs(candidate["publication_approved"], False)
        self.assertIs(candidate["review_required"], True)
        self.assertFalse(candidate["states"]["TX"]["coverage_complete"])
        self.assertTrue(candidate["states"]["NC"]["coverage_complete"])
        self.assertEqual(candidate["states"]["TX"]["reporting_label"], "Partially reported")
        self.assertEqual(candidate["states"]["TX"]["total_basis"], "sum_of_reported_counties")
        self.assertIsNone(candidate["states"]["TX"]["counties"][0]["file_as_of"])

    def test_invalid_source_cannot_create_candidate(self):
        tx = self.input / "TX.json"
        payload = json.loads(tx.read_text())
        payload["counties"][0]["total"] = -1
        tx.write_text(json.dumps(payload))
        output = self.root / "candidate.json"
        with self.assertRaises(ValueError):
            run(self.input, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
