import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_watchlist_county_reconciliation import audit

def candidate(cutoff="2026-10-27",statewide=100):
    return {"publication_approved":False,"review_required":True,"states":{
        "VA":{"total":130,"provider_statewide_total":statewide,
              "statewide_cutoff":cutoff,"reporting_label":"Partially reported",
              "geographic_count":133,"counties":[{"total":130,"file_as_of":"2026-10-26",
              "source_url":"https://example.org/official"}]}}}

class AuditTests(unittest.TestCase):
    def test_different_cutoffs_do_not_explain_away_mismatch(self):
        result=audit(candidate())["states"]["VA"]
        self.assertEqual(result["difference"],30)
        self.assertEqual(result["county_vs_statewide_cutoff"],"county_older")
        self.assertEqual(result["reconciliation_status"],"different_cutoffs_or_unknown")
        self.assertFalse(result["freshness_verified"])

    def test_matching_cutoff_mismatch_is_unreconciled(self):
        doc=candidate("2026-10-26")
        result=audit(doc)["states"]["VA"]
        self.assertEqual(result["reconciliation_status"],"same_cutoff_unreconciled")

    def test_matching_totals_still_do_not_imply_publication(self):
        result=audit(candidate(statewide=130))["states"]["VA"]
        self.assertEqual(result["reconciliation_status"],"matching")
        self.assertFalse(result["publication_approved"])

if __name__=="__main__":
    unittest.main()
