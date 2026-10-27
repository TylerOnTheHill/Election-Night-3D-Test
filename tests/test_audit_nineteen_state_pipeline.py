import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_nineteen_state_pipeline import audit
from audit_national_early_vote import WATCH
from audit_remaining_watchlist_county_sources import STATES as MISSING

def fixtures():
    readiness={"schema":"electionhq-watchlist-readiness-v1","publication_approved":False,"states":[
        {"state":code,"county_staged":code not in MISSING,
         "county_ballots":None if code in MISSING else 100,
         "county_reported":None if code in MISSING else 1,
         "county_publication_approved":False} for code in WATCH]}
    discovery={"schema":"electionhq-remaining-watchlist-source-discovery-v1",
               "publication_approved":False,
               "states":{code:{"publication_approved":False} for code in MISSING}}
    return readiness,discovery

class UnifiedPipelineTests(unittest.TestCase):
    def test_all_nineteen_represented(self):
        r,d=fixtures()
        result=audit(r,d)
        self.assertEqual(result["states_checked"],19)
        self.assertEqual(result["source_discovery_count"],11)
        self.assertFalse(result["county_values_imputed"])
    def test_reject_fabricated_missing_county(self):
        r,d=fixtures()
        next(x for x in r["states"] if x["state"]=="NH")["county_ballots"]=0
        with self.assertRaisesRegex(ValueError,"fabricated"):
            audit(r,d)
    def test_reject_missing_state(self):
        r,d=fixtures()
        r["states"].pop()
        with self.assertRaisesRegex(ValueError,"19"):
            audit(r,d)
    def test_reject_unstaged_state_with_county_subtotal(self):
        r,d=fixtures()
        next(x for x in r["states"] if x["state"]=="TX")["county_staged"]=False
        with self.assertRaisesRegex(ValueError,"Coverage gap"):
            audit(r,d)

    def test_reject_malformed_staged_ballots(self):
        for invalid in (None, -1, True, "100"):
            with self.subTest(invalid=invalid):
                r,d=fixtures()
                next(x for x in r["states"] if x["state"]=="TX")["county_ballots"]=invalid
                with self.assertRaisesRegex(ValueError,"subtotal"):
                    audit(r,d)

    def test_reject_malformed_reported_counties(self):
        for invalid in (None, 0, -1, True, "1"):
            with self.subTest(invalid=invalid):
                r,d=fixtures()
                next(x for x in r["states"] if x["state"]=="TX")["county_reported"]=invalid
                with self.assertRaisesRegex(ValueError,"reported county"):
                    audit(r,d)

    def test_reject_unapproved_state_promoted(self):
        r,d=fixtures()
        r["states"][0]["county_publication_approved"]=True
        with self.assertRaisesRegex(ValueError,"approval"):
            audit(r,d)
if __name__=="__main__":
    unittest.main()
