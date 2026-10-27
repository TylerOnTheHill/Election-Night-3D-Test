import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from overlay_florida_county_updates import overlay

class FloridaOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((ROOT / "data/early-vote/FL.json").read_text())

    def update(self):
        county = self.base["counties"][0]
        counts = copy.deepcopy(county["voted_early"])
        counts["total"] += 1
        counts["registration"]["republican"] += 1
        return {"county": county["county"], "source_url": "https://elections.example.gov/turnout",
                "compiled_at_local": "2026-10-26T15:00:00",
                "categories": {"voted_early": counts}}

    def test_replaces_not_adds_and_preserves_official_baseline(self):
        u = self.update()
        staged = overlay(self.base, [u])
        self.assertEqual(staged["staged_mixed_cutoff_totals"]["voted_early"]["total"],
                         self.base["statewide"]["voted_early"]["total"] + 1)
        self.assertEqual(staged["baseline_statewide"], self.base["statewide"])
        self.assertEqual(len(staged["counties"]), 67)
        self.assertEqual(len(staged["staged_supplemental_counties"]), 1)
        self.assertEqual(self.base["counties"][0]["voted_early"]["total"] + 1,
                         staged["counties"][0]["voted_early"]["total"])

    def test_rejects_old_source(self):
        u = self.update()
        u["compiled_at_local"] = "2026-10-25T15:00:00"
        with self.assertRaises(ValueError): overlay(self.base, [u])

    def test_rejects_duplicate_county(self):
        u = self.update()
        with self.assertRaises(ValueError): overlay(self.base, [u, u])

    def test_rejects_unreconciled_counts(self):
        u = self.update()
        u["categories"]["voted_early"]["total"] += 2
        with self.assertRaises(ValueError): overlay(self.base, [u])

    def test_rejects_non_https_source(self):
        u = self.update()
        u["source_url"] = "http://example.org"
        with self.assertRaises(ValueError): overlay(self.base, [u])

    def test_rejects_unknown_category(self):
        u = self.update()
        u["categories"]["candidate_votes"] = u["categories"]["voted_early"]
        with self.assertRaises(ValueError): overlay(self.base, [u])

if __name__ == "__main__":
    unittest.main()
