"""Audit provider timestamps and statewide/county reconciliation before publication."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_county_source_freshness import review
from test_county_publication_candidate import candidate

NOW = datetime(2026, 10, 28, tzinfo=timezone.utc)

class CountySourceReviewTests(unittest.TestCase):
    def test_unknown_cutoffs_remain_unknown_not_fresh(self):
        doc = candidate()
        for state in doc["states"].values():
            state["statewide_cutoff"] = None
            for county in state["counties"]:
                county["file_as_of"] = None
        result = review(doc, NOW)
        tx = result["states"]["TX"]
        self.assertEqual(tx["counties_without_source_cutoff"], 254)
        self.assertIsNone(tx["latest_county_cutoff"])
        self.assertIs(tx["freshness_verified"], False)
        self.assertIs(result["states"]["NC"]["publication_approved"], False)

    def test_reconciliation_difference_is_explicit_not_added(self):
        doc = candidate()
        doc["states"]["TX"]["provider_statewide_total"] = 800
        result = review(doc, NOW)["states"]["TX"]
        self.assertEqual(result["county_ballots_observed"], 508)
        self.assertEqual(result["county_minus_provider_statewide"], -292)
        self.assertEqual(result["county_total_basis"], "sum_of_reported_counties")

    def test_future_county_cutoff_is_rejected(self):
        doc = candidate()
        doc["states"]["TX"]["counties"][0]["file_as_of"] = "2026-10-29"
        with self.assertRaisesRegex(ValueError, "future"):
            review(doc, NOW)

    def test_future_provider_checked_at_is_rejected(self):
        doc = candidate()
        doc["states"]["NC"]["provider_checked_at"] = "2026-10-29T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "future"):
            review(doc, NOW)

    def test_earliest_latest_dates_are_exposed(self):
        doc = candidate()
        doc["states"]["TX"]["counties"][0]["file_as_of"] = "2026-10-25"
        result = review(doc, NOW)["states"]["TX"]
        self.assertEqual(result["counties_with_source_cutoff"], 254)
        self.assertTrue(result["earliest_county_cutoff"].startswith("2026-10-25"))
        self.assertTrue(result["latest_county_cutoff"].startswith("2026-10-27"))

if __name__ == "__main__":
    unittest.main()
