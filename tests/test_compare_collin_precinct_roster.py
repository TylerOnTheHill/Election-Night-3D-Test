import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from compare_collin_precinct_roster import compare
def geo(ids):
 return {"type":"FeatureCollection","features":[{"properties":{"area_id":x}} for x in ids]}
class RosterAuditTests(unittest.TestCase):
 def test_matching_ids_does_not_certify_boundaries(self):
  r=compare(geo(["001","002"]),["002","001"])
  self.assertTrue(r["id_sets_match"])
  self.assertFalse(r["boundary_equivalence_verified"])
  self.assertFalse(r["publication_approved"])
 def test_missing_ids_reported(self):
  r=compare(geo(["001","002"]),["001","003"])
  self.assertEqual(r["missing_from_primary_geometry"],["003"])
  self.assertEqual(r["missing_from_general_roster"],["002"])
 def test_leading_zeros_preserved(self):
  r=compare(geo(["001"]),["1"])
  self.assertFalse(r["id_sets_match"])
 def test_duplicate_roster_rejected(self):
  with self.assertRaisesRegex(ValueError,"Duplicate roster"):compare(geo(["001"]),["001","001"])
 def test_duplicate_geometry_rejected(self):
  with self.assertRaisesRegex(ValueError,"Duplicate geometry"):compare(geo(["001","001"]),["001"])
if __name__=="__main__":unittest.main()
