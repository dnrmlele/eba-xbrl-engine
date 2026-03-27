"""
engine/generator.py
EBA XBRL-CSV package generator — LCR DA (C72–C76), COREP 4.2
Produces packages conformant with:
  - XBRL International CSV 2021 (https://xbrl.org/2021/xbrl-csv)
  - EBA Filing Rules v5.8
  - LCR Delegated Act taxonomy (EBA 2025-03-31)

Concept IDs: eba_met:mi{variable_id}  (extracted from EBA annotated tables)
"""
import json, zipfile, io, csv
from datetime import date as date_type

# EBA taxonomy reference for LCR-DA (COREP 4.2, from 2025-03-31)
EBA_LCR_TAXONOMY = (
    "https://www.eba.europa.eu/eu/fr/xbrl/crr/fws/lcr/cir-2015-61/"
    "2025-03-31/mod/lcr-da.json"
)

EBA_NAMESPACES = {
    "eba_met": "http://www.eba.europa.eu/xbrl/crr/dict/met",
    "eba_dim": "http://www.eba.europa.eu/xbrl/crr/dict/dim",
    "eba_LCI": "http://www.eba.europa.eu/xbrl/crr/fws/lcr/cir-2015-61/2025-03-31/tab",
    "eba_GA":  "http://www.eba.europa.eu/xbrl/crr/dict/dim",
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
        """
        Generate a complete EBA XBRL-CSV ZIP package.
        data: output of EBAExcelReader.read()
        """
        buf = io.BytesIO()
        filing_indicators = {}
        table_files = {}   # table_key → csv_content

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for sheet_name, inst in data.items():
                fi  = inst.get("xbrl_filing_indicator", "")
                ccy = inst["currency"]
                filing_indicators[fi] = True

                csv_filename = self._csv_filename(inst)
                csv_content  = self._build_csv(inst)
                table_files[csv_filename] = (inst, csv_content)
                zf.writestr(f"reports/{csv_filename}", csv_content)

            # report.json — the XBRL-CSV manifest
            report_json = self._build_report_json(data, filing_indicators, table_files)
            zf.writestr("reports/report.json",
                        json.dumps(report_json, indent=2, ensure_ascii=False))

            # META-INF/reportPackage.json
            zf.writestr("META-INF/reportPackage.json",
                        json.dumps(self._build_package_info(data), indent=2))

        buf.seek(0)
        return buf.read()

    def get_preview(self, data: dict) -> dict:
        preview = {}
        for i, (sheet_name, inst) in enumerate(data.items()):
            if i >= 3:
                break
            preview[f"reports/{self._csv_filename(inst)}"] = self._build_csv(inst)
        fi = {inst.get("xbrl_filing_indicator", ""): True for inst in data.values()}
        table_files = {self._csv_filename(inst): (inst, "") for inst in data.values()}
        preview["reports/report.json"] = json.dumps(
            self._build_report_json(data, fi, table_files), indent=2)
        return preview

    # ── CSV generation ────────────────────────────────────────────────────────
    def _csv_filename(self, inst: dict) -> str:
        code = inst["template_code"].replace(" ", "_").replace(".", "_")
        ccy  = inst["currency"]
        sub  = inst.get("sub_template", "a")
        return f"{code}_{sub}_{ccy}.csv"

    def _build_csv(self, inst: dict) -> str:
        """
        Build the XBRL-CSV fact file for one template instance.
        Format: concept,value,decimals,unit
        """
        cell_map    = inst.get("cell_map", {})    # (row_code, col_code) → concept
        data_points = inst.get("data_points", {}) # "row_code_col_code" → value

        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["concept", "value", "decimals", "unit"])

        for dp_key, value in data_points.items():
            # dp_key = "0010_0010"
            parts = dp_key.split("_", 1)
            if len(parts) != 2:
                continue
            row_code, col_code = parts
            concept = cell_map.get((row_code, col_code))
            if concept is None or value is None:
                continue
            unit = self.base_ccy if isinstance(value, (int, float)) else ""
            writer.writerow([concept, value, self.decimals, unit])

        return out.getvalue()

    # ── report.json ───────────────────────────────────────────────────────────
    def _build_report_json(self, data: dict, filing_indicators: dict,
                           table_files: dict) -> dict:
        tables = {}
        for csv_fname, (inst, _) in table_files.items():
            fi   = inst.get("xbrl_filing_indicator", "")
            ccy  = inst["currency"]
            key  = f"{fi}_{ccy}" if ccy != self.base_ccy else fi
            tables[key] = {
                "url": csv_fname,
                "optional": True,
                "parameters": {
                    "periodOfReport":   self.ref_date,
                    "entityIdentifier": self.entity_id,
                    "currency":         ccy,
                    "decimals":         str(self.decimals),
                },
            }

        return {
            "documentInfo": {
                "documentType": "https://xbrl.org/2021/xbrl-csv",
                "taxonomy":     [EBA_LCR_TAXONOMY],
                "namespaces":   EBA_NAMESPACES,
            },
            "filing-indicators": filing_indicators,
            "parameters": {
                "periodOfReport":   self.ref_date,
                "entityIdentifier": f"lei:{self.entity_id}",
                "decimals":         str(self.decimals),
                "currency":         self.base_ccy,
            },
            "tables": tables,
        }

    def _build_package_info(self, data: dict) -> dict:
        modules = sorted({v.get("module", "LCR") for v in data.values()})
        return {
            "documentInfo": {
                "documentType": "http://xbrl.org/2016/report-package",
            },
            "reportPackage": {
                "name": f"EBA COREP 4.2 XBRL-CSV — {', '.join(modules)}",
                "description": (
                    f"Generated by eba-xbrl-engine "
                    f"Entity: {self.entity_id} "
                    f"Period: {self.ref_date}"
                ),
                "publisher":        f"lei:{self.entity_id}",
                "publicationDate":  str(date_type.today()),
                "entryPoints": [{
                    "href": "reports/report.json",
                    "type": "https://xbrl.org/2021/xbrl-csv",
                }],
            },
        }
