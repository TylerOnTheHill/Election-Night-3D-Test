"""Regression tests for source-aware nationwide refresh safeguards."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refresh_early_vote import validate_snapshot, refresh


def snapshot(cutoff="2026-10-26", checked="2026-10-27T05:00:00Z"):
    states = [{"state": f"{n:02d}", "state_name": f"State {n}", "total": 100 + n,
               "mail": None, "in_person": None, "counts_through": cutoff,
               "source_url": "https://example.org/source", "credit": "Example"}
              for n in range(30)]
    return {"schema": "ctm-early-vote-download-v1", "states": states,
            "national": {"total": sum(x["total"] for x in states), "states_counted": len(states)},
            "credit": "Example", "license": "Example", "checked_at": checked}


class FakeResponse:
    def __init__(self, doc):
        self.payload = json.dumps(doc).encode()
    def __enter__(self):
        import io
        self.stream = io.BytesIO(self.payload)
        return self.stream
    def __exit__(self, *args):
        self.stream.close()


class NationalRefreshTests(unittest.TestCase):
    def test_complete_snapshot_accepted(self):
        self.assertEqual(validate_snapshot(snapshot()), 30)

    def test_newer_state_cutoff_accepted(self):
        old = snapshot()
        new = snapshot("2026-10-27", "2026-10-27T06:00:00Z")
        self.assertEqual(validate_snapshot(new, old), 30)

    def test_same_cutoff_correction_is_not_double_counted(self):
        old = snapshot()
        new = snapshot(checked="2026-10-27T06:00:00Z")
        new["states"][0]["total"] += 5
        new["national"]["total"] += 5
        self.assertEqual(validate_snapshot(new, old), 30)

    def test_newer_download_with_stale_state_is_rejected(self):
        old = snapshot()
        new = snapshot(checked="2026-10-27T06:00:00Z")
        new["states"][0]["counts_through"] = "2026-10-25"
        with self.assertRaisesRegex(ValueError, "stale state"):
            validate_snapshot(new, old)

    def test_missing_reporting_state_is_rejected(self):
        old = snapshot()
        new = snapshot(checked="2026-10-27T06:00:00Z")
        new["states"].pop()
        new["national"]["states_counted"] -= 1
        new["national"]["total"] = sum(s["total"] for s in new["states"])
        with self.assertRaisesRegex(ValueError, "Incomplete state list|disappearing"):
            validate_snapshot(new, old)

    def test_rejected_refresh_preserves_existing_file(self):
        old = snapshot()
        new = snapshot(checked="2026-10-27T06:00:00Z")
        new["states"][0]["counts_through"] = "2026-10-25"
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "US.json"
            dest.write_text(json.dumps(old))
            before = dest.read_bytes()
            with patch("refresh_early_vote.urllib.request.urlopen", return_value=FakeResponse(new)):
                with self.assertRaisesRegex(ValueError, "stale state"):
                    refresh("https://example.org/US.json", dest)
            self.assertEqual(dest.read_bytes(), before)

    def test_successful_refresh_replaces_snapshot_not_adds(self):
        old = snapshot()
        new = snapshot("2026-10-27", "2026-10-27T06:00:00Z")
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "US.json"
            dest.write_text(json.dumps(old))
            with patch("refresh_early_vote.urllib.request.urlopen", return_value=FakeResponse(new)):
                refresh("https://example.org/US.json", dest)
            saved = json.loads(dest.read_text())
            self.assertEqual(saved["national"]["total"], new["national"]["total"])
            self.assertEqual(saved["states"], new["states"])


if __name__ == "__main__":
    unittest.main()
