import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from stage_michigan_counties import parse
from validate_county_publication_candidate import validate

class MichiganCountyTests(unittest.TestCase):
    def test_numeric_counts_and_full_geography_without_statewide_reconciliation(self):
        geo = {"features": [{"id": f"26{i:03d}", "properties": {"NAME": f"County{i}"}} for i in range(1, 84)]}
        csv = "County,Recorded Participation,Absentee Returned,Early In Person\n"
        csv += "".join(f"County{i},1517,1000,517\n" for i in range(1, 84))
        result = parse(csv, geo)
        state = result["states"]["MI"]
        self.assertEqual(state["county_count"], 83)
        self.assertEqual(state["total"], 83 * 1517)
        self.assertEqual(state["reporting_label"], "Fully reported")
        self.assertFalse(state["statewide_reconciled"])
        self.assertEqual(validate(result)["MI"]["reported_ballots"], 83 * 1517)

    def test_rejects_suppressed_counts(self):
        geo = {"features": [{"id": f"26{i:03d}", "properties": {"NAME": f"County{i}"}} for i in range(1, 84)]}
        csv = "County,Recorded Participation,Absentee Returned,Early In Person\nCounty1,suppressed,1,2\n"
        with self.assertRaisesRegex(ValueError, "Suppressed"):
            parse(csv, geo)

if __name__ == "__main__":
    unittest.main()
