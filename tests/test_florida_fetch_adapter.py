import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.fetch_florida_aggregates import fetch_official

class FakeResponse:
    def __init__(self, url, data):
        self.url, self.data = url, data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def geturl(self):
        return self.url
    def read(self, limit):
        return self.data[:limit]

class FloridaFetchTests(unittest.TestCase):
    def test_rejects_nonofficial_hosts(self):
        with tempfile.TemporaryDirectory() as directory:
            for url in ("https://example.com/file.txt",
                        "http://countyfilesvbm-ev.floridados.gov/file.txt",
                        "https://countyfilesvbm-ev.floridados.gov.evil.test/file.txt"):
                with self.assertRaises(ValueError):
                    fetch_official(url, Path(directory) / "test.txt")

    def test_rejects_html_and_wrong_format(self):
        url = "https://countyfilesvbm-ev.floridados.gov/example"
        with tempfile.TemporaryDirectory() as directory:
            with patch("scripts.fetch_florida_aggregates.urllib.request.urlopen",
                       return_value=FakeResponse(url, b"<html>no data</html>")):
                with self.assertRaises(ValueError):
                    fetch_official(url, Path(directory) / "test.txt")

    def test_rejects_cross_host_redirect(self):
        url = "https://countyfilesvbm-ev.floridados.gov/example"
        with tempfile.TemporaryDirectory() as directory:
            with patch("scripts.fetch_florida_aggregates.urllib.request.urlopen",
                       return_value=FakeResponse("https://other.example/file", b"ElectionNumber\t")):
                with self.assertRaises(ValueError):
                    fetch_official(url, Path(directory) / "test.txt")

if __name__ == "__main__":
    unittest.main()
