import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from merge_restricted_nineteen_state_review import merge
from test_county_publication_candidate import candidate

class RestrictedNineteenStateMergeTests(unittest.TestCase):
    def test_joins_new_state_without_adding_overlapping_totals(self):
        standard=candidate()
        restricted={"schema":"electionhq-county-preview-v1","redistribution_authorized":False,
                    "states":{"TX":{"total":999,"counties":[{"fips":"48001","total":999}]},
                              "AZ":{"total":13,"reporting_label":"Partially reported",
                                    "counties":[{"fips":"04001","total":13}]}}}
        result=merge(standard,restricted)
        self.assertEqual(result["states"]["TX"]["total"],standard["states"]["TX"]["total"])
        self.assertEqual(result["states"]["AZ"]["total"],13)
        self.assertFalse(result["county_totals_added_across_sources"])
        self.assertFalse(result["redistribution_authorized"])
    def test_rejects_inconsistent_restricted_total(self):
        standard=candidate()
        restricted={"schema":"electionhq-county-preview-v1","redistribution_authorized":False,
                    "states":{"AZ":{"total":14,"counties":[{"fips":"04001","total":13}]}}}
        with self.assertRaisesRegex(ValueError,"totals"):
            merge(standard,restricted)

if __name__=="__main__":
    unittest.main()
