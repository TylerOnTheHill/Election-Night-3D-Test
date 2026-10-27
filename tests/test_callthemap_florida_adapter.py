import copy
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reconcile_callthemap_florida import validate

class CallTheMapFloridaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.official = json.loads((ROOT / "data/early-vote/FL.json").read_text())

    def feed(self):
        rows = []
        for county in self.official["counties"]:
            early = county["voted_early"]
            mail = county["voted_mail"]
            parties = {p: early["registration"][p] + mail["registration"][p]
                       for p in ("democrat", "republican", "other", "no_party_affiliation")}
            rows.append({"county": county["county"], "state": "FL",
                         "total": sum(parties.values()), "dem": parties["democrat"],
                         "rep": parties["republican"],
                         "unaffiliated_other": parties["other"] + parties["no_party_affiliation"],
                         "file_as_of": "2026-10-26T12:06:00Z",
                         "source_url": "https://example.gov/fl", "credit": "CTM"})
        return {"schema": "ctm-early-vote-download-v1", "state": "FL",
                "credit": "Call the Map", "license": "Free with credit",
                "checked_at": "2026-10-27T01:35:36Z",
                "summary": {"total": sum(r["total"] for r in rows) + 100},
                "counties": rows}

    def test_preserves_statewide_only_difference(self):
        result = validate(self.feed(), self.official)
        self.assertEqual(result["counties_count"], 67)
        self.assertEqual(result["unallocated_statewide_minus_counties"], 100)
        self.assertEqual(sum(x["difference"] for x in result["county_comparison"]), 0)

    def test_rejects_missing_county(self):
        f = self.feed()
        f["counties"].pop()
        with self.assertRaises(ValueError): validate(f, self.official)

    def test_rejects_bad_party_sum(self):
        f = self.feed()
        f["counties"][0]["dem"] += 1
        with self.assertRaises(ValueError): validate(f, self.official)

    def test_rejects_duplicate_county(self):
        f = self.feed()
        f["counties"][1]["county"] = f["counties"][0]["county"]
        with self.assertRaises(ValueError): validate(f, self.official)

if __name__ == "__main__":
    unittest.main()
