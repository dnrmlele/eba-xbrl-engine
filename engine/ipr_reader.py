"""
engine/ipr_reader.py
Reads a filled IPR Excel (produced by ipr_sample_creator.py).
Returns data_by_year: {year: {tpl_code: {(row_code, col_code): float}}}
"""

import re
import openpyxl

from engine.definitions.ipr_templates import TEMPLATE_STRUCTURE

# Sheet name pattern: "2022_S_01_01"  "2025_S_04_00"
SHEET_RE = re.compile(r"^(\d{4})_(S_\d{2}_(?:\d{2}|\d{2}))$")


def _sheet_key(sheet_name: str):
    """Returns (year: int, tpl_code: str) or (None, None)."""
    m = SHEET_RE.match(sheet_name)
    if not m:
        return None, None
    year = int(m.group(1))
    # "S_01_01" → "S 01.01",  "S_03_00" → "S 03.00"
    raw = m.group(2)           # e.g. "S_01_01"
    parts = raw.split("_")     # ["S", "01", "01"]
    tpl = f"{parts[0]} {parts[1]}.{parts[2]}"
    if tpl not in TEMPLATE_STRUCTURE:
        return None, None
    return year, tpl


def read_ipr_excel(file_obj, years: list) -> dict:
    """
    Returns {year: {tpl_code: {(row_code, col_code): float}}}.
    Skips disabled (N/A) sheets.
    """
    wb = openpyxl.load_workbook(file_obj, data_only=True)
    data_by_year = {y: {} for y in years}

    for sheet_name in wb.sheetnames:
        year, tpl_code = _sheet_key(sheet_name)
        if year is None or year not in years:
            continue

        ws = wb[sheet_name]
        rows_def, cols_def = TEMPLATE_STRUCTURE[tpl_code]
        row_codes = {r[0] for r in rows_def}
        col_codes = [c[0] for c in cols_def]

        tpl_data = {}
        for excel_row in ws.iter_rows(values_only=True):
            if not excel_row or excel_row[0] is None:
                continue
            first = str(excel_row[0]).strip()
            # Row code is always the first 4 chars of the cell ("0010    label…")
            rc = first[:4]
            if rc not in row_codes:
                continue
            for c_idx, col_code in enumerate(col_codes, start=1):
                raw = excel_row[c_idx] if c_idx < len(excel_row) else None
                if raw is None:
                    continue
                try:
                    tpl_data[(rc, col_code)] = float(raw)
                except (ValueError, TypeError):
                    pass

        if tpl_data:
            data_by_year[year][tpl_code] = tpl_data

    return data_by_year
