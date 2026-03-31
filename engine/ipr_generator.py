"""
engine/ipr_generator.py
SEPA_IPR XBRL-CSV package generator.
Produces one conformant ZIP per reference year, ready for CSSF eDesk.
"""

import csv
import io
import json
import zipfile

from engine.definitions.ipr_templates import (
    ALL_INDICATORS,
    EURO_AREA_FILED,
    TAXONOMY_URL,
    IPR_TEMPLATES,
    TEMPLATE_FILE_NAMES,
)


def _parameters_csv(lei: str, period: str, decimals: int) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "value"])
    w.writerow(["entityIdentifier", lei])
    w.writerow(["entityScheme", "http://standards.iso.org/iso/17442"])
    w.writerow(["periodInstant", period])
    w.writerow(["decimals", str(decimals)])
    return buf.getvalue()


def _filing_indicators_csv(filed: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["templateOrTable", "filed"])
    for ind in ALL_INDICATORS:
        w.writerow([ind, "true" if ind in filed else "false"])
    return buf.getvalue()


def _template_csv(tpl_code: str, data: dict) -> str:
    """data: {(row_code, col_code): numeric_value}"""
    cell_map = IPR_TEMPLATES[tpl_code]["cell_map"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["concept", "value", "decimals"])
    for (row, col), value in data.items():
        concept = cell_map.get((row, col))
        if concept and value is not None:
            w.writerow([concept, value, 0])
    return buf.getvalue()


def _reports_json() -> str:
    return json.dumps(
        {
            "documentInfo": {
                "documentType": "https://xbrl.org/2021/xbrl-csv",
                "taxonomy": [TAXONOMY_URL],
                "namespaces": {
                    "eba_met": "https://eba.europa.eu/xbrl/crr/dict/met",
                    "eba_LCI": "https://eba.europa.eu/xbrl/crr/dict/lci",
                },
            },
            "tableTemplates": {
                ind: {"dimensions": {"eba_LCI:LCI": ind}} for ind in ALL_INDICATORS
            },
        },
        indent=2,
    )


def _report_package_json(lei: str, period: str) -> str:
    return json.dumps(
        {
            "documentInfo": {"documentType": "https://xbrl.org/2021/report-package"},
            "reports": {
                "report": {"entryPoints": [TAXONOMY_URL], "reportDate": period}
            },
        },
        indent=2,
    )


def generate_ipr_zip(
    lei: str,
    year: int,
    decimals: int,
    template_data: dict,
    filed_indicators: list | None = None,
) -> bytes:
    """Generate a single-year SEPA_IPR XBRL-CSV ZIP."""
    period = f"{year}-12-31"
    filed = filed_indicators or EURO_AREA_FILED
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("META-INF/reports.json", _reports_json())
        zf.writestr("META-INF/reportPackage.json", _report_package_json(lei, period))
        zf.writestr("reports/parameters.csv", _parameters_csv(lei, period, decimals))
        zf.writestr("reports/FilingIndicators.csv", _filing_indicators_csv(filed))
        for tpl_code, fname in TEMPLATE_FILE_NAMES.items():
            data = template_data.get(tpl_code, {})
            zf.writestr(f"reports/{fname}", _template_csv(tpl_code, data))
    return buf.getvalue()


def generate_ipr_multi_year_zips(
    lei: str,
    years: list,
    decimals: int,
    data_by_year: dict,
    filed_indicators: list | None = None,
) -> dict:
    """Returns {year: zip_bytes} — one ZIP per reference year."""
    return {
        year: generate_ipr_zip(
            lei=lei,
            year=year,
            decimals=decimals,
            template_data=data_by_year.get(year, {}),
            filed_indicators=filed_indicators,
        )
        for year in years
    }
