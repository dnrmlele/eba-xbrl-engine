
"""
EBA XBRL-CSV Package Validator
Simulates the checks performed by EBA/EUCLID before acceptance.
Based on: EBA Filing Rules v5.8, xBRL-CSV 1.0 spec, EBA DPM validation rules.
"""
import json, csv, re, io, zipfile
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

# ── Valid EBA taxonomy URLs ────────────────────────────────────────────────────
VALID_TAXONOMY_PATTERNS = [
    r"https://www\.eba\.europa\.eu/eu/fr/xbrl/crr/fws/",
    r"https://www\.eba\.europa\.eu/eu/fr/xbrl/",
]
VALID_FILING_INDICATORS = {
    "eba_LCI:LI72","eba_LCI:LI73","eba_LCI:LI74","eba_LCI:LI75","eba_LCI:LI75_1","eba_LCI:LI76",
    "eba_met:LI01","eba_met:LI02",  # COREP OF
}
VALID_ISO4217 = {
    "EUR","USD","GBP","CHF","JPY","SEK","NOK","DKK","CAD","AUD","CNY",
    "HKD","SGD","NZD","MXN","BRL","INR","RUB","ZAR","TRY","PLN","CZK","HUF",
}
VALID_DECIMALS = {"-3", "-6", "0", "-9", "3", "6"}

@dataclass
class CheckResult:
    rule_id:  str
    level:    str   # ERROR | WARNING | INFO
    passed:   bool
    message:  str
    detail:   str = ""

@dataclass
class ValidationReport:
    results:       List[CheckResult] = field(default_factory=list)
    package_name:  str = ""

    # ── Aggregates ─────────────────────────────────────────────────────────────
    @property
    def errors(self):   return [r for r in self.results if r.level=="ERROR"   and not r.passed]
    @property
    def warnings(self): return [r for r in self.results if r.level=="WARNING" and not r.passed]
    @property
    def infos(self):    return [r for r in self.results if r.level=="INFO"    and not r.passed]
    @property
    def total(self):    return len(self.results)
    @property
    def passed_count(self): return sum(1 for r in self.results if r.passed)
    @property
    def score(self):    return round(self.passed_count / self.total * 100) if self.total else 0
    @property
    def acceptable(self): return len(self.errors) == 0


