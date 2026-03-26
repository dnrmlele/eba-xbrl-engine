
import json, csv, io, zipfile
from typing import Dict, Any
from collections import defaultdict

class XBRLCSVGenerator:
    """
    Generates an EBA xBRL-CSV report package (ZIP) with multi-currency support.

    Package structure (EBA Filing Rules v5.8):
      META-INF/reports.json
      reports/parameters.csv
      reports/FilingIndicators.csv
      reports/C_72_00_EUR.csv
      reports/C_72_00_USD.csv
      reports/C_73_00_EUR.csv
      …
    """
    TAXONOMY_URL = ("https://www.eba.europa.eu/eu/fr/xbrl/crr/fws/lcr/"
                    "4.2/2024-12-31/mod/lcr.json")
    NAMESPACE    = "http://www.eba.europa.eu/xbrl/crr/dict/dom/LCI"
    CCY_DIM      = "eba_LCI:CUS"   # currency typed dimension

    def __init__(self, entity_id: str, reference_date: str,
                 decimals: int = -3, base_currency: str = "EUR"):
        self.entity_id      = entity_id
        self.reference_date = reference_date
        self.decimals       = decimals
        self.base_currency  = base_currency

    # ── Public API ─────────────────────────────────────────────────────────────
    def generate_package(self, extracted_data: Dict[str, Any]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("META-INF/reports.json",
                        self._reports_json(extracted_data))
            zf.writestr("reports/parameters.csv",
                        self._parameters_csv())
            zf.writestr("reports/FilingIndicators.csv",
                        self._filing_indicators(extracted_data))
            for key, data in extracted_data.items():
                zf.writestr(f"reports/{key}.csv",
                            self._template_csv(data))
        return buf.getvalue()

    def get_preview(self, extracted_data: Dict[str, Any]) -> Dict[str, str]:
        out = {
            "META-INF/reports.json":        self._reports_json(extracted_data),
            "reports/parameters.csv":       self._parameters_csv(),
            "reports/FilingIndicators.csv": self._filing_indicators(extracted_data),
        }
        for key, data in extracted_data.items():
            out[f"reports/{key}.csv"] = self._template_csv(data)
        return out

    # ── Package builders ──────────────────────────────────────────────────────
    def _reports_json(self, extracted_data: dict) -> str:
        reports = {
            "parameters":       {"url": "reports/parameters.csv"},
            "FilingIndicators": {"url": "reports/FilingIndicators.csv"},
        }
        for key, data in extracted_data.items():
            currency = data.get("currency", "EUR")
            entry = {
                "url":        f"reports/{key}.csv",
                "template":   data["filing_indicator"],
                "dimensions": {self.CCY_DIM: f"ISO4217:{currency}"},
            }
            reports[key] = entry

        doc = {
            "documentInfo": {
                "documentType": "https://xbrl.org/2021/xbrl-csv",
                "namespaces":   {"eba_LCI": self.NAMESPACE},
                "taxonomy":     [self.TAXONOMY_URL],
            },
            "reports": reports,
        }
        return json.dumps(doc, indent=2)

    def _parameters_csv(self) -> str:
        out = io.StringIO(); w = csv.writer(out)
        w.writerow(["name", "value"])
        w.writerow(["entityIdentifier", self.entity_id])
        w.writerow(["periodInstant",    self.reference_date])
        w.writerow(["decimals",         str(self.decimals)])
        w.writerow(["baseCurrency",     f"ISO4217:{self.base_currency}"])
        return out.getvalue()

    def _filing_indicators(self, extracted_data: dict) -> str:
        out = io.StringIO(); w = csv.writer(out)
        w.writerow(["templateId", "reported", "currency"])
        for data in extracted_data.values():
            w.writerow([data["filing_indicator"], "true",
                        data.get("currency", "EUR")])
        return out.getvalue()

    def _template_csv(self, template_data: dict) -> str:
        dps = template_data.get("data_points", [])
        if not dps:
            return ""
        row_ids = list(dict.fromkeys(d["row_id"] for d in dps))
        col_ids = list(dict.fromkeys(d["col_id"] for d in dps))
        lookup  = {(d["row_id"], d["col_id"]): d["value"] for d in dps}
        out = io.StringIO(); w = csv.writer(out)
        w.writerow(["r"] + col_ids)
        for r in row_ids:
            w.writerow([r] + [lookup.get((r, c), "") for c in col_ids])
        return out.getvalue()
