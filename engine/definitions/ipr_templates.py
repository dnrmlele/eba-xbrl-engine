"""
engine/definitions/ipr_templates.py
SEPA_IPR template definitions — EBA RF 4.2 · ITS Annex I
Auto-generated concept map: run generate_ipr_templates.py
"""

# ── Filing indicators ─────────────────────────────────────────────────────────
ALL_INDICATORS = [
    "eba_LCI:LIS0101",  # S 01.01 — Volumes national currency  (All PSPs)
    "eba_LCI:LIS0102",  # S 01.02 — Volumes EUR                (Non-euro MS only)
    "eba_LCI:LIS0201",  # S 02.01 — Charges national currency  (All PSPs)
    "eba_LCI:LIS0202",  # S 02.02 — Charges EUR                (Non-euro MS only)
    "eba_LCI:LIS0300",  # S 03.00 — Accounts & total charges   (All PSPs)
    "eba_LCI:LIS0400",  # S 04.00 — Rejected SCT Inst          (All PSPs)
]

EURO_AREA_FILED = [
    "eba_LCI:LIS0101",
    "eba_LCI:LIS0201",
    "eba_LCI:LIS0300",
    "eba_LCI:LIS0400",
]
NON_EURO_FILED = list(ALL_INDICATORS)

# ── Taxonomy ──────────────────────────────────────────────────────────────────
# TODO: confirm exact entryPointHREF from EBA RF 4.2 taxonomy ZIP
TAXONOMY_URL = "https://eba.europa.eu/eu/fr/taxonomy/2026-03-27/mod/sepa_ipr"

# ── Row / column definitions (ITS Annex I) ────────────────────────────────────
S0101_ROWS = [
    ("0010", "Total CT payer PSP"),
    ("0020", "  of which: SCT Inst"),
    ("0030", "  of which: SCT (non-instant)"),
    ("0040", "Accounts subject to charges for SCT Inst — payer"),
    ("0050", "    Free of charge"),
    ("0060", "    Per-transaction fee"),
    ("0070", "    Account-maintenance fee only"),
    ("0080", "Total CT payee PSP"),
    ("0090", "  of which: SCT Inst"),
    ("0100", "  of which: SCT (non-instant)"),
    ("0110", "Accounts subject to charges for SCT Inst — payee"),
    ("0120", "    Free of charge"),
    ("0130", "    Per-transaction fee"),
    ("0140", "    Account-maintenance fee only"),
]
S0101_COLS = [("0010", "Number of transactions"), ("0020", "Value (national currency)")]

S0102_ROWS = S0101_ROWS
S0102_COLS = [("0010", "Number of transactions"), ("0020", "Value (EUR)")]

S0201_ROWS = [
    ("0010", "Charges on payer — SCT Inst"),
    ("0020", "  of which: per-transaction fees"),
    ("0030", "  of which: account-maintenance fees"),
    ("0040", "Charges on payee — SCT Inst"),
    ("0050", "  of which: per-transaction fees"),
    ("0060", "  of which: account-maintenance fees"),
    ("0070", "Charges on payer — SCT (non-instant)"),
    ("0080", "Charges on payee — SCT (non-instant)"),
]
S0201_COLS = [
    ("0010", "Total charges (national currency)"),
    ("0020", "Average charge per transaction"),
]

S0202_ROWS = S0201_ROWS
S0202_COLS = [("0010", "Total charges (EUR)"), ("0020", "Average charge per transaction (EUR)")]

S0300_ROWS = [
    ("0010", "Number of payment accounts — payer PSP"),
    ("0020", "  of which: offering SCT Inst"),
    ("0030", "  of which: free SCT Inst"),
    ("0040", "Total charges collected from payers (national currency)"),
    ("0050", "Total charges collected from payees (national currency)"),
]
S0300_COLS = [("0010", "Value")]

S0400_ROWS = [
    ("0010", "Total SCT Inst submitted"),
    ("0020", "Total SCT Inst rejected"),
    ("0030", "  of which: rejected — sanctions screening (TFRM)"),
    ("0040", "Share of rejected SCT Inst (%)"),
    ("0050", "  of which: share rejected TFRM (%)"),
]
S0400_COLS = [("0010", "Value")]

TEMPLATE_STRUCTURE = {
    "S 01.01": (S0101_ROWS, S0101_COLS),
    "S 01.02": (S0102_ROWS, S0102_COLS),
    "S 02.01": (S0201_ROWS, S0201_COLS),
    "S 02.02": (S0202_ROWS, S0202_COLS),
    "S 03.00": (S0300_ROWS, S0300_COLS),
    "S 04.00": (S0400_ROWS, S0400_COLS),
}

TEMPLATE_FILE_NAMES = {
    "S 01.01": "S_01_01_a.csv",
    "S 01.02": "S_01_02_a.csv",
    "S 02.01": "S_02_01_a.csv",
    "S 02.02": "S_02_02_a.csv",
    "S 03.00": "S_03_00_a.csv",
    "S 04.00": "S_04_00_a.csv",
}

INDICATOR_MAP = {t: ind for t, ind in zip(TEMPLATE_STRUCTURE, ALL_INDICATORS)}

# ── Concept map — run generate_ipr_templates.py to populate ──────────────────
IPR_TEMPLATES = {
    tpl: {
        "template_code": tpl,
        "xbrl_filing_indicator": INDICATOR_MAP[tpl],
        "file_name": TEMPLATE_FILE_NAMES[tpl],
        "rows": rows,
        "cols": cols,
        "cell_map": {},  # populated by generate_ipr_templates.py
    }
    for tpl, (rows, cols) in TEMPLATE_STRUCTURE.items()
}
