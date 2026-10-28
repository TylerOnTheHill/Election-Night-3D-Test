import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from combine_county_candidates import combine
from test_county_publication_candidate import candidate

class CombinedCountyReviewTests(unittest.TestCase):
    def test_combines_without_changing_counts_or_approval(self):
        original=candidate()
        codes=list(original["states"])
        pieces=[]
        for code in codes:
            part=copy.deepcopy(original)
            part["states"]={code:part["states"][code]}
            pieces.append(part)
        merged=combine(pieces)
        self.assertEqual(set(merged["states"]),set(codes))
        self.assertFalse(merged["publication_approved"])
        self.assertTrue(merged["review_required"])
        for code in codes:
            self.assertEqual(merged["states"][code]["total"],original["states"][code]["total"])

    def test_duplicate_state_rejected_instead_of_double_counted(self):
        original=candidate()
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            combine([original,copy.deepcopy(original)])

    def test_combination_order_does_not_change_county_totals(self):
        original=candidate()
        pieces=[]
        for code,state in original["states"].items():
            part=copy.deepcopy(original)
            part["states"]={code:copy.deepcopy(state)}
            pieces.append(part)
        forward=combine(pieces)
        reverse=combine(list(reversed(pieces)))
        self.assertEqual(forward,reverse)
        for code in original["states"]:
            self.assertEqual(forward["states"][code]["counties"],original["states"][code]["counties"])

    def test_rejects_overlapping_snapshot_even_if_counts_differ(self):
        original=candidate()
        revised=copy.deepcopy(original)
        code=next(iter(revised["states"]))
        revised["states"]={code:revised["states"][code]}
        revised["states"][code]["counties"][0]["total"]+=10
        revised["states"][code]["total"]+=10
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            combine([original,revised])

    def test_approved_input_cannot_be_laundered_into_review(self):
        original=candidate()
        original["publication_approved"]=True
        with self.assertRaises(ValueError):
            combine([original])

if __name__=="__main__":
    unittest.main()
