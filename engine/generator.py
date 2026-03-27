"""
engine/generator.py
EBA XBRL-CSV package generator — LCR DA (C72-C76), COREP 4.2
Produces packages conformant with:
  - XBRL International CSV 2021
  - EBA Filing Rules v5.8
  - LCR Delegated Act taxonomy (EBA 2025-03-31)
"""
import json, zipfile, io, csv
from datetime import date as date_type

EBA_LCR_TAXONOMY = (
    "https://www.eba.europa.eu/eu/fr/xbrl/crr/fws/lcr/cir-2015-61/"
    "2025-03-31/mod/lcr-da.json"
)
EBA_NAMESPACES = {
    "eba_met": "http://www.eba.europa.eu/xbrl/crr/dict/met",
    "eba_dim": "http://www.eba.europa.eu/xbrl/crr/dict/dim",
    "eba_LCI": "http://www.eba.europa.eu/xbrl/crr/fws/lcr/cir-2015-61/2025-03-31/tab",
    "xbrl":    "https://xbrl.org/2021/xbrl-csv",
    "iso4217": "http://www.xbrl.org/2003/iso4217",
    "lei":     "http://standards.iso.org/iso/17442",
}


class XBRLCSVGenerator:
    def __init__(self, entity_id: str, ref_date: str,
                 decimals: int = -3, base_ccy: str = "EUR"):
        self.entity_id = entity_id
        self.ref_date  = ref_date
        self.decimals  = decimals
        self.base_ccy  = base_ccy

    def generate_package(self, data: dict) -> bytes:
        buf = io.BytesIO()
        filing_indicators = {}
        reports_map = {}

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sheet_name, inst in data.items():
                fi       = inst.get("xbrl_filing_indicator", "")
                ccy      = inst["currency"]
                filing_indicators[fi] = True

                csv_path    = f"reports/{self._csv_filename(inst)}"
                csv_content = self._build_csv(inst)
                report_key  = f"{fi}_{ccy}" if ccy != self.base_ccy else fi
                reports_map[report_key] = (inst, csv_path, csv_content)
                zf.writestr(csv_path, csv_content)

            # reports/parameters.csv
            zf.writestr("reports/parameters.csv",
                        self._build_parameters_csv())

            # reports/FilingIndicators.csv
            zf.writestr("reports/FilingIndicators.csv",
                        self._build_filing_indicators_csv(data))

            # META-INF/reports.json  (correct EBA location)
            reports_json = self._build_reports_json(reports_map)
            zf.writestr("META-INF/reports.json",
                        json.dumps(reports_json, indent=2, ensure_ascii=False))

            # META-INF/reportPackage.json
            zf.writestr("META-INF/reportPackage.json",
                        json.dumps(self._build_package_info(data), indent=2))

        buf.seek(0)
        return buf.read()

    def get_preview(self, data: dict) -> dict:
        preview = {}
        for i, (sheet_name, inst) in enumerate(data.items()):
            if i >= 2:
                break
            preview[f"reports/{self._csv_filename(inst)}"] = self._build_csv(inst)
        preview["reports/parameters.csv"] = self._build_parameters_csv()
        preview["reports/FilingIndicators.csv"] = self._build_filing_indicators_csv(data)
        reports_map = {}
        for sheet_name, inst in data.items():
            fi  = inst.get("xbrl_filing_indicator", "")
            ccy = inst["currency"]
            key = f"{fi}_{ccy}" if ccy != self.base_ccy else fi
            reports_map[key] = (inst, f"reports/{self._csv_filename(inst)}", "")
        preview["META-INF/reports.json"] = json.dumps(
            self._build_reports_json(reports_map), indent=2)
        return preview

    # ── CSV ───────────────────────────────────────────────────────────────────
    def _csv_filename(self, inst: dict) -> str:
        code = inst["template_code"].replace(" ", "_").replace(".", "_")
        sub  = inst.get("sub_template", "a")
        ccy  = inst["currency"]
        return f"{code}_{sub}_{ccy}.csv"

    def _build_csv(self, inst: dict) -> str:
        cell_map    = inst.get("cell_map", {})
        data_points = inst.get("data_points", {})
        out    = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["concept", "value", "decimals", "unit"])
        for dp_key, value in data_points.items():
            parts = dp_key.split("_", 1)
            if len(parts) != 2 or value is None:
                continue
            row_code, col_code = parts
            concept = cell_map.get((row_code, col_code))
            if concept is None:
                continue
            unit = self.base_ccy if isinstance(value, (int, float)) else ""
            writer.writerow([concept, value, self.decimals, unit])
        return out.getvalue()

    # ── parameters.csv ────────────────────────────────────────────────────────
    def _build_parameters_csv(self) -> str:
        out = io.StringIO()
        w   = csv.writer(out, lineterminator="\n")
        w.writerow(["name", "value"])
        w.writerow(["entityIdentifier", self.entity_id])
        w.writerow(["periodInstant",    self.ref_date])
        w.writerow(["decimals",         str(self.decimals)])
        w.writerow(["currency",         self.base_ccy])
        return out.getvalue()

    # ── FilingIndicators.csv ──────────────────────────────────────────────────
    def _build_filing_indicators_csv(self, data: dict) -> str:
        out  = io.StringIO()
        w    = csv.writer(out, lineterminator="\n")
        w.writerow(["templateId", "currency", "reported"])
        seen = set()
        for inst in data.values():
            fi  = inst.get("xbrl_filing_indicator", "")
            ccy = inst["currency"]
            key = (fi, ccy)
            if key not in seen and fi:
                w.writerow([fi, ccy, "true"])
                seen.add(key)
        return out.getvalue()

    # ── META-INF/reports.json ─────────────────────────────────────────────────
    def _build_reports_json(self, reports_map: dict) -> dict:
        reports = {}
        for report_key, (inst, csv_path, _) in reports_map.items():
            ccy = inst["currency"]
            reports[report_key] = {
                "url":        csv_path,
                "optional":   True,
                "dimensions": {"eba_dim:CUS": f"ISO4217:{ccy}"},
                "parameters": {
                    "periodInstant":    self.ref_date,
                    "entityIdentifier": self.entity_id,
                    "decimals":         str(self.decimals),
                },
            }
        return {
            "documentInfo": {
                "documentType": "https://xbrl.org/2021/xbrl-csv",
                "taxonomy":     [EBA_LCR_TAXONOMY],
                "namespaces":   EBA_NAMESPACES,
            },
            "parameters": {
                "periodInstant":    self.ref_date,
                "entityIdentifier": f"lei:{self.entity_id}",
                "decimals":         str(self.decimals),
                "currency":         self.base_ccy,
            },
            "reports": reports,
        }

    def _build_package_info(self, data: dict) -> dict:
        return {
            "documentInfo": {
                "documentType": "http://xbrl.org/2016/report-package",
            },
            "reportPackage": {
                "name": "EBA COREP 4.2 XBRL-CSV — LCR DA",
                "publisher": f"lei:{self.entity_id}",
                "publicationDate": str(date_type.today()),
                "entryPoints": [{
                    "href": "META-INF/reports.json",
                    "type": "https://xbrl.org/2021/xbrl-csv",
                }],
            },
        }
