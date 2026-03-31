#!/usr/bin/env python3
"""
generate_ipr_templates.py
Extracts SEPA_IPR concept IDs from the EBA RF 4.2 DPM Annotated Excel
and updates engine/definitions/ipr_templates.py with real cell_map entries.

Usage:
    python generate_ipr_templates.py [path/to/DPM_4.2_Annotated.xlsx]

Download: https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks/reporting-framework-42
"""

import sys, re, os
import openpyxl
from pathlib import Path

EXCEL_PATH  = sys.argv[1] if len(sys.argv) > 1 else "DPM_4.2_Annotated.xlsx"
OUTPUT_PATH = Path("engine/definitions/ipr_templates.py")
MODULE_KEY  = "SEPA_IPR"

if not os.path.exists(EXCEL_PATH):
    print(f"ERROR: {EXCEL_PATH} not found.")
    print("Download EBA RF 4.2 technical package and place the DPM Excel here.")
    sys.exit(1)

print(f"Reading {EXCEL_PATH} …")
wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

sheet_name = next(
    (s for s in wb.sheetnames if "Data Point" in s or "DataPoint" in s),
    wb.sheetnames[0],
)
print(f"Using sheet: {sheet_name}")
ws = wb[sheet_name]

headers = [str(c.value).strip() if c.value else "" for c in next(ws.iter_rows(max_row=1))]
idx = {h: i for i, h in enumerate(headers)}

MODULE_COL = next((h for h in headers if "Module" in h), None)
TABLE_COL  = next((h for h in headers if "Table" in h or "Template" in h), None)
ROW_COL    = next((h for h in headers if h == "Row" or h.startswith("Row")), None)
COL_COL    = next((h for h in headers if h == "Column" or h.startswith("Col")), None)
METRIC_COL = next((h for h in headers if "Metric" in h or "Concept" in h or h == "ID"), None)

print(f"Column mapping: module={MODULE_COL} table={TABLE_COL} row={ROW_COL} col={COL_COL} metric={METRIC_COL}")

concepts: dict[tuple, str] = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    try:
        mod = str(row[idx[MODULE_COL]]).strip() if MODULE_COL else ""
        if MODULE_KEY not in mod:
            continue
        tpl    = str(row[idx[TABLE_COL]]).strip()
        r_code = str(row[idx[ROW_COL]]).strip().zfill(4)
        c_code = str(row[idx[COL_COL]]).strip().zfill(4)
        metric = row[idx[METRIC_COL]]
        if tpl and r_code and c_code and metric:
            concepts[(tpl, r_code, c_code)] = f"eba_met:mi{int(float(metric))}"
    except Exception:
        continue

print(f"Extracted {len(concepts)} SEPA_IPR concepts")

# Inject into ipr_templates.py replacing the cell_map blocks
src = OUTPUT_PATH.read_text(encoding="utf-8")

for tpl_code in set(t for t, _, _ in concepts):
    tpl_concepts = {
        (r, c): v for (t, r, c), v in concepts.items() if t == tpl_code
    }
    # Build new cell_map string
    map_lines = ",\n        ".join(f"(\"{r}\", \"{c}\"): \"{v}\"" for (r, c), v in sorted(tpl_concepts.items()))
    new_map = f"        \"cell_map\": {{\n        {map_lines}\n        }}"
    # Pattern: match cell_map block for this template
    pat = re.compile(
        r'(\"\' + re.escape(tpl_code) + r'\":.*?\"cell_map\":\s*\{)[^}]*(\})',
        re.DOTALL
    )
    src = pat.sub(lambda m: m.group(0)[:m.start(2)-m.start()] + "\n        " + map_lines + "\n        " + "}", src)

OUTPUT_PATH.write_text(src, encoding="utf-8")
print(f"✅ ipr_templates.py updated with {len(concepts)} concept entries")