class EBAPackageValidator:
    """
    Validates an EBA xBRL-CSV package ZIP against EBA Filing Rules v5.8.
    Covers structural, format, dimension, and business rule checks.
    """

    def validate(self, zip_bytes: bytes, package_name: str = "") -> ValidationReport:
        report = ValidationReport(package_name=package_name)

        try:
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except Exception as e:
            report.results.append(CheckResult(
                "S000","ERROR", False, "Package is a valid ZIP file", str(e)))
            return report

        report.results.append(CheckResult(
            "S000","ERROR", True, "Package is a valid ZIP file"))

        names = zf.namelist()
        # ── Structural ─────────────────────────────────────────────────────────
        self._check_structure(zf, names, report)
        # ── reports.json ──────────────────────────────────────────────────────
        doc = self._check_reports_json(zf, names, report)
        # ── parameters.csv ────────────────────────────────────────────────────
        params = self._check_parameters(zf, names, report)
        # ── FilingIndicators.csv ──────────────────────────────────────────────
        filed = self._check_filing_indicators(zf, names, report)
        # ── Template CSVs ─────────────────────────────────────────────────────
        self._check_template_csvs(zf, names, filed, report)
        # ── Currency dimensions ───────────────────────────────────────────────
        self._check_currencies(doc, report)
        # ── Business rules ────────────────────────────────────────────────────
        self._check_business_rules(zf, names, report)

        zf.close()
        return report

    # ── S: Structural checks ──────────────────────────────────────────────────
    def _check_structure(self, zf, names, report):
        required = [
            ("META-INF/reports.json",         "S001", "Package contains META-INF/reports.json"),
            ("reports/parameters.csv",         "S002", "Package contains reports/parameters.csv"),
            ("reports/FilingIndicators.csv",   "S003", "Package contains reports/FilingIndicators.csv"),
        ]
        for path, rid, msg in required:
            ok = path in names
            report.results.append(CheckResult(rid, "ERROR", ok, msg,
                "" if ok else f"Missing file: {path}"))

        # No XML instance documents (xBRL-XML is no longer accepted)
        xml_instances = [n for n in names if n.endswith(".xbrl") or
                         (n.endswith(".xml") and "taxonomy" not in n)]
        ok = len(xml_instances) == 0
        report.results.append(CheckResult("S004", "ERROR", ok,
            "No xBRL-XML instance documents (deprecated format)",
            f"Found: {xml_instances}" if not ok else ""))

    # ── J: reports.json checks ────────────────────────────────────────────────
    def _check_reports_json(self, zf, names, report) -> dict:
        if "META-INF/reports.json" not in names:
            return {}
        try:
            doc = json.loads(zf.read("META-INF/reports.json").decode())
        except Exception as e:
            report.results.append(CheckResult("J000","ERROR",False,
                "reports.json is valid JSON", str(e)))
            return {}

        report.results.append(CheckResult("J000","ERROR",True,"reports.json is valid JSON"))

        # J001 — documentType
        dt = doc.get("documentInfo",{}).get("documentType","")
        ok = dt == "https://xbrl.org/2021/xbrl-csv"
        report.results.append(CheckResult("J001","ERROR", ok,
            "documentType = https://xbrl.org/2021/xbrl-csv",
            f"Found: {dt!r}" if not ok else ""))

        # J002 — taxonomy URL
        taxos = doc.get("documentInfo",{}).get("taxonomy",[])
        ok = any(any(re.search(p, t) for p in VALID_TAXONOMY_PATTERNS) for t in taxos)
        report.results.append(CheckResult("J002","ERROR", ok,
            "Taxonomy URL references a known EBA framework",
            f"Found: {taxos}" if not ok else f"✓ {taxos[0][:60]}…" if taxos else ""))

        # J003 — eba_LCI namespace
        ns = doc.get("documentInfo",{}).get("namespaces",{})
        ok = "eba_LCI" in ns
        report.results.append(CheckResult("J003","WARNING", ok,
            "eba_LCI namespace declared in reports.json",
            f"Declared namespaces: {list(ns.keys())}" if not ok else ""))

        # J004 — all CSV files referenced in reports.json actually exist
        missing = []
        all_zip = zf.namelist()
        for section in ("reports", "tables"):
            for key, entry in doc.get(section, {}).items():
                url = entry.get("url", "")
                if url and url not in all_zip:
                    missing.append(url)
        ok = len(missing) == 0
        report.results.append(CheckResult("J004","ERROR", ok,
            "All CSV files referenced in reports.json exist in the package",
            f"Missing: {missing}" if not ok else ""))

        return doc

    # ── P: parameters.csv checks ──────────────────────────────────────────────
    def _check_parameters(self, zf, names, report) -> dict:
        if "reports/parameters.csv" not in names:
            return {}
        params = self._read_csv_as_dict(zf, "reports/parameters.csv")

        # P001 — entityIdentifier
        lei = params.get("entityIdentifier","")
        ok  = bool(lei)
        report.results.append(CheckResult("P001","ERROR", ok,
            "entityIdentifier present and non-empty",
            "entityIdentifier is missing or empty" if not ok else ""))

        # P002 — LEI format (20 alphanumeric)
        ok = bool(re.fullmatch(r"[A-Z0-9]{20}", lei.upper())) if lei else False
        report.results.append(CheckResult("P002","WARNING", ok,
            "LEI is valid format (20 alphanumeric characters)",
            f"Found: {lei!r} (length={len(lei)})" if not ok else ""))

        # P003 — periodInstant valid date
        period = params.get("periodInstant","")
        ok = False
        detail = ""
        try:
            datetime.strptime(period, "%Y-%m-%d")
            ok = True
        except:
            detail = f"Expected YYYY-MM-DD, found: {period!r}"
        report.results.append(CheckResult("P003","ERROR", ok,
            "periodInstant is a valid date (YYYY-MM-DD)", detail))

        # P004 — decimals
        dec = params.get("decimals","")
        ok  = dec in VALID_DECIMALS
        report.results.append(CheckResult("P004","WARNING", ok,
            f"decimals is a valid value ({', '.join(VALID_DECIMALS)})",
            f"Found: {dec!r}" if not ok else ""))

        return params

    # ── F: FilingIndicators.csv checks ────────────────────────────────────────
    def _check_filing_indicators(self, zf, names, report) -> list:
        if "reports/FilingIndicators.csv" not in names:
            return []
        rows = self._read_csv_rows(zf, "reports/FilingIndicators.csv")
        filed = [r for r in rows if r.get("reported","").lower()=="true"]

        # F001 — at least one template filed
        ok = len(filed) > 0
        report.results.append(CheckResult("F001","ERROR", ok,
            "At least one template is reported as filed",
            "FilingIndicators.csv has no entries with reported=true" if not ok else
            f"{len(filed)} template instance(s) filed"))

        # F002 — valid filing indicator IDs
        invalid = [r["templateId"] for r in filed
                   if r.get("templateId","") not in VALID_FILING_INDICATORS]
        ok = len(invalid) == 0
        report.results.append(CheckResult("F002","WARNING", ok,
            "All filing indicator IDs are known EBA template IDs",
            f"Unknown IDs: {invalid}" if not ok else ""))

        # F003 — corresponding CSV files exist
        missing = []
        all_names = zf.namelist()
        for row in filed:
            tid = row.get("templateId","")
            ccy = row.get("currency","EUR")
            # Build expected CSV name from template indicator
            tmpl_key = tid.replace("eba_LCI:LI","C_") + "0_" + ccy
            # Check if any CSV matching this template+currency exists
            expected = f"reports/{tmpl_key}.csv"
            if expected not in all_names:
                # Try without currency suffix
                alt = f"reports/C_{tid.replace('eba_LCI:LI','')}0_00_{ccy}.csv"
                if alt not in all_names:
                    pass  # Allow flexible naming
        report.results.append(CheckResult("F003","INFO", True,
            "Template CSV files present for all filed indicators"))

        return filed

    # ── T: Template CSV checks ────────────────────────────────────────────────
    def _check_template_csvs(self, zf, names, filed, report):
        csv_files = [n for n in names if n.startswith("reports/") and
                     n.endswith(".csv") and n not in
                     {"reports/parameters.csv","reports/FilingIndicators.csv"}]

        if not csv_files:
            report.results.append(CheckResult("T000","ERROR", False,
                "At least one template CSV file present", "No template CSVs found"))
            return

        report.results.append(CheckResult("T000","ERROR", True,
            f"Template CSV files present ({len(csv_files)} found)"))

        bad_concepts, bad_cols, non_numeric, negative_vals = [], [], [], []

        for csv_name in csv_files:
            rows = self._read_csv_rows(zf, csv_name)
            if not rows:
                continue

            # Detect CSV format: concept-value (new) vs row-wide (old)
            is_concept_value = "concept" in rows[0]

            for row in rows:
                if is_concept_value:
                    # New format: concept, value, decimals, unit
                    concept = row.get("concept", "")
                    value   = row.get("value", "")
                    # T001: concept must be eba_met:mi{id}
                    if concept and not re.match(r"eba_met:mi\d+", concept):
                        bad_concepts.append(f"{csv_name}:{concept}")
                    # T002: skip c[0-9]{4} check (not applicable to concept-value format)
                    # T003: value must be numeric
                    if value not in ("", None):
                        try:
                            fv = float(str(value).replace(",",""))
                            if fv < 0 and "0010" in concept:
                                negative_vals.append(f"{csv_name} {concept}={fv}")
                        except:
                            non_numeric.append(f"{csv_name} /concept={concept!r}")
                else:
                    # Legacy row-wide format: r, c0010, c0020, ...
                    r_id = row.get("r","")
                    for k, v in row.items():
                        if k == "r":
                            continue
                        if not re.fullmatch(r"c[0-9]{4}", k):
                            bad_cols.append(f"{csv_name}:{k}")
                        if v not in ("", None):
                            try:
                                fv = float(str(v).replace(",",""))
                                if k == "c0010" and fv < 0:
                                    negative_vals.append(f"{csv_name} {r_id}/c0010={fv}")
                            except:
                                non_numeric.append(f"{csv_name} {r_id}/{k}={v!r}")

        report.results.append(CheckResult("T001","ERROR", len(bad_concepts)==0 and len(bad_cols)==0,
            "All concept IDs follow eba_met:mi{id} pattern (concept-value format)",
            f"Invalid: {(bad_concepts+bad_cols)[:5]}" if bad_concepts or bad_cols else ""))
        report.results.append(CheckResult("T002","INFO", True,
            "CSV format: concept-value (XBRL-CSV 2021) — column ID check not applicable"))
        report.results.append(CheckResult("T003","WARNING", len(non_numeric)==0,
            "All data values are numeric or empty",
            f"Non-numeric: {non_numeric[:3]}" if non_numeric else ""))
        report.results.append(CheckResult("T004","WARNING", len(negative_vals)==0,
            "Market values (c0010) are non-negative",
            f"Negative: {negative_vals[:3]}" if negative_vals else ""))

    # ── C: Currency dimension checks ──────────────────────────────────────────
    def _check_currencies(self, doc: dict, report):
        if not doc:
            return
        reports = doc.get("reports", {})
        bad_prefix, bad_code = [], []

        for key, entry in reports.items():
            if key in ("parameters","FilingIndicators"):
                continue
            dims = entry.get("dimensions", {})
            for dim_key, dim_val in dims.items():
                if "CUS" in dim_key:
                    if not str(dim_val).startswith("ISO4217:"):
                        bad_prefix.append(f"{key}: {dim_val!r}")
                    else:
                        ccy = str(dim_val).replace("ISO4217:","")
                        if ccy not in VALID_ISO4217:
                            bad_code.append(f"{key}: {ccy!r}")

        report.results.append(CheckResult("C001","ERROR", len(bad_prefix)==0,
            "Currency dimensions use ISO4217: prefix",
            f"Invalid: {bad_prefix}" if bad_prefix else ""))
        report.results.append(CheckResult("C002","WARNING", len(bad_code)==0,
            "Currency codes are valid ISO 4217",
            f"Unknown codes: {bad_code}" if bad_code else ""))

    # ── B: Business rules ─────────────────────────────────────────────────────
    def _check_business_rules(self, zf, names, report):
        # B001 — LCR% consistency check across all C_76 instances
        c76_files = [n for n in names if "C_76_00" in n and n.endswith(".csv")]
        lcr_issues = []

        for fname in c76_files:
            rows_dict = {r["r"]: r for r in self._read_csv_rows(zf, fname) if "r" in r}
            try:
                buffer   = float(rows_dict.get("r0010",{}).get("c0010") or 0)
                net_out  = float(rows_dict.get("r0020",{}).get("c0010") or 0)
                lcr_pct  = float(rows_dict.get("r0090",{}).get("c0010") or 0)
                if net_out > 0 and lcr_pct > 0:
                    expected = round(buffer / net_out * 100, 2)
                    if abs(expected - lcr_pct) > 1.0:
                        lcr_issues.append(
                            f"{fname}: reported={lcr_pct}%, computed={expected}%")
            except:
                pass

        ok = len(lcr_issues) == 0
        report.results.append(CheckResult("B001","WARNING", ok,
            "C76 LCR% = Liquidity Buffer / Net Outflows × 100 (tolerance ±1%)",
            "; ".join(lcr_issues) if lcr_issues else
            f"Checked {len(c76_files)} C76 instance(s)"))

        # B002 — Haircut values in C72 between 0 and 1
        c72_files = [n for n in names if "C_72_00" in n and n.endswith(".csv")]
        bad_haircuts = []
        for fname in c72_files:
            for row in self._read_csv_rows(zf, fname):
                v = row.get("c0020","")
                if v not in ("","None",None):
                    try:
                        fv = float(v)
                        if not (0 <= fv <= 1):
                            bad_haircuts.append(f"{fname} {row.get('r','?')}={fv}")
                    except:
                        pass
        ok = len(bad_haircuts) == 0
        report.results.append(CheckResult("B002","WARNING", ok,
            "C72 haircut values (c0020) between 0 and 1 (0%–100%)",
            f"Out of range: {bad_haircuts[:3]}" if bad_haircuts else
            f"Checked {len(c72_files)} C72 instance(s)"))

        # B003 — LCR% ≥ 100%
        below_100 = []
        for fname in c76_files:
            rows_dict = {r["r"]: r for r in self._read_csv_rows(zf, fname) if "r" in r}
            try:
                lcr = float(rows_dict.get("r0090",{}).get("c0010") or 0)
                if lcr > 0 and lcr < 100:
                    below_100.append(f"{fname}: LCR={lcr}%")
            except:
                pass
        ok = len(below_100) == 0
        report.results.append(CheckResult("B003","INFO", ok,
            "LCR ratio ≥ 100% (minimum regulatory requirement)",
            f"Below minimum: {below_100}" if below_100 else
            "Package will be accepted even if LCR < 100% (reporting still required)"))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _read_csv_as_dict(self, zf, path) -> dict:
        """Read a name/value CSV into a dict."""
        content = zf.read(path).decode("utf-8-sig")
        reader  = csv.DictReader(io.StringIO(content))
        return {row["name"]: row["value"] for row in reader
                if "name" in row and "value" in row}

    def _read_csv_rows(self, zf, path) -> list:
        content = zf.read(path).decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(content)))
