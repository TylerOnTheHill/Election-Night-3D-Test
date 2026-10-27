import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from normalize_collin_precinct_geojson import convert

def fixture(ids):
    return {"type":"FeatureCollection","features":[
        {"type":"Feature","properties":{"PRECINCT":p},
         "geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}}
        for p in ids]}

class CollinGeoTests(unittest.TestCase):
    def test_normalizes_integer_precinct(self):
        data=convert(fixture([101, 102]))
        self.assertEqual(data["features"][0]["properties"],{"county_fips":"48085","area_id":"101"})
        self.assertEqual(len(data["features"]),2)
    def test_strips_leading_zeroes_for_canonical_id(self):
        data=convert(fixture(["00101"]))
        self.assertEqual(data["features"][0]["properties"]["area_id"],"101")
    def test_rejects_duplicate_after_normalization(self):
        with self.assertRaises(ValueError):convert(fixture([101,"00101"]))
    def test_rejects_missing_precinct(self):
        with self.assertRaises(ValueError):convert(fixture([None]))
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):convert(fixture([]))
    def test_rejects_bad_geometry(self):
        d=fixture([101]);d["features"][0]["geometry"]["type"]="Point"
        with self.assertRaises(ValueError):convert(d)
if __name__=="__main__":unittest.main()
