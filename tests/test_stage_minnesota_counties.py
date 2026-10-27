import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_minnesota_counties import parse
from validate_county_publication_candidate import validate

class MinnesotaTests(unittest.TestCase):
    def test_partial_county_observations_preserved(self):
        census=[["NAME","state","county"]]+[[f"County {i} County, Minnesota","27",f"{i:03}"] for i in range(1,88)]
        html="""<p>Absentee Counts by County as of October 23, 2026</p>
        <table><tr><th>County</th><th>Applications</th><th>Accepted ballots - by mail</th><th>Accepted ballots - in person</th></tr>
        <tr><td>County 1</td><td>500</td><td>12</td><td>30</td></tr>
        <tr><td>County 2</td><td>400</td><td>8</td><td>20</td></tr></table>"""
        candidate=parse(html,census)
        state=candidate["states"]["MN"]
        self.assertEqual(state["total"],70)
        self.assertEqual(state["county_count"],2)
        self.assertEqual(state["reporting_label"],"Partially reported")
        self.assertIsNone(state["provider_statewide_total"])
        self.assertEqual(validate(candidate)["MN"]["reported_counties"],2)
    def test_duplicate_county_rejected(self):
        census=[["NAME","state","county"]]+[[f"County {i} County, Minnesota","27",f"{i:03}"] for i in range(1,88)]
        html="""Absentee Counts by County as of October 23, 2026
        <table><tr><th>County</th><th>Applications</th><th>Accepted ballots - by mail</th><th>Accepted ballots - in person</th></tr>
        <tr><td>County 1</td><td>2</td><td>1</td><td>1</td></tr>
        <tr><td>County 1</td><td>2</td><td>1</td><td>1</td></tr></table>"""
        with self.assertRaisesRegex(ValueError,"Duplicate"):parse(html,census)
if __name__=="__main__":unittest.main()
