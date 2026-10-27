import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from import_florida_tsv import read_table

class FloridaBlankDateTests(unittest.TestCase):
    def test_blank_county_date_uses_valid_report_timestamp(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fl.tsv"
            fields=["ElectionNumber","ElectionDate","ElectionName","CountyName","StatType","GrandTotal","CompileDate","TotalRep","TotalDem","TotalOth","TotalNpa"]
            with p.open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
                writer.writeheader()
                for i in range(67):
                    writer.writerow(dict(ElectionNumber="49894",ElectionDate="11/03/2026",ElectionName="General",CountyName=f"County {i}",StatType="Voted Early",GrandTotal="1",CompileDate="",TotalRep="1",TotalDem="0",TotalOth="0",TotalNpa="0"))
                writer.writerow(dict(ElectionNumber="49894",ElectionDate="11/03/2026",ElectionName="General",CountyName="State Totals",StatType="Voted Early",GrandTotal="67",CompileDate="10/27/2026  12:00PM",TotalRep="67",TotalDem="0",TotalOth="0",TotalNpa="0"))
            rows,state,stamp=read_table(p,"Voted Early")
            self.assertEqual(len(rows),67)
            self.assertEqual(state["total"],67)
            self.assertEqual(stamp.date().isoformat(),"2026-10-27")
    def test_missing_all_timestamps_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fl.tsv"
            fields=["ElectionNumber","ElectionDate","ElectionName","CountyName","StatType","GrandTotal","CompileDate","TotalRep","TotalDem","TotalOth","TotalNpa"]
            with p.open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
                writer.writeheader()
                for i in range(67):
                    writer.writerow(dict(ElectionNumber="49894",ElectionDate="11/03/2026",ElectionName="General",CountyName=f"County {i}",StatType="Voted Early",GrandTotal="1",CompileDate="",TotalRep="1",TotalDem="0",TotalOth="0",TotalNpa="0"))
                writer.writerow(dict(ElectionNumber="49894",ElectionDate="11/03/2026",ElectionName="General",CountyName="State Totals",StatType="Voted Early",GrandTotal="67",CompileDate="",TotalRep="67",TotalDem="0",TotalOth="0",TotalNpa="0"))
            with self.assertRaisesRegex(ValueError,"Missing"):
                read_table(p,"Voted Early")
if __name__=="__main__":
    unittest.main()
