import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from validate_national_early_vote import validate
BASE={"schema":"ctm-early-vote-download-v1","credit":"Call the Map","license":"With credit","national":{"total":30,"states_counted":2,"counts_through":{"first":"2026-10-25","last":"2026-10-26"}},"states":[{"state":"TX","total":20,"mail":5,"in_person":15,"source_name":"Publisher","source_url":"https://example.org/tx","counts_through":"2026-10-26"},{"state":"NC","total":10,"mail":None,"in_person":None,"source_name":"Publisher","source_url":"https://example.org/nc","counts_through":"2026-10-25"}]}
class NationalTests(unittest.TestCase):
 def test_valid_mixed_cutoffs(self):
  r=validate(BASE);self.assertEqual(r["reported_ballots"],30);self.assertEqual(r["states_with_full_mode_split"],1)
 def test_duplicate_state(self):
  d=copy.deepcopy(BASE);d["states"][1]["state"]="TX"
  with self.assertRaisesRegex(ValueError,"duplicate"):validate(d)
 def test_national_total_mismatch(self):
  d=copy.deepcopy(BASE);d["national"]["total"]=31
  with self.assertRaisesRegex(ValueError,"sum"):validate(d)
 def test_mode_sum_mismatch(self):
  d=copy.deepcopy(BASE);d["states"][0]["mail"]=6
  with self.assertRaisesRegex(ValueError,"sum mismatch"):validate(d)
 def test_cutoff_mismatch(self):
  d=copy.deepcopy(BASE);d["national"]["counts_through"]["first"]="2026-10-24"
  with self.assertRaisesRegex(ValueError,"date range"):validate(d)
 def test_missing_attribution(self):
  d=copy.deepcopy(BASE);d["states"][0]["source_url"]=""
  with self.assertRaisesRegex(ValueError,"source"):validate(d)
if __name__=="__main__":unittest.main()
