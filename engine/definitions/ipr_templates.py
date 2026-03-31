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
    ("0010", "Total"),
    ("0020", "  of which: Initiated electronically via online banking"),
    ("0030", "  of which: Initiated electronically via mobile payment solutions"),
    ("0040", "  of which: Initiated in a paper-based form"),
    ("0050", "0045 Breakdown by location of PSPs — National"),
    ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
    ("0070", "0065 Breakdown by charges levied — Free of charge"),
    ("0080", "0065 Breakdown by charges levied — Charged"),
    ("0090", "0085 Breakdown by PSU type — PSUs other than consumers"),
    ("0100", "0085 Breakdown by PSU type — Consumers"),
]
S0101_COLS = [
    ("0010", "Number of credit transfers — sent"),
    ("0020", "of which: instant credit transfers — sent"),
    ("0030", "Value of credit transfers — sent"),
    ("0040", "of which: instant credit transfers value — sent"),
    ("0050", "Number of credit transfers — received"),
    ("0060", "of which: instant credit transfers — received"),
    ("0070", "Value of credit transfers — received"),
    ("0080", "of which: instant credit transfers value — received"),
]

S0102_ROWS = S0101_ROWS
S0102_COLS = [
    ("0010", "Number of credit transfers — sent"),
    ("0020", "of which: instant credit transfers — sent"),
    ("0030", "Value of credit transfers — sent (EUR)"),
    ("0040", "of which: instant credit transfers value — sent (EUR)"),
    ("0050", "Number of credit transfers — received"),
    ("0060", "of which: instant credit transfers — received"),
    ("0070", "Value of credit transfers — received (EUR)"),
    ("0080", "of which: instant credit transfers value — received (EUR)"),
]

S0201_ROWS = [
    ("0010", "Total"),
    ("0020", "  of which: Initiated electronically via online banking"),
    ("0030", "  of which: Initiated electronically via mobile payment solutions"),
    ("0040", "  of which: Initiated in a paper-based form"),
    ("0050", "0045 Breakdown by location of PSPs — National"),
    ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
    ("0070", "0065 Breakdown by PSU type — PSUs other than consumers"),
    ("0080", "0065 Breakdown by PSU type — Consumers"),
]
S0201_COLS = [
    ("0010", "Value of charges — sent"),
    ("0020", "of which: instant credit transfers charges — sent"),
    ("0030", "Value of charges — received"),
    ("0040", "of which: instant credit transfers charges — received"),
]

S0202_ROWS = S0201_ROWS
S0202_COLS = [
    ("0010", "Value of charges — sent (EUR)"),
    ("0020", "of which: instant credit transfers charges — sent (EUR)"),
    ("0030", "Value of charges — received (EUR)"),
    ("0040", "of which: instant credit transfers charges — received (EUR)"),
]

S0300_ROWS = [
    ("0010", "Total"),
]
S0300_COLS = [
    ("0010", "Number of payment accounts"),
    ("0020", "Value of charges for payment accounts"),
    ("0030", "of which: maintenance of payment accounts"),
]

