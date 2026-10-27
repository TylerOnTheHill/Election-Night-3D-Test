"""Approval gate and conversion tests; synthetic counts only."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_approved_county_feed import prepare
from test_county_publication_candidate import candidate

class PublicationConversionTests(unittest.TestCase):
    def test_unapproved_candidate_cannot_be_published(self):
        with self.assertRaisesRegex(ValueError, "Explicit owner"):
            prepare(candidate(), "")

    def test_approval_produces_browser_compatible_feed(self):
        original = candidate()
        result = prepare(original, "OWNER_APPROVED_TX_NC_COUNTY_PUBLICATION")
        self.assertTrue(result["publication_approved"])
        self.assertNotIn("review_required", result)
        self.assertEqual(set(result["states"]), {"TX", "NC"})
        for code in ("TX", "NC"):
            self.assertEqual(result["states"][code]["status"], "published")
            self.assertEqual(result["states"][code]["total_basis"], "sum_of_reported_counties")
        self.assertFalse(original["publication_approved"])

    def test_partial_counties_remain_partial_after_approval(self):
        c = candidate()
        tx = c["states"]["TX"]
        tx["counties"] = tx["counties"][:150]
        tx.update(county_count=150, coverage_complete=False,
                  reporting_label="Partially reported", total=300, statewide_cutoff=None)
        result = prepare(c, "OWNER_APPROVED_TX_NC_COUNTY_PUBLICATION")
        self.assertEqual(len(result["states"]["TX"]["counties"]), 150)
        self.assertFalse(result["states"]["TX"]["coverage_complete"])
        self.assertIsNone(result["states"]["TX"]["statewide_cutoff"])

    def test_bad_candidate_never_becomes_approved(self):
        c = candidate()
        c["states"]["TX"]["total"] += 1
        with self.assertRaisesRegex(ValueError, "aggregation"):
            prepare(c, "OWNER_APPROVED_TX_NC_COUNTY_PUBLICATION")

if __name__ == "__main__":
    unittest.main()
