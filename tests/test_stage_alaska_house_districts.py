"""Regression checks for Alaska's 40 geographic districts plus special District 99."""
import csv
import tempfile
import unittest
from pathlib import Path
from scripts.stage_alaska_house_districts import parse

SOURCE = "https://elections.alaska.gov/wp-content/uploads/2026/10/Combined-Ballot-Report-10_26_2026-10_31_33-AM.html"
FIXTURE = Path("data/staging/alaska-house-districts-2026-10-26.csv")

class AlaskaDistrictTests(unittest.TestCase):
    def test_official_snapshot_reconciles(self):
        result = parse(FIXTURE, SOURCE)
        self.assertEqual(result["reported_districts"], 40)
        self.assertEqual(result["special_reporting_districts"], [99])
        self.assertEqual(result["geographic_received_ballots"], 46287)
        self.assertEqual(result["nongeographic_received_ballots"], 116)
        self.assertEqual(result["total_received_ballots"], 46403)
        self.assertEqual(result["absentee_received"], 15867)
        self.assertEqual(result["early_vote_received"], 30536)
        self.assertFalse(result["publication_approved"])

    def test_corrupt_district_total_rejected(self):
        with FIXTURE.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["received"] = str(int(rows[0]["received"]) + 1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "do not reconcile"):
                parse(path, SOURCE)

    def test_missing_special_district_rejected(self):
        with FIXTURE.open(newline="", encoding="utf-8") as handle:
            rows = [r for r in csv.DictReader(handle) if r["district"] != "99"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "40 geographic districts"):
                parse(path, SOURCE)

if __name__ == "__main__":
    unittest.main()
