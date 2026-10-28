import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from capture_ci_failure import summarize

class CaptureCiFailureTests(unittest.TestCase):
    def test_detects_failure_before_job_has_finished(self):
        jobs = [{"name": "review", "conclusion": None, "steps": [
            {"name": "checkout", "conclusion": "success", "number": 1},
            {"name": "validate", "conclusion": "failure", "number": 2}]}]
        result = summarize(jobs)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["failed_steps"][0]["name"], "validate")

    def test_running_job_without_failure_is_not_misreported(self):
        self.assertEqual(summarize([{"name": "review", "conclusion": None,
                                     "steps": [{"name": "staging", "conclusion": None}]}]), [])

    def test_ignores_successful_jobs(self):
        self.assertEqual(summarize([{"name": "passed", "conclusion": "success",
                                     "steps": [{"name": "ok", "conclusion": "success"}]}]), [])

    def test_failed_job_without_step_still_recorded(self):
        result = summarize([{"name": "failed", "conclusion": "failure", "steps": []}])
        self.assertEqual(result[0]["failed_steps"], [])

if __name__ == "__main__":
    unittest.main()
