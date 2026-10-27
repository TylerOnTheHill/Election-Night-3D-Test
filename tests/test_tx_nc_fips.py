import sys
import unittest
import io
import zipfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_tx_nc_fips import canonical, crosswalk, census_url, fetch_gazetteer

class CensusCrosswalkTests(unittest.TestCase):
    def test_gazetteer_zip_tsv_parsing(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("2020_Gazetteer_counties_national.txt",
                       "USPS\tGEOID\tNAME\nTX\t48453\tTravis County\nNC\t37183\tWake County\n")
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return buffer.getvalue()
        with patch("verify_tx_nc_fips.urllib.request.urlopen", return_value=Response()):
            self.assertEqual(fetch_gazetteer("48"),
                             [["NAME", "state", "county"], ["Travis County", "48", "453"]])
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
    def test_gazetteer_crosswalk_rejects_missing_county(self):
        census = [["NAME", "state", "county"], ["Travis County", "48", "453"]]
        staged = {"state": "TX", "status": "staging_only_not_approved_for_publication",
                  "counties": [{"county": "Travis", "total": 12}]}
        with self.assertRaisesRegex(ValueError, "geographic count unexpected"):
            crosswalk("TX", census, staged, "2020 Census Gazetteer", "https://www2.census.gov/")
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
