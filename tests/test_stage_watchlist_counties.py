import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_watchlist_counties import stage,build,STATES

def fixture(code):
    prefix,expected=STATES[code]
    census=[["NAME","state","county"]]+[[f"County{i} County",prefix,f"{i:03d}"] for i in range(1,expected+1)]
    provider={"schema":"ctm-early-vote-download-v1","state":code,
        "credit":"Fixture","license":"Fixture",
        "summary":{"total":1000,"file_as_of":"2026-10-27"},
        "counties":[{"county":"County1","state":code,"total":30,
            "source_url":"https://example.org/official","credit":"Fixture","file_as_of":"2026-10-27"},
            {"county":"County2","state":code,"total":None,
            "source_url":"https://example.org/official","credit":"Fixture"}]}
    return provider,census

class WatchlistStagingTests(unittest.TestCase):
    def test_all_four_states_partial_and_unknown_not_zero(self):
        payloads,census={},{}
        for code in STATES:
            payloads[code],census[code]=fixture(code)
        candidate=build(payloads,census)
        self.assertFalse(candidate["publication_approved"])
        self.assertTrue(candidate["review_required"])
        self.assertEqual(set(candidate["states"]),set(STATES))
        for code in STATES:
            state=candidate["states"][code]
            self.assertEqual(state["county_count"],1)
            self.assertEqual(state["total"],30)
            self.assertEqual(state["reporting_label"],"Partially reported")
            self.assertEqual(state["counties"][0]["fips"],STATES[code][0]+"001")

    def test_no_observations_does_not_fabricate_state(self):
        p,c=fixture("IA")
        p["counties"][0]["total"]=None
        self.assertIsNone(stage("IA",p,c))

    def test_duplicate_reported_county_rejected(self):
        p,c=fixture("WI")
        p["counties"].append(dict(p["counties"][0]))
        with self.assertRaises(ValueError):
            stage("WI",p,c)

    def test_missing_provenance_rejected(self):
        p,c=fixture("SC")
        p["counties"][0]["source_url"]=""
        with self.assertRaises(ValueError):
            stage("SC",p,c)

    def test_bad_geography_rejected(self):
        p,c=fixture("VA")
        c.pop()
        with self.assertRaises(ValueError):
            stage("VA",p,c)

if __name__=="__main__":
    unittest.main()
