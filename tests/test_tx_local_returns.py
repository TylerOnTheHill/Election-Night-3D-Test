import copy
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_tx_local_returns import validate

BASE = {
 "schema": "electionhq-local-returns-v1", "state": "TX",
 "publication_approved": False, "area_type": "voting_precinct",
 "metric_kind": "ballots_cast", "source_url": "https://example.org/roster",
 "geometry_source_url": "https://data.capitol.texas.gov/dataset/precincts",
 "geometry_vintage": "2026 primary (not confirmed for general)",
 "file_as_of": "2026-10-27", "reported_area_total": 7,
 "coverage_complete": None,
 "areas": [{"county_fips": "48201", "area_id": "0001", "ballots_total": 7,
            "prior_dem_primary": None, "prior_rep_primary": None}]
}
class LocalReturnTests(unittest.TestCase):
 def test_valid_is_staging_only(self):
  d = validate(copy.deepcopy(BASE))
  self.assertEqual(d["reported_area_count"], 1)
  self.assertIn("staging_only", d["status"])
 def test_reject_duplicate_precinct(self):
  d=copy.deepcopy(BASE);d["areas"].append(copy.deepcopy(d["areas"][0]));d["reported_area_total"]=14
  with self.assertRaises(ValueError):validate(d)
 def test_reject_mismatched_total(self):
  d=copy.deepcopy(BASE);d["reported_area_total"]=8
  with self.assertRaises(ValueError):validate(d)
 def test_reject_published(self):
  d=copy.deepcopy(BASE);d["publication_approved"]=True
  with self.assertRaises(ValueError):validate(d)
 def test_reject_unverified_coverage_claim(self):
  d=copy.deepcopy(BASE);d["coverage_complete"]=True
  with self.assertRaises(ValueError):validate(d)
 def test_reject_candidate_votes(self):
  d=copy.deepcopy(BASE);d["areas"][0]["candidate_dem_votes"]=3
  with self.assertRaises(ValueError):validate(d)
 def test_reject_non_texas_fips(self):
  d=copy.deepcopy(BASE);d["areas"][0]["county_fips"]="37183"
  with self.assertRaises(ValueError):validate(d)
if __name__ == "__main__":unittest.main()
