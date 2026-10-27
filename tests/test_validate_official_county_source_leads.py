import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from validate_official_county_source_leads import validate

class LeadRegistryTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads(Path("data/sources/remaining-watchlist-official-source-leads.json").read_text())
    def test_current_registry(self):
        result=validate(self.doc)
        self.assertIn("OH",result["states"])
        self.assertFalse(result["approved"])
    def test_cannot_mark_verified_without_ingestion(self):
        doc=copy.deepcopy(self.doc)
        doc["leads"][0]["county_ballot_values_verified"]=True
        with self.assertRaisesRegex(ValueError,"verified ingestible"):
            validate(doc)
    def test_duplicate_source_rejected(self):
        doc=copy.deepcopy(self.doc)
        doc["leads"].append(copy.deepcopy(doc["leads"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            validate(doc)
    def test_publication_cannot_be_enabled(self):
        doc=copy.deepcopy(self.doc)
        doc["publication_approved"]=True
        with self.assertRaisesRegex(ValueError,"unapproved"):
            validate(doc)

if __name__=="__main__":
    unittest.main()
