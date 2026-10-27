import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_florida_county_candidate import stage, from_official_tsv_snapshot

def fixture():
    census=[["NAME","state","county"]]
    for i in range(1,68):
        census.append([f"County{i} County","12",f"{i:03d}"])
    normalized={"schema":"electionhq-county-early-vote-v1","state_fips":"12",
        "source_url":"https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats",
        "reported_through":"2026-10-27","records":[]}
    for name in ["County1","County2"]:
        for category,total in [("voted_mail",10),("voted_early",20)]:
            normalized["records"].append({"county":name,"category":category,"total":total,
                "registration":{"republican":total,"democrat":0,"other":0,"no_party_affiliation":0}})
    return normalized,census

class FloridaCountyStagingTests(unittest.TestCase):
    def test_existing_official_tsv_snapshot_adapter(self):
        data,census=fixture()
        counties=[]
        for county in ("County1","County2"):
            entries={r["category"]:{"total":r["total"],"registration":r["registration"]}
                     for r in data["records"] if r["county"]==county}
            counties.append({"county":county,**entries})
        snapshot={"schema":"electionhq-florida-county-aggregate-v1",
                  "election_id":"49894","state_fips":"12",
                  "source_url":data["source_url"],
                  "compiled_at_local":"2026-10-27T08:00:00","counties":counties}
        converted=from_official_tsv_snapshot(snapshot)
        candidate=stage(converted,census)
        self.assertEqual(candidate["states"]["FL"]["total"],60)
        self.assertEqual(candidate["states"]["FL"]["county_count"],2)
        self.assertFalse(candidate["publication_approved"])

    def test_partial_counties_and_no_zero_fill(self):
        data,census=fixture()
        candidate=stage(data,census)
        self.assertFalse(candidate["publication_approved"])
        self.assertTrue(candidate["review_required"])
        fl=candidate["states"]["FL"]
        self.assertEqual(fl["county_count"],2)
        self.assertEqual(fl["geographic_count"],67)
        self.assertEqual(fl["reporting_label"],"Partially reported")
        self.assertEqual(fl["total"],60)
        self.assertEqual([r["fips"] for r in fl["counties"]],["12001","12002"])
        self.assertEqual(fl["counties"][0]["mail"],10)
        self.assertEqual(fl["counties"][0]["in_person"],20)

    def test_incomplete_method_does_not_become_complete_county(self):
        data,census=fixture()
        data["records"].pop()
        candidate=stage(data,census)
        self.assertEqual(candidate["states"]["FL"]["county_count"],1)
        self.assertEqual(candidate["states"]["FL"]["total"],30)

    def test_invalid_fips_crosswalk_rejected(self):
        data,census=fixture()
        census.pop()
        with self.assertRaises(ValueError):
            stage(data,census)

    def test_duplicate_category_rejected(self):
        data,census=fixture()
        data["records"].append(dict(data["records"][0]))
        with self.assertRaises(ValueError):
            stage(data,census)

    def test_reconciliation_rejected(self):
        data,census=fixture()
        data["records"][0]["total"]=999
        with self.assertRaises(ValueError):
            stage(data,census)

if __name__=="__main__":
    unittest.main()
