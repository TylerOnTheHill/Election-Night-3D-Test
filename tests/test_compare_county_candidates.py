"""County snapshots must replace prior observations, not accumulate them."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_county_candidates import compare
from test_county_publication_candidate import candidate

def partial_tx(doc, count):
    state = doc["states"]["TX"]
    state["counties"] = state["counties"][:count]
    state["county_count"] = count
    state["coverage_complete"] = count == 254
    state["reporting_label"] = "Fully reported" if count == 254 else "Partially reported"
    state["total"] = sum(r["total"] for r in state["counties"])

class CountyComparisonTests(unittest.TestCase):
    def test_partial_coverage_growth_only_counts_new_counties(self):
        before, after = candidate(), candidate()
        partial_tx(before, 150)
        partial_tx(after, 160)
        result = compare(before, after)["states"]["TX"]
        self.assertEqual(result["new_counties"], 10)
        self.assertEqual(result["revised_counties"], 0)
        self.assertEqual(result["counties_reported"], 160)
        self.assertEqual(result["latest_reported_ballots"], 320)
        self.assertEqual(result["net_change_in_reported_county_totals"], 20)
        self.assertEqual(result["reporting_status"], "Partially reported")

    def test_same_county_correction_replaces_prior_total(self):
        before, after = candidate(), candidate()
        after["states"]["TX"]["counties"][0]["total"] = 7
        after["states"]["TX"]["total"] += 5
        result = compare(before, after)["states"]["TX"]
        self.assertEqual(result["revised_counties"], 1)
        self.assertEqual(result["new_counties"], 0)
        self.assertEqual(result["latest_reported_ballots"], 513)
        self.assertEqual(result["net_change_in_reported_county_totals"], 5)

    def test_missing_county_rejected(self):
        before, after = candidate(), candidate()
        partial_tx(after, 150)
        with self.assertRaisesRegex(ValueError, "disappeared"):
            compare(before, after)

    def test_stale_county_cutoff_rejected(self):
        before, after = candidate(), candidate()
        after["states"]["TX"]["counties"][0]["file_as_of"] = "2026-10-26"
        with self.assertRaisesRegex(ValueError, "county .* regressed"):
            compare(before, after)

    def test_stale_statewide_cutoff_rejected(self):
        before, after = candidate(), candidate()
        after["states"]["TX"]["statewide_cutoff"] = "2026-10-26"
        with self.assertRaisesRegex(ValueError, "statewide reporting cutoff"):
            compare(before, after)

    def test_unapproved_data_stays_unapproved(self):
        before, after = candidate(), candidate()
        result = compare(before, after)
        self.assertEqual(result["status"], "review_only_not_approved_for_publication")
        self.assertIs(after["publication_approved"], False)

if __name__ == "__main__":
    unittest.main()
