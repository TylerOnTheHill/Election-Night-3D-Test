import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from stage_maine_aggregated_counties import aggregate

class MaineAggregationTests(unittest.TestCase):
    def test_2026_accepted_by_county_not_requests_or_other_elections(self):
        units=[{"unit_id":"1","county":"Cumberland"},{"unit_id":"2","county":"York"}]
        ballots=[
            {"unit_id":"1","election_date":"2026-11-03","accepted":"12","returned":"15","requested":"30"},
            {"unit_id":"1","election_date":"2026-11-03","accepted":"3","returned":"4","requested":"9"},
            {"unit_id":"2","election_date":"2026-11-03","accepted":"7","returned":"8","requested":"10"},
            {"unit_id":"1","election_date":"2024-11-05","accepted":"100","returned":"100","requested":"100"}]
        result=aggregate(ballots,units)
        self.assertEqual(result["total"],22)
        self.assertEqual(result["counties"],{"Cumberland":15,"York":7})
        self.assertEqual(result["metric"],"accepted")
    def test_reachable_dataset_without_2026_rows_is_not_an_outage(self):
        result=aggregate([{"unit_id":"1","election_date":"2024-11-05","returned":"20"}],
                         [{"unit_id":"1","county":"York"}])
        self.assertEqual(result["status"],"no_2026_general_election_rows")
        self.assertIsNone(result["county_ballots"])
        self.assertEqual(result["reporting_label"],"Not reported")
    def test_missing_unit_fails_closed(self):
        with self.assertRaises(ValueError):
            aggregate([{"unit_id":"3","election_date":"2026-11-03","returned":"4"}],
                      [{"unit_id":"1","county":"York"}])
if __name__=="__main__":
    unittest.main()
