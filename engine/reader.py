
import openpyxl, logging, re
from typing import Dict, Any, List
from .definitions.lcr_templates import LCR_TEMPLATES

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = {"EUR","USD","GBP","CHF","JPY","CNY","SEK","NOK","DKK","CAD","AUD"}

class EBAExcelReader:
    """
    Reads EBA Excel templates (C72–C76) with multi-currency support.

    Sheet naming convention:
      - "C 72.00"        → EUR (base currency, no suffix)
      - "C 72.00 USD"    → USD instance
      - "C 72.00 GBP"    → GBP instance
    """
    def __init__(self, templates_config: dict = None):
        self.config = templates_config or LCR_TEMPLATES

    # ── Public API ─────────────────────────────────────────────────────────────
    def read(self, file_path_or_buffer) -> Dict[str, Any]:
        """
        Returns a flat dict keyed as {TEMPLATE}_{CURRENCY}
        e.g. "C_72_00_EUR", "C_72_00_USD", …
        """
        try:
            wb = openpyxl.load_workbook(file_path_or_buffer, data_only=True)
        except Exception as e:
            raise ValueError(f"Cannot open Excel file: {e}")

        currencies = self._detect_currencies(wb)
        logger.info(f"Detected currencies: {currencies}")

        extracted = {}
        for template_key, template_def in self.config.items():
            for currency in currencies:
                sheet_name = self._sheet_name(template_def, currency)
                if sheet_name not in wb.sheetnames:
                    logger.debug(f"Sheet '{sheet_name}' not found, skipping.")
                    continue
                ws = wb[sheet_name]
                pts = self._extract(ws, template_def)
                if pts:
                    instance_key = f"{template_key}_{currency}"
                    extracted[instance_key] = {
                        "template_code":    template_def["template_code"],
                        "name":             template_def["name"],
                        "filing_indicator": template_def["xbrl_filing_indicator"],
                        "template_key":     template_key,
                        "currency":         currency,
                        "data_points":      pts,
                    }
                    logger.info(f"  {instance_key}: {len(pts)} data points")
        return extracted

    def get_currencies(self, file_path_or_buffer) -> List[str]:
        """Return list of currencies detected in the workbook."""
        wb = openpyxl.load_workbook(file_path_or_buffer, data_only=True)
        return self._detect_currencies(wb)

    def get_template_info(self) -> list:
        return [{"key": k, "code": v["template_code"], "name": v["name"],
                 "sheet_name": v["sheet_name"]} for k, v in self.config.items()]

    # ── Private helpers ────────────────────────────────────────────────────────
    def _detect_currencies(self, wb) -> List[str]:
        """
        Scan sheet names to detect all reported currencies.
        "C 72.00"     → EUR (default)
        "C 72.00 USD" → USD
        """
        currencies = set()
        base_names = {tdef["sheet_name"] for tdef in self.config.values()}

        for sheet in wb.sheetnames:
            for base in base_names:
                if sheet.strip() == base:
                    currencies.add("EUR")
                elif sheet.strip().startswith(base + " "):
                    suffix = sheet.strip()[len(base):].strip().upper()
                    if re.fullmatch(r"[A-Z]{3}", suffix):
                        currencies.add(suffix)

        if not currencies:
            logger.warning("No matching sheets found.")
            return []

        # EUR always first, then alphabetical
        return ["EUR"] + sorted(c for c in currencies if c != "EUR")

    def _sheet_name(self, template_def: dict, currency: str) -> str:
        base = template_def["sheet_name"]
        return base if currency == "EUR" else f"{base} {currency}"

    def _extract(self, ws, template_def: dict) -> list:
        points = []
        for row_id, row_def in template_def.get("rows", {}).items():
            er = row_def.get("excel_row")
            for col_id, col_def in template_def.get("columns", {}).items():
                ec = col_def.get("excel_col")
                if not er or not ec:
                    continue
                value = ws.cell(row=er, column=ec).value
                if value is not None:
                    points.append({
                        "row_id":    row_id, "col_id":    col_id,
                        "row_label": row_def.get("label", ""),
                        "col_label": col_def.get("label", ""),
                        "value":     value,
                    })
        return points
