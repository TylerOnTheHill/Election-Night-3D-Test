import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from check_tx_precinct_geometry import check_join
from test_tx_local_returns import BASE

class GeometryJoinTests(unittest.TestCase):
 def geo(self,precinct="0001"):
  return {"type":"FeatureCollection","features":[{"type":"Feature","properties":{"county":"48201","precinct":precinct},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}}]}
 def test_match_remains_staging(self):
  result=check_join(copy.deepcopy(BASE),self.geo(),"county","precinct")
  self.assertEqual(result["matched"],1)
  self.assertFalse(result["publication_approved"])
 def test_unmatched_data_reported(self):
  result=check_join(copy.deepcopy(BASE),self.geo("0002"),"county","precinct")
  self.assertEqual(result["unmatched_data"],[["48201","0001"]])
 def test_reject_duplicate_geometry(self):
  geo=self.geo();geo["features"].append(copy.deepcopy(geo["features"][0]))
  with self.assertRaises(ValueError):check_join(copy.deepcopy(BASE),geo,"county","precinct")
 def test_reject_missing_attribute(self):
  with self.assertRaises(ValueError):check_join(copy.deepcopy(BASE),self.geo(),"FIPS","precinct")
if __name__=="__main__":unittest.main()
