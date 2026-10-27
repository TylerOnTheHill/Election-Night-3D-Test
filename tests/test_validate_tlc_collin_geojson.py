import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from validate_tlc_collin_geojson import validate
BASE={"type":"FeatureCollection","features":[{"type":"Feature","properties":{"county_fips":"48085","area_id":"00101"},"geometry":{"type":"Polygon","coordinates":[[[-96.7,33.1],[-96.6,33.1],[-96.6,33.2],[-96.7,33.1]]]}}]}
class GeometryTests(unittest.TestCase):
 def test_valid_primary_is_never_general_certified(self):
  r=validate(BASE)
  self.assertEqual(r["precinct_count"],1)
  self.assertFalse(r["publication_approved"])
  self.assertFalse(r["verified_for_2026_general"])
 def test_duplicate(self):
  d=copy.deepcopy(BASE);d["features"].append(copy.deepcopy(d["features"][0]))
  with self.assertRaisesRegex(ValueError,"Duplicate"):validate(d)
 def test_reject_projected_coordinates(self):
  d=copy.deepcopy(BASE);d["features"][0]["geometry"]["coordinates"][0][0]=[123456,456789]
  d["features"][0]["geometry"]["coordinates"][0][-1]=[123456,456789]
  with self.assertRaisesRegex(ValueError,"Not WGS84"):validate(d)
 def test_reject_wrong_county(self):
  d=copy.deepcopy(BASE);d["features"][0]["properties"]["county_fips"]="48201"
  with self.assertRaisesRegex(ValueError,"county"):validate(d)
 def test_reject_unclosed_ring(self):
  d=copy.deepcopy(BASE);d["features"][0]["geometry"]["coordinates"][0][-1]=[-96.8,33.1]
  with self.assertRaisesRegex(ValueError,"Unclosed"):validate(d)
if __name__=="__main__":unittest.main()