S0400_ROWS = [
    ("0010", "Total"),
    ("0020", "0015 Breakdown by location of PSPs — National"),
    ("0030", "0015 Breakdown by location of PSPs — Cross-border"),
]
S0400_COLS = [
    ("0010", "Payee's PSP instances"),
    ("0020", "Payer's PSP instances"),
]

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
    "S 01.01": {
        "template_code": "S 01.01",
        "xbrl_filing_indicator": "eba_LCI:LIS0101",
        "file_name": "S_01_01_a.csv",
        "rows": [
            ("0010", "Total"),
            ("0020", "  of which: Initiated electronically via online banking"),
            ("0030", "  of which: Initiated electronically via mobile payment solutions"),
            ("0040", "  of which: Initiated in a paper-based form"),
            ("0050", "0045 Breakdown by location of PSPs — National"),
            ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
            ("0070", "0065 Breakdown by charges levied — Free of charge"),
            ("0080", "0065 Breakdown by charges levied — Charged"),
            ("0090", "0085 Breakdown by PSU type — PSUs other than consumers"),
            ("0100", "0085 Breakdown by PSU type — Consumers"),
        ],
        "cols": [
            ("0010", "Number of credit transfers — sent"),
            ("0020", "of which: instant credit transfers — sent"),
            ("0030", "Value of credit transfers — sent"),
            ("0040", "of which: instant credit transfers value — sent"),
            ("0050", "Number of credit transfers — received"),
            ("0060", "of which: instant credit transfers — received"),
            ("0070", "Value of credit transfers — received"),
            ("0080", "of which: instant credit transfers value — received"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi3526422",
            ("0010", "0020"): "eba_met:mi3526424",
            ("0010", "0030"): "eba_met:mi3529924",
            ("0010", "0040"): "eba_met:mi3529929",
            ("0010", "0050"): "eba_met:mi3526425",
            ("0010", "0060"): "eba_met:mi3526423",
            ("0010", "0070"): "eba_met:mi3529932",
            ("0010", "0080"): "eba_met:mi3529928",
            ("0020", "0010"): "eba_met:mi3526418",
            ("0020", "0020"): "eba_met:mi3526417",
            ("0020", "0030"): "eba_met:mi3529919",
            ("0020", "0040"): "eba_met:mi3529920",
            ("0030", "0010"): "eba_met:mi3526429",
            ("0030", "0020"): "eba_met:mi3526430",
            ("0030", "0030"): "eba_met:mi3529921",
            ("0030", "0040"): "eba_met:mi3529938",
            ("0040", "0010"): "eba_met:mi3526428",
            ("0040", "0020"): "eba_met:mi3526419",
            ("0040", "0030"): "eba_met:mi3529918",
            ("0040", "0040"): "eba_met:mi3529939",
            ("0050", "0010"): "eba_met:mi3526420",
            ("0050", "0020"): "eba_met:mi3526427",
            ("0050", "0030"): "eba_met:mi3529940",
            ("0050", "0040"): "eba_met:mi3529917",
            ("0060", "0010"): "eba_met:mi3526426",
            ("0060", "0020"): "eba_met:mi3526421",
            ("0060", "0030"): "eba_met:mi3529942",
            ("0060", "0040"): "eba_met:mi3529941",
            ("0070", "0010"): "eba_met:mi3526434",
            ("0070", "0020"): "eba_met:mi3526436",
            ("0070", "0030"): "eba_met:mi3529933",
            ("0070", "0040"): "eba_met:mi3529931",
            ("0070", "0050"): "eba_met:mi3526413",
            ("0070", "0060"): "eba_met:mi3526411",
            ("0070", "0070"): "eba_met:mi3529923",
            ("0070", "0080"): "eba_met:mi3529930",
            ("0080", "0010"): "eba_met:mi3526414",
            ("0080", "0020"): "eba_met:mi3526412",
            ("0080", "0030"): "eba_met:mi3529934",
            ("0080", "0040"): "eba_met:mi3529925",
            ("0080", "0050"): "eba_met:mi3526433",
            ("0080", "0060"): "eba_met:mi3526435",
            ("0080", "0070"): "eba_met:mi3529927",
            ("0080", "0080"): "eba_met:mi3529926",
            ("0090", "0010"): "eba_met:mi3526431",
            ("0090", "0020"): "eba_met:mi3526416",
            ("0090", "0030"): "eba_met:mi3529922",
            ("0090", "0040"): "eba_met:mi3529937",
            ("0100", "0010"): "eba_met:mi3526432",
            ("0100", "0020"): "eba_met:mi3526415",
            ("0100", "0030"): "eba_met:mi3529936",
            ("0100", "0040"): "eba_met:mi3529935",
        },
    },
    "S 01.02": {
        "template_code": "S 01.02",
        "xbrl_filing_indicator": "eba_LCI:LIS0102",
        "file_name": "S_01_02_a.csv",
        "rows": [
            ("0010", "Total"),
            ("0020", "  of which: Initiated electronically via online banking"),
            ("0030", "  of which: Initiated electronically via mobile payment solutions"),
            ("0040", "  of which: Initiated in a paper-based form"),
            ("0050", "0045 Breakdown by location of PSPs — National"),
            ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
            ("0070", "0065 Breakdown by charges levied — Free of charge"),
            ("0080", "0065 Breakdown by charges levied — Charged"),
            ("0090", "0085 Breakdown by PSU type — PSUs other than consumers"),
            ("0100", "0085 Breakdown by PSU type — Consumers"),
        ],
        "cols": [
            ("0010", "Number of credit transfers — sent"),
            ("0020", "of which: instant credit transfers — sent"),
            ("0030", "Value of credit transfers — sent (EUR)"),
            ("0040", "of which: instant credit transfers value — sent (EUR)"),
            ("0050", "Number of credit transfers — received"),
            ("0060", "of which: instant credit transfers — received"),
            ("0070", "Value of credit transfers — received (EUR)"),
            ("0080", "of which: instant credit transfers value — received (EUR)"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi5486832",
            ("0010", "0020"): "eba_met:mi5486836",
            ("0010", "0030"): "eba_met:mi5488660",
            ("0010", "0040"): "eba_met:mi5488659",
            ("0010", "0050"): "eba_met:mi5486837",
            ("0010", "0060"): "eba_met:mi5486838",
            ("0010", "0070"): "eba_met:mi5488658",
            ("0010", "0080"): "eba_met:mi5488657",
        },
    },
    "S 02.01": {
        "template_code": "S 02.01",
        "xbrl_filing_indicator": "eba_LCI:LIS0201",
        "file_name": "S_02_01_a.csv",
        "rows": [
            ("0010", "Total"),
            ("0020", "  of which: Initiated electronically via online banking"),
            ("0030", "  of which: Initiated electronically via mobile payment solutions"),
            ("0040", "  of which: Initiated in a paper-based form"),
            ("0050", "0045 Breakdown by location of PSPs — National"),
            ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
            ("0070", "0065 Breakdown by PSU type — PSUs other than consumers"),
            ("0080", "0065 Breakdown by PSU type — Consumers"),
        ],
        "cols": [
            ("0010", "Value of charges — sent"),
            ("0020", "of which: instant credit transfers charges — sent"),
            ("0030", "Value of charges — received"),
            ("0040", "of which: instant credit transfers charges — received"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi3530892",
            ("0010", "0020"): "eba_met:mi3530879",
            ("0010", "0030"): "eba_met:mi3530893",
            ("0010", "0040"): "eba_met:mi3530880",
            ("0020", "0010"): "eba_met:mi3530877",
            ("0020", "0020"): "eba_met:mi3530886",
            ("0030", "0010"): "eba_met:mi3530887",
            ("0030", "0020"): "eba_met:mi3530888",
            ("0040", "0010"): "eba_met:mi3530876",
            ("0040", "0020"): "eba_met:mi3530885",
            ("0050", "0010"): "eba_met:mi3530874",
            ("0050", "0020"): "eba_met:mi3530875",
            ("0060", "0010"): "eba_met:mi3530884",
            ("0060", "0020"): "eba_met:mi3530873",
            ("0070", "0010"): "eba_met:mi3530878",
            ("0070", "0020"): "eba_met:mi3530889",
            ("0080", "0010"): "eba_met:mi3530890",
            ("0080", "0020"): "eba_met:mi3530891",
        },
    },
    "S 02.02": {
        "template_code": "S 02.02",
        "xbrl_filing_indicator": "eba_LCI:LIS0202",
        "file_name": "S_02_02_a.csv",
        "rows": [
            ("0010", "Total"),
            ("0020", "  of which: Initiated electronically via online banking"),
            ("0030", "  of which: Initiated electronically via mobile payment solutions"),
            ("0040", "  of which: Initiated in a paper-based form"),
            ("0050", "0045 Breakdown by location of PSPs — National"),
            ("0060", "0045 Breakdown by location of PSPs — Cross-border"),
            ("0070", "0065 Breakdown by PSU type — PSUs other than consumers"),
            ("0080", "0065 Breakdown by PSU type — Consumers"),
        ],
        "cols": [
            ("0010", "Value of charges — sent (EUR)"),
            ("0020", "of which: instant credit transfers charges — sent (EUR)"),
            ("0030", "Value of charges — received (EUR)"),
            ("0040", "of which: instant credit transfers charges — received (EUR)"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi3530881",
            ("0010", "0020"): "eba_met:mi3530872",
            ("0010", "0030"): "eba_met:mi3530882",
            ("0010", "0040"): "eba_met:mi3530883",
        },
    },
    "S 03.00": {
        "template_code": "S 03.00",
        "xbrl_filing_indicator": "eba_LCI:LIS0300",
        "file_name": "S_03_00_a.csv",
        "rows": [
            ("0010", "Total"),
        ],
        "cols": [
            ("0010", "Number of payment accounts"),
            ("0020", "Value of charges for payment accounts"),
            ("0030", "of which: maintenance of payment accounts"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi3526437",
            ("0010", "0020"): "eba_met:mi3530894",
            ("0010", "0030"): "eba_met:mi3530895",
        },
    },
    "S 04.00": {
        "template_code": "S 04.00",
        "xbrl_filing_indicator": "eba_LCI:LIS0400",
        "file_name": "S_04_00_a.csv",
        "rows": [
            ("0010", "Total"),
            ("0020", "0015 Breakdown by location of PSPs — National"),
            ("0030", "0015 Breakdown by location of PSPs — Cross-border"),
        ],
        "cols": [
            ("0010", "Payee's PSP instances"),
            ("0020", "Payer's PSP instances"),
        ],
        "cell_map": {
            ("0010", "0010"): "eba_met:mi3530896",
            ("0010", "0020"): "eba_met:mi3530901",
            ("0020", "0010"): "eba_met:mi3530897",
            ("0020", "0020"): "eba_met:mi3530898",
            ("0030", "0010"): "eba_met:mi3530900",
            ("0030", "0020"): "eba_met:mi3530899",
        },
    },
}
