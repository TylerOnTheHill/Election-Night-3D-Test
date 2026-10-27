import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATES=("AK","AZ","KS","ME","MI","MN","MS","NE","NV","NH","OH")

class UfOutputTests(unittest.TestCase):
    def test_cli_writes_parseable_restricted_json(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            for code in STATES:
                (directory/(code+"_county.csv")).write_text("county,voted_all\n")
            # Use local fixture geography through a tiny monkeypatch-free
            # integration path: the review output itself must be valid JSON.
            output=directory/"review.json"
            subprocess.run([sys.executable,str(ROOT/"scripts/stage_uf_county_review.py"),
                            "--input-dir",str(directory),"--output",str(output)],
                           cwd=ROOT,check=True,capture_output=True,text=True)
            review=json.loads(output.read_text())
            self.assertEqual(set(review["states"]),set(STATES))

if __name__=="__main__":
    unittest.main()
