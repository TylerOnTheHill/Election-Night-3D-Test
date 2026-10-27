import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_tx_nc_fips import canonical, crosswalk, census_url

class CensusCrosswalkTests(unittest.TestCase):
    def test_census_query_escapes_special_characters(self):
        from urllib.parse import parse_qs, urlsplit
        query = parse_qs(urlsplit(census_url('48')).query)
        self.assertEqual(query['get'], ['NAME'])
        self.assertEqual(query['for'], ['county:*'])
        self.assertEqual(query['in'], ['state:48'])
        self.assertIn('%2A', census_url('48'))
    def test_normalization(self):
        self.assertEqual(canonical("DeWitt County"), canonical("De Witt"))
        self.assertEqual(canonical("McLennan County"), canonical("McLennan"))
    def test_rejects_incomplete_geography(self):
        staged={"state":"TX","status":"staging_only_not_approved_for_publication","counties":[]}
        with self.assertRaises(ValueError):
            crosswalk("TX",[["NAME","state","county"],["Travis County, Texas","48","453"]],staged)
    def test_rejects_wrong_state(self):
        staged={"state":"TX","status":"staging_only_not_approved_for_publication","counties":[]}
        with self.assertRaises(ValueError):
            crosswalk("TX",[["NAME","state","county"],["Travis County, Texas","37","453"]],staged)
    def test_rejects_unexpected_schema(self):
        with self.assertRaises(ValueError):
            crosswalk("NC",[["bad"]],{"state":"NC","status":"staging_only_not_approved_for_publication","counties":[]})

if __name__ == "__main__":
    unittest.main()
