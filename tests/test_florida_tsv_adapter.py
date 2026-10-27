import tempfile
import unittest
from pathlib import Path
from scripts.import_florida_tsv import import_files

HEADER = "ElectionNumber\tElectionDate\tElectionName\tCountyName\tStatType\tTotalRep\tTotalDem\tTotalOth\tTotalNpa\tGrandTotal\tCompileDate\n"
STAMP = "10/26/2026  8:06AM"
LABELS = ("Voted Early", "Voted Vote-by-Mail", "Vote-by-Mail Provided (Not Yet Returned)")

def fixture(path, label, count=67, mismatch=False):
    rows = [HEADER]
    def row(name, total):
        return f"49894\t11/03/2026\t2026 General\t{name}\t{label}\t{total}\t0\t0\t0\t{total}\t{STAMP}\n"
    rows.append(row("State Totals", count + (1 if mismatch else 0)))
    for n in range(count):
        rows.append(row(f"County {n:02}", 1))
    path.write_text("".join(rows))

class FloridaTSVTests(unittest.TestCase):
    def test_full_snapshot_and_return_rate(self):
        with tempfile.TemporaryDirectory() as d:
            files = [Path(d) / f"{i}.txt" for i in range(3)]
            for path, label in zip(files, LABELS):
                fixture(path, label)
            result = import_files(*files)
            self.assertEqual(result["coverage"]["counties_reported"], 67)
            self.assertEqual(result["statewide"]["mail_return_rate"], 0.5)
            self.assertEqual(result["counties"][0]["mail_return_rate"], 0.5)

    def test_rejects_incomplete_counties(self):
        with tempfile.TemporaryDirectory() as d:
            files = [Path(d) / f"{i}.txt" for i in range(3)]
            for path, label in zip(files, LABELS):
                fixture(path, label, count=66)
            with self.assertRaises(ValueError):
                import_files(*files)

    def test_rejects_statewide_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            files = [Path(d) / f"{i}.txt" for i in range(3)]
            for path, label in zip(files, LABELS):
                fixture(path, label, mismatch=(label == "Voted Early"))
            with self.assertRaises(ValueError):
                import_files(*files)

if __name__ == "__main__":
    unittest.main()
