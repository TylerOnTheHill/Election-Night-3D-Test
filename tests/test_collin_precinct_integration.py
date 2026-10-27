import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from normalize_collin_precinct_geojson import convert
from check_tx_precinct_geometry import check_join

def polygon():
 return {"type":"Polygon","coordinates":[[[-97,33],[-96,33],[-96,34],[-97,33]]]}

def geo(ids):
 return convert({"type":"FeatureCollection","features":[
  {"type":"Feature","properties":{"PRECINCT":n},"geometry":polygon()} for n in ids]})

def data(ids):
 rows=[{"county_fips":"48085","area_id":str(n),"ballots_total":10,
        "prior_dem_primary":None,"prior_rep_primary":None} for n in ids]
 return {"schema":"electionhq-local-returns-v1","state":"TX","publication_approved":False,
         "area_type":"voting_precinct","metric_kind":"ballots_cast",
         "source_url":"https://example.org/collin-aggregate",
         "geometry_source_url":"https://example.org/collin-2026-boundaries",
         "geometry_vintage":"2026 general election (fixture only)",
         "file_as_of":"2026-10-27","reported_area_total":10*len(ids),
         "coverage_complete":None,"areas":rows}

class CollinEndToEndTests(unittest.TestCase):
 def test_normalization_and_join(self):
  result=check_join(data([101,102]),geo(["00101",102]),"county_fips","area_id")
  self.assertEqual(result["matched"],2)
  self.assertEqual(result["unmatched_data"],[])
  self.assertFalse(result["publication_approved"])
 def test_missing_precinct_detected(self):
  result=check_join(data([101,102]),geo([101]),"county_fips","area_id")
  self.assertEqual(result["unmatched_data"],[["48085","102"]])
 def test_extra_geometry_reported(self):
  result=check_join(data([101]),geo([101,102]),"county_fips","area_id")
  self.assertEqual(result["unmatched_geometry"],[["48085","102"]])
if __name__=="__main__":unittest.main()
