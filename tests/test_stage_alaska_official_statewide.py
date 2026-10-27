import sys
import unittest
import tempfile
import json
from unittest.mock import patch
from urllib.error import URLError
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_alaska_official_statewide import parse, main

class AlaskaOfficialTests(unittest.TestCase):
    def test_2026_general_received_not_issued_or_primary(self):
        html="""<h2>2026 General Election – November 3, 2026</h2>
        <div>Total Ballots Issued: 80,717</div>
        <div>Total Ballots Received: 46,403</div>
        <div>Table last updated October 26, 2026 at 1:33 pm.</div>
        <h2>2026 Primary Election – August 18, 2026</h2>
        <div>Total Ballots Issued: 59,063</div>
        <div>Total Ballots Received: 52,873</div>"""
        result=parse(html)
        self.assertEqual(result["received_ballots"],46403)
        self.assertEqual(result["source_cutoff"],"October 26, 2026 at 1:33 pm")
        self.assertIsNone(result["county_equivalent_observations"])
    def test_unreachable_source_writes_explicit_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"alaska.json"
            with patch.object(sys,"argv",["stage_alaska_official_statewide.py","--output",str(output)]):
                with patch("stage_alaska_official_statewide.urllib.request.urlopen",side_effect=URLError("certificate error")):
                    main()
            record=json.loads(output.read_text())
            self.assertEqual(record["status"],"source_unavailable")
            self.assertFalse(record["publication_approved"])
    def test_missing_cutoff_fails(self):
        with self.assertRaises(ValueError):
            parse("2026 General Election Total Ballots Issued: 20 Total Ballots Received: 10 2026 Primary Election")
if __name__=="__main__":
    unittest.main()
