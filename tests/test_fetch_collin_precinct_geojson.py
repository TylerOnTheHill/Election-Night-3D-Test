import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs,urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fetch_collin_precinct_geojson import collect

def feature(n):
 return {"type":"Feature","properties":{"OBJECTID":n,"PRECINCT":n},
         "geometry":{"type":"Polygon","coordinates":[[[-97,33],[-96,33],[-96,34],[-97,33]]]}}

class CollinFetchTests(unittest.TestCase):
 def test_pagination(self):
  def fetch(url):
   offset=int(parse_qs(urlparse(url).query)["resultOffset"][0])
   return {"type":"FeatureCollection","features":[feature(x) for x in [101,102,103][offset:offset+2]]}
  result=collect(fetch,page_size=2)
  self.assertEqual(len(result["features"]),3)
  self.assertEqual(result["features"][2]["properties"]["area_id"],"103")
 def test_duplicate_objectid(self):
  def fetch(url):
   return {"type":"FeatureCollection","features":[feature(101),feature(101)]}
  with self.assertRaises(ValueError):collect(fetch,page_size=2)
 def test_api_error(self):
  with self.assertRaises(ValueError):collect(lambda _:{"error":{"message":"denied"}})
 def test_empty(self):
  with self.assertRaises(ValueError):collect(lambda _:{"type":"FeatureCollection","features":[]})
 def test_invalid_page_size(self):
  with self.assertRaises(ValueError):collect(lambda _:{},page_size=0)
if __name__=="__main__":unittest.main()
