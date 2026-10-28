"""Regression tests for provider retrieval evidence and missing source dates."""
import datetime as dt
import io
import unittest
from unittest.mock import patch
from scripts import stage_public_county_tables_ten_states as source

class FakeResponse:
    def __init__(self, html):
        self.html = html.encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return self.html[:limit]

class RetrievalEvidenceTests(unittest.TestCase):
    def test_successful_county_table_has_actual_check_timestamp(self):
        html = "<h2>By county</h2><div>Maricopa</div><div>1,234</div><div>By day</div>"
        with patch.object(source.urllib.request, "urlopen", return_value=FakeResponse(html)):
            result = source.retrieve("AZ", "returned")
        self.assertEqual(result["status"], "county_table_found")
        self.assertEqual(result["counties"], [{"name": "Maricopa", "total": 1234}])
        checked = dt.datetime.fromisoformat(result["provider_checked_at"])
        self.assertEqual(checked.utcoffset(), dt.timedelta(0))
        self.assertLess(abs((dt.datetime.now(dt.timezone.utc)-checked).total_seconds()), 30)
        self.assertNotIn("file_as_of", result)

    def test_successful_request_without_county_table_records_check(self):
        with patch.object(source.urllib.request, "urlopen", return_value=FakeResponse("<p>No county data</p>")):
            result = source.retrieve("KS", "returned")
        self.assertEqual(result["status"], "county_table_absent")
        self.assertIsNotNone(dt.datetime.fromisoformat(result["provider_checked_at"]).tzinfo)
        self.assertNotIn("file_as_of", result)

    def test_failed_request_does_not_generate_successful_check_timestamp(self):
        with patch.object(source.urllib.request, "urlopen", side_effect=OSError("unavailable")):
            with self.assertRaises(OSError):
                source.retrieve("NV", "returned")

if __name__ == "__main__":
    unittest.main()
