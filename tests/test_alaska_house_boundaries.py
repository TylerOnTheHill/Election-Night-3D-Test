import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("alaska_boundaries", Path(__file__).resolve().parents[1] / "scripts" / "fetch_alaska_house_boundaries.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def fixture():
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"HouseDistrict": n},
         "geometry": {"type": "Polygon", "coordinates": [[[-150, 60], [-149, 60], [-149, 61], [-150, 60]]]}}
        for n in range(1, 41)]}

class AlaskaHouseBoundariesTest(unittest.TestCase):
    def test_exactly_40_districts(self):
        self.assertEqual(len(module.validate(fixture())["features"]), 40)

    def test_missing_district_rejected(self):
        data = fixture()
        data["features"].pop()
        with self.assertRaises(ValueError):
            module.validate(data)

    def test_duplicate_district_rejected(self):
        data = fixture()
        data["features"][39]["properties"]["HouseDistrict"] = 1
        with self.assertRaises(ValueError):
            module.validate(data)

    def test_missing_polygon_rejected(self):
        data = fixture()
        data["features"][0]["geometry"] = None
        with self.assertRaises(ValueError):
            module.validate(data)

if __name__ == "__main__":
    unittest.main()
