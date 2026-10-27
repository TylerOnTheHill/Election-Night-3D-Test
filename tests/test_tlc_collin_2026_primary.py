import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fetch_tlc_collin_2026_primary import convert_records

def poly():
 return {"type":"Polygon","coordinates":[[[-96.7,33.1],[-96.6,33.1],[-96.6,33.2],[-96.7,33.1]]]}

class TLCCollinTests(unittest.TestCase):
 def test_real_tlc_cnty_schema(self):
  rows=[({"CNTY":85,"PREC":"00101","PCTKEY":"4808500101"},poly()),
        ({"CNTY":201,"PREC":"0001"},poly())]
  data=convert_records(rows)
  self.assertEqual(len(data["features"]),1)
  self.assertEqual(data["features"][0]["properties"]["area_id"],"00101")
 def test_accept_fips_schema(self):
  self.assertEqual(len(convert_records([({"FIPS":"48085","PREC":"101"},poly())])["features"]),1)
 def test_duplicate_ids_block(self):
  with self.assertRaisesRegex(ValueError,"Duplicate"):
   convert_records([({"CNTY":85,"PREC":"101"},poly()),({"CNTY":85,"PREC":"101"},poly())])
 def test_no_collin_records_block(self):
  with self.assertRaisesRegex(ValueError,"No Collin"):
   convert_records([({"CNTY":201,"PREC":"101"},poly())])
 def test_invalid_geometry_block(self):
  with self.assertRaisesRegex(ValueError,"Invalid"):
   convert_records([({"CNTY":85,"PREC":"101"},{"type":"Point","coordinates":[-96,33]})])
if __name__=="__main__":unittest.main()
