
import openpyxl, logging
from typing import Dict, Any
from .definitions.lcr_templates import LCR_TEMPLATES

logger = logging.getLogger(__name__)

class EBAExcelReader:
    """Reads EBA Excel templates and extracts XBRL data points."""

    def __init__(self, templates_config: dict = None):
        self.config = templates_config or LCR_TEMPLATES

    def read(self, file_path_or_buffer) -> Dict[str, Any]:
        try:
            wb = openpyxl.load_workbook(file_path_or_buffer, data_only=True)
        except Exception as e:
            raise ValueError(f"Failed to open Excel file: {e}")

        extracted = {}
        for template_key, template_def in self.config.items():
            sheet_name = template_def.get("sheet_name", template_key)
            if sheet_name not in wb.sheetnames:
                logger.warning(f"Sheet '{sheet_name}' not found. Skipping.")
                continue
            ws = wb[sheet_name]
            data_points = self._extract(ws, template_def)
            if data_points:
                extracted[template_key] = {
                    "template_code": template_def["template_code"],
                    "name": template_def["name"],
                    "filing_indicator": template_def["xbrl_filing_indicator"],
                    "data_points": data_points,
                }
                logger.info(f"Extracted {len(data_points)} data points from {sheet_name}")
        return extracted

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
                        "row_id": row_id, "col_id": col_id,
                        "row_label": row_def.get("label", ""),
                        "col_label": col_def.get("label", ""),
                        "value": value,
                    })
        return points

    def get_template_info(self) -> list:
        return [{"key": k, "code": v["template_code"], "name": v["name"],
                 "sheet_name": v["sheet_name"]} for k, v in self.config.items()]
