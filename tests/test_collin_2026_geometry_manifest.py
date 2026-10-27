import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from check_collin_2026_geometry_manifest import assess

BASE={"county_fips":"48085","election_date":"2026-11-03",
"geometry_source_url":"https://example.org/official-2026.geojson",
"boundary_approval_url":"https://example.org/2026-notice",
"geometry_effective_date":"2026-01-01","geometry_vintage":"2026 general verified",
"downloaded_at":"2026-10-27",
"county_confirmed_for_2026_general":True,
"precinct_ids_reconciled":True,"full_geometry_coverage_verified":True,
"source_use_permitted":True}
class ManifestTests(unittest.TestCase):
 def test_eligible_is_still_not_publication(self):
  result=assess(BASE)
  self.assertTrue(result["eligible_for_staging_join"])
  self.assertFalse(result["publication_approved"])
 def test_missing_confirmation_blocks(self):
  d=copy.deepcopy(BASE);d["county_confirmed_for_2026_general"]=False
  self.assertFalse(assess(d)["eligible_for_staging_join"])
 def test_missing_id_join_blocks(self):
  d=copy.deepcopy(BASE);d["precinct_ids_reconciled"]=False
  self.assertFalse(assess(d)["eligible_for_staging_join"])
 def test_reject_wrong_election(self):
  d=copy.deepcopy(BASE);d["election_date"]="2026-03-03"
  with self.assertRaises(ValueError):assess(d)
 def test_reject_missing_source(self):
  d=copy.deepcopy(BASE);d.pop("boundary_approval_url")
  with self.assertRaises(ValueError):assess(d)
if __name__=="__main__":unittest.main()
