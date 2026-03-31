"""xBRL-CSV Generator — Streamlit UI (EBA + CSSF / multi-currency)"""
import streamlit as st, io, json, sys, os, pandas as pd
from datetime import date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from engine.validator      import EBAPackageValidator
from engine.reader         import EBAExcelReader
from engine.generator      import XBRLCSVGenerator
from engine.sample_creator import create_sample_workbook
from engine.definitions.lcr_templates import LCR_TEMPLATES

# ── CSSF / SEPA_IPR ──────────────────────────────────────────────────────────
from engine.definitions.ipr_templates  import IPR_TEMPLATES, EURO_AREA_FILED, NON_EURO_FILED
from engine.ipr_generator              import generate_ipr_multi_year_zips
from engine.ipr_reader                 import read_ipr_excel
from engine.ipr_sample_creator         import create_ipr_sample

CCY_FLAGS = {"EUR":"\U0001f1ea\U0001f1fa","USD":"\U0001f1fa\U0001f1f8",
             "GBP":"\U0001f1ec\U0001f1e7","CHF":"\U0001f1e8\U0001f1ed",
             "JPY":"\U0001f1ef\U0001f1f5","SEK":"\U0001f1f8\U0001f1ea",
             "NOK":"\U0001f1f3\U0001f1f4","DKK":"\U0001f1e9\U0001f1f0",
             "CAD":"\U0001f1e8\U0001f1e6","AUD":"\U0001f1e6\U0001f1fa",
             "CNY":"\U0001f1e8\U0001f1f3"}

st.set_page_config(page_title="xBRL-CSV Generator", page_icon="\U0001f4ca",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.eba-header{background:linear-gradient(135deg,#003399,#0055CC);padding:1.4rem 2rem;
  border-radius:12px;margin-bottom:1.2rem;color:white}
.eba-header h1{color:white;margin:0;font-size:1.7rem}
.eba-header p{color:#b8d0ff;margin:.3rem 0 0;font-size:.9rem}
.cssf-header{background:linear-gradient(135deg,#1a5c38,#2e7d52);padding:1.4rem 2rem;
  border-radius:12px;margin-bottom:1.2rem;color:white}
.cssf-header h1{color:white;margin:0;font-size:1.7rem}
.cssf-header p{color:#b8f0cf;margin:.3rem 0 0;font-size:.9rem}
.card{background:#f0f6ff;border-left:4px solid #003399;padding:.9rem 1.1rem;
  border-radius:6px;margin:.4rem 0;font-size:.88rem;color:#1a1a2e !important}
.card *{color:#1a1a2e !important}
.card code{background:#dce8ff !important;color:#003399 !important;
  padding:1px 5px;border-radius:3px}
.card-cssf{background:#f0fff6;border-left:4px solid #1a5c38;padding:.9rem 1.1rem;
  border-radius:6px;margin:.4rem 0;font-size:.88rem;color:#0a2e1a !important}
.card-cssf *{color:#0a2e1a !important}
.card-cssf code{background:#c8f0d8 !important;color:#1a5c38 !important;
  padding:1px 5px;border-radius:3px}
.ccy-pill{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.82rem;
  font-weight:700;margin:3px;border:1.5px solid;background:white}
.badge{display:inline-block;background:#003399;color:white;padding:1px 7px;
  border-radius:4px;font-size:.78rem;font-weight:700;margin:2px}
.badge-cssf{display:inline-block;background:#1a5c38;color:white;padding:1px 7px;
  border-radius:4px;font-size:.78rem;font-weight:700;margin:2px}
.filetree{font-family:monospace;background:#1e1e1e;color:#d4d4d4;padding:1rem;
  border-radius:8px;font-size:.83rem;line-height:1.65}
.wip-footer{
  position:fixed;bottom:0;left:0;right:0;z-index:999;
  background:linear-gradient(90deg,#001055,#003399,#001055);
  border-top:2px solid #0055CC;
  padding:.55rem 2rem;
  display:flex;justify-content:space-between;align-items:center;
}
.wip-badge{
  background:#ff6b00;color:white;padding:2px 10px;
  border-radius:10px;font-size:.78rem;font-weight:700;
  letter-spacing:.6px;margin-right:10px;
  animation:wippulse 2s infinite;
}
@keyframes wippulse{0%,100%{opacity:1}50%{opacity:.65}}
.wip-owner{color:#7ab8ff;font-weight:700}
.wip-right{color:#5580b0;font-size:.78rem;text-align:right}
</style>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### \u2699\ufe0f Report Parameters")
    entity_id = st.text_input("Entity LEI", value="7LTWFZYICNSX8D621K86")
    ref_date  = st.date_input("Reference Date", value=date(2025, 12, 31))
    base_ccy  = st.selectbox("Base Currency", ["EUR","USD","GBP","CHF"], index=0,
                              help="Consolidation currency of the institution")
    decimals  = st.selectbox("Decimal Accuracy", [-3,-6,0],
        format_func=lambda x:{-3:"-3 (thousands)",-6:"-6 (millions)",0:"0 (units)"}[x])
    st.divider()
    st.markdown("### \U0001f4cb LCR Templates")
    for _,t in LCR_TEMPLATES.items():
        st.markdown(f'<span class="badge">{t["template_code"]}</span> {t["name"]}',
                    unsafe_allow_html=True)
    st.divider()
    st.markdown("""### \U0001f4d0 Sheet Naming Rules
| Sheet name | Currency |
|---|---|
| `C 72.00` | EUR (default) |
| `C 72.00 USD` | USD |
| `C 72.00 GBP` | GBP |
| `C 72.00 CHF` | CHF |
""")
    st.divider()
    # ── CSSF / IPR params ─────────────────────────────────────────────────────
    st.markdown("### \U0001f1f1\U0001f1fa CSSF — SEPA_IPR")
    ipr_euro  = st.checkbox("Euro-area PSP (LU/FR/DE…)", value=True, key="ipr_euro")
    ipr_years = st.multiselect("Reference years",
                               [2022,2023,2024,2025],
                               default=[2022,2023,2024,2025],
                               key="ipr_years")
    ipr_entity_type = st.selectbox("Entity type",
        ["Bank (CRD)","Payment Institution (PSD2)","E-money Institution (EMD2)"],
        key="ipr_entity_type")
    ipr_dec = st.number_input("Decimals (IPR)", value=0, key="ipr_dec")
    st.caption("First remittance: **9 April 2026**")

# ── TOP-LEVEL TABS ────────────────────────────────────────────────────────────
tab_eba, tab_cssf = st.tabs(["\U0001f3e6 EBA Reporting", "\U0001f1f1\U0001f1fa CSSF Reporting"])

# ══════════════════════════════════════════════════════════════════════════════
# EBA REPORTING
# ══════════════════════════════════════════════════════════════════════════════
with tab_eba:
    st.markdown("""<div class="eba-header">
      <h1>\U0001f3e6 xBRL-CSV Generator</h1>
      <p>LCR Delegated Act \u00b7 C72\u2013C76 \u00b7 Framework 4.2 \u00b7 eba_met concept IDs \u00b7 EBA Filing Rules v5.8</p>
    </div>""", unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["\U0001f4e4 Convert", "\U0001f4e5 Sample Template",
                               "\U0001f50d Validate Package", "\U0001f4d6 Documentation"])

    # ══════════════════════════════════════════════════════════════════════════
    # EBA TAB 1 — CONVERT
    # ══════════════════════════════════════════════════════════════════════════
    with t1:
        st.markdown("### Upload your filled EBA Excel template")
        c1, c2 = st.columns([2,1])
        with c1:
            uploaded = st.file_uploader("Choose .xlsx file", type=["xlsx"])
        with c2:
            st.markdown('<div class="card"><strong>Multi-currency support</strong><br>'
                        'The engine auto-detects currencies from sheet names.<br>'
                        'Add <code>C 72.00 USD</code>, <code>C 72.00 GBP</code>\u2026'
                        ' alongside the base <code>C 72.00</code> sheet.</div>',
                        unsafe_allow_html=True)

        if uploaded:
            st.divider()
            try:
                with st.spinner("Reading Excel\u2026"):
                    reader = EBAExcelReader()
                    data   = reader.read(io.BytesIO(uploaded.read()))

                if not data:
                    st.error("No matching sheets found. Check sheet names.")
                    st.stop()

                currencies  = sorted(set(v["currency"] for v in data.values()),
                                     key=lambda x:(x!=base_ccy, x))
                templates   = sorted(set(v["template_key"] for v in data.values()))

                st.markdown("#### \u2705 Detected currencies")
                ccy_html = ""
                colors = {"EUR":"#003399","USD":"#1a7a1a","GBP":"#7a1a1a",
                          "CHF":"#7a5a00","JPY":"#6a006a"}
                for c in currencies:
                    col  = colors.get(c, "#444")
                    flag = CCY_FLAGS.get(c,"")
                    ccy_html += (f'<span class="ccy-pill" style="color:{col};border-color:{col}">'
                                 f'{flag} {c}</span>')
                st.markdown(ccy_html + "<br>", unsafe_allow_html=True)

                st.markdown("#### \U0001f4ca Data points per template \u00d7 currency")
                matrix = defaultdict(dict)
                for key, v in data.items():
                    matrix[v["template_code"]][v["currency"]] = len(v["data_points"])
                df = pd.DataFrame(matrix).T.fillna(0).astype(int)
                df.index.name = "Template"
                df["TOTAL"] = df.sum(axis=1)
                st.dataframe(df.style.highlight_max(axis=1, color="#D0E8FF"),
                             use_container_width=True)

                st.divider()

                with st.spinner("Generating xBRL-CSV package\u2026"):
                    gen     = XBRLCSVGenerator(entity_id, ref_date.isoformat(),
                                               decimals, base_ccy)
                    zipdata = gen.generate_package(data)
                    preview = gen.get_preview(data)

                total_pts = sum(len(v["data_points"]) for v in data.values())
                st.success(f"\u2705 Package ready \u2014 {len(currencies)} currencies \u00b7 "
                           f"{len(data)} instances \u00b7 {total_pts} data points \u00b7 "
                           f"{len(zipdata)/1024:.1f} KB")

                fname = f"XBRL_LCR_{entity_id[:8]}_{ref_date:%Y%m%d}_{'_'.join(currencies)}.zip"
                cd, ci = st.columns([1,2])
                with cd:
                    st.download_button("\u2b07\ufe0f Download XBRL-CSV Package", zipdata, fname,
                                       "application/zip", use_container_width=True, type="primary")
                with ci:
                    st.markdown(
                        f'<div class="card">\U0001f4e6 <b>{fname}</b><br>'
                        f'Entity: <code>{entity_id}</code><br>'
                        f'Period: <code>{ref_date}</code> \u00b7 Base CCY: <code>{base_ccy}</code><br>'
                        f'Currencies: <code>{", ".join(currencies)}</code></div>',
                        unsafe_allow_html=True)

                st.markdown("#### \U0001f4c1 Package Contents")
                for fname_p, content in preview.items():
                    with st.expander(f"\U0001f4c4 `{fname_p}`"):
                        if fname_p.endswith(".json"):
                            st.json(json.loads(content))
                        else:
                            st.code(content, language="text")

            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
        else:
            st.info("Upload a file above, or grab a multi-currency sample from the **Sample Template** tab.")

    # ══════════════════════════════════════════════════════════════════════════
    # EBA TAB 2 — SAMPLE
    # ══════════════════════════════════════════════════════════════════════════
    with t2:
        st.markdown("### Generate a multi-currency sample template")
        st.markdown("Choose which currencies to include. The workbook will contain "
                    "one set of C72\u2013C76 sheets per currency.")

        available = ["EUR","USD","GBP","CHF","JPY","SEK","NOK","DKK","CAD"]
        selected  = st.multiselect("Currencies to include",
                                   available, default=["EUR","USD","GBP"],
                                   help="EUR is mandatory (base currency)")
        if "EUR" not in selected:
            selected = ["EUR"] + selected

        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"**Will generate:** {len(selected)} \u00d7 5 = "
                        f"**{len(selected)*5} sheets**")
            for c in selected:
                flag = CCY_FLAGS.get(c,"")
                st.markdown(f"- {flag} `{c}` \u2192 sheets: "
                            + ", ".join(f"`C 72.00{(' '+c if c!='EUR' else '')}`"[:15]
                                        for _ in [""])
                            + f"C 72.00{'  '+c if c!='EUR' else ''} \u2026 C 76.00{'  '+c if c!='EUR' else ''}")
        with cb:
            st.markdown("**Sheet naming convention:**")
            st.code("C 72.00        \u2190 EUR (no suffix)\n"
                    "C 72.00 USD    \u2190 USD\n"
                    "C 72.00 GBP    \u2190 GBP\n"
                    "C 73.00        \u2190 EUR\n"
                    "C 73.00 USD    \u2190 USD\n"
                    "\u2026")

        if st.button("\U0001f528 Generate Multi-Currency Template", type="primary"):
            with st.spinner(f"Building workbook with {selected}\u2026"):
                buf = create_sample_workbook(
                    currencies=selected,
                    entity_lei=entity_id,
                    ref_date=ref_date.isoformat(),
                    base_currency=base_ccy,
                )
                xb = buf.getvalue()
            ccy_str = "_".join(selected)
            st.success(f"\u2705 {len(selected)*5} sheets created!")
            st.download_button(
                f"\u2b07\ufe0f Download EBA_LCR_Sample_{ccy_str}.xlsx", xb,
                f"EBA_LCR_Sample_{ccy_str}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, type="primary")

    # ══════════════════════════════════════════════════════════════════════════
    # EBA TAB 3 — VALIDATE
    # ══════════════════════════════════════════════════════════════════════════
    with t3:
        st.markdown("### Pre-submission validation")
        st.markdown(
            "Upload a generated **xBRL-CSV package (.zip)** to check if it will be "
            "accepted by the EBA / NCA filing system. Covers **structural**, "
            "**format**, **dimension** and **business rule** checks per "
            "EBA Filing Rules v5.8.")

        st.info("\u2139\ufe0f This is a pre-flight simulation \u2014 it does not submit to EBA/EUCLID. "
                "No data leaves this application.", icon="\u2139\ufe0f")

        val_file = st.file_uploader("Upload XBRL-CSV package (.zip)", type=["zip"],
                                     key="validator_upload")
        if val_file:
            st.divider()
            with st.spinner("Running validation checks\u2026"):
                validator = EBAPackageValidator()
                rpt       = validator.validate(val_file.read(), val_file.name)

            n_err  = len(rpt.errors)
            n_warn = len(rpt.warnings)
            n_info = len(rpt.infos)

            if rpt.acceptable:
                verdict_color = "#1a7a1a" if n_warn == 0 else "#7a5a00"
                verdict_icon  = "\u2705" if n_warn == 0 else "\u26a0\ufe0f"
                verdict_text  = ("LIKELY TO BE ACCEPTED" if n_warn == 0
                                 else "LIKELY ACCEPTED \u2014 WITH WARNINGS")
                verdict_sub   = ("No errors or warnings detected."
                                 if n_warn == 0
                                 else f"{n_warn} warning(s) may require attention.")
            else:
                verdict_color = "#7a1a1a"
                verdict_icon  = "\u274c"
                verdict_text  = "WILL BE REJECTED"
                verdict_sub   = f"{n_err} critical error(s) must be fixed before submission."

            st.markdown(f"""
            <div style="background:{verdict_color}22;border:2px solid {verdict_color};
                 border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:1rem;text-align:center">
              <div style="font-size:2rem">{verdict_icon}</div>
              <div style="font-size:1.3rem;font-weight:700;color:{verdict_color}">{verdict_text}</div>
              <div style="color:#555;margin-top:.3rem">{verdict_sub}</div>
            </div>""", unsafe_allow_html=True)

            score     = rpt.score
            bar_color = "#1a7a1a" if score>=90 else "#7a5a00" if score>=70 else "#7a1a1a"
            st.markdown(f"""
            <div style="margin:.5rem 0 1.2rem">
              <div style="display:flex;justify-content:space-between;font-size:.85rem;
                   font-weight:600;margin-bottom:4px">
                <span>Validation Score</span>
                <span style="color:{bar_color}">{rpt.passed_count}/{rpt.total} checks passed ({score}%)</span>
              </div>
              <div style="background:#eee;border-radius:8px;height:14px;overflow:hidden">
                <div style="background:{bar_color};width:{score}%;height:100%;
                     border-radius:8px;transition:width .5s"></div>
              </div>
            </div>""", unsafe_allow_html=True)

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("\u2705 Passed",   rpt.passed_count)
            mc2.metric("\u274c Errors",   n_err,  delta=f"-{n_err}"  if n_err  else None, delta_color="inverse")
            mc3.metric("\u26a0\ufe0f Warnings", n_warn, delta=f"-{n_warn}" if n_warn else None, delta_color="inverse")
            mc4.metric("\u2139\ufe0f Info",     n_info)

            st.divider()
            st.markdown("#### Detailed Check Results")

            LEVEL_CFG = {
                "ERROR":   {"icon":"\u274c", "color":"#7a1a1a", "bg":"#fff0f0"},
                "WARNING": {"icon":"\u26a0\ufe0f", "color":"#7a5a00", "bg":"#fffbf0"},
                "INFO":    {"icon":"\u2139\ufe0f", "color":"#1a4a7a", "bg":"#f0f6ff"},
            }
            categories = {
                "S": "\U0001f4e6 Structure",
                "J": "\U0001f4c4 reports.json",
                "P": "\U0001f511 parameters.csv",
                "F": "\U0001f4cb Filing Indicators",
                "T": "\U0001f4ca Template CSVs",
                "C": "\U0001f4b1 Currency Dimensions",
                "B": "\U0001f4d0 Business Rules",
            }
            for prefix, cat_label in categories.items():
                cat_results = [r for r in rpt.results if r.rule_id.startswith(prefix)]
                if not cat_results:
                    continue
                cat_pass  = sum(1 for r in cat_results if r.passed)
                cat_total = len(cat_results)
                cat_ok    = cat_pass == cat_total

                status_icon = "\u2705" if cat_ok else "\u274c" if any(not r.passed and r.level=='ERROR' for r in cat_results) else "\u26a0\ufe0f"
                with st.expander(
                    f"{status_icon} {cat_label} \u2014 {cat_pass}/{cat_total}",
                    expanded=not cat_ok):

                    for res in cat_results:
                        cfg    = LEVEL_CFG[res.level]
                        icon   = "\u2705" if res.passed else cfg["icon"]
                        bg     = "#f0fff0" if res.passed else cfg["bg"]
                        color  = "#1a7a1a" if res.passed else cfg["color"]
                        detail = (f'<div style="font-size:.8rem;color:#666;margin-top:2px">'
                                  f'\U0001f4ac {res.detail}</div>' if res.detail else "")
                        st.markdown(f"""
                        <div style="background:{bg};border-left:3px solid {color};
                             padding:.5rem .8rem;border-radius:4px;margin:4px 0">
                          <span style="font-weight:600;color:{color}">{icon} [{res.rule_id}]</span>
                          <span style="margin-left:.5rem">{res.message}</span>
                          {detail}
                        </div>""", unsafe_allow_html=True)

            failed = [r for r in rpt.results if not r.passed and r.level=="ERROR"]
            if failed:
                st.divider()
                st.markdown("#### \U0001f527 How to fix the errors")
                FIX_GUIDE = {
                    "S001":"Add META-INF/reports.json to your ZIP. Use the Convert tab to regenerate.",
                    "S002":"Add reports/parameters.csv. Use the Convert tab to regenerate.",
                    "S003":"Add reports/FilingIndicators.csv. Use the Convert tab to regenerate.",
                    "S004":"Remove .xbrl/.xml files \u2014 EBA only accepts xBRL-CSV format since March 2026.",
                    "J001":'Set documentType to exactly "https://xbrl.org/2021/xbrl-csv".',
                    "J002":"Taxonomy URL must point to an EBA framework (eba.europa.eu/eu/fr/xbrl/crr/).",
                    "J004":"Ensure every URL in reports.json has a matching CSV file in the ZIP.",
                    "P001":"Add entityIdentifier row to parameters.csv.",
                    "P003":"Set periodInstant to YYYY-MM-DD format (e.g. 2025-12-31).",
                    "F001":"Add at least one row with reported=true to FilingIndicators.csv.",
                    "T001":"Row IDs must follow r[0-9]{4} format (e.g. r0010, r0020).",
                    "T002":"Column IDs must follow c[0-9]{4} format (e.g. c0010, c0020).",
                    "C001":"Currency dimension values must use ISO4217: prefix (e.g. ISO4217:EUR).",
                }
                for res in failed:
                    fix = FIX_GUIDE.get(res.rule_id,
                        "Use the Convert tab to regenerate the package from a corrected template.")
                    st.markdown(f"- **[{res.rule_id}] {res.message}**  \u2192  {fix}")

    # ══════════════════════════════════════════════════════════════════════════
    # EBA TAB 4 — DOCS
    # ══════════════════════════════════════════════════════════════════════════
    with t4:
        st.markdown("### Architecture & Multi-Currency Reference")
        da, db = st.columns(2)
        with da:
            st.markdown("""
**Multi-currency flow:**

1. Business fills `C 72.00` (EUR) + `C 72.00 USD` + `C 72.00 GBP`\u2026  
2. `EBAExcelReader.read()` auto-detects currencies from sheet names  
3. Returns flat dict: `C_72_00_EUR`, `C_72_00_USD`, `C_72_00_GBP`\u2026  
4. `XBRLCSVGenerator` adds `eba_LCI:CUS \u2192 ISO4217:XXX` dimension  
   to each CSV entry in `reports.json`  
5. Each currency gets its own CSV: `C_72_00_USD.csv`

**EBA regulatory rule:**  
Any currency \u2265 5% of total liabilities must be reported separately  
(Art. 415(2) CRR). All instances go in **one single ZIP**.
""")
        with db:
            st.markdown('<div class="filetree">' +
                "\U0001f4e6 XBRL_LCR_EUR_USD_GBP.zip<br>"
                "\u251c\u2500\u2500 \U0001f4c1 META-INF/<br>"
                "\u2502   \u2514\u2500\u2500 reports.json<br>"
                "\u2502   \u00a0\u00a0\u00a0\u00a0<span style='color:#6a9955'>\u2190 eba_LCI:CUS: ISO4217:USD\u2026</span><br>"
                "\u2514\u2500\u2500 \U0001f4c1 reports/<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 parameters.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 FilingIndicators.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 C_72_00_EUR.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 C_72_00_USD.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 C_72_00_GBP.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 C_73_00_EUR.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u251c\u2500\u2500 C_73_00_USD.csv<br>"
                "\u00a0\u00a0\u00a0\u00a0\u2514\u2500\u2500 \u2026"
                '</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Template \u00d7 Currency Mapping Table")
        rows_doc = []
        for key, t in LCR_TEMPLATES.items():
            for ccy in ["EUR","USD","GBP"]:
                sname = t["template_code"] if ccy=="EUR" else f"{t['template_code']} {ccy}"
                csv_f = f"{key}_{ccy}.csv"
                dim   = f"eba_LCI:CUS = ISO4217:{ccy}"
                rows_doc.append({"Template":t["template_code"],"Currency":ccy,
                                 "Excel Sheet":sname,"CSV File":csv_f,
                                 "XBRL Dimension":dim})
        st.dataframe(pd.DataFrame(rows_doc), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# CSSF REPORTING
# ══════════════════════════════════════════════════════════════════════════════
with tab_cssf:
    st.markdown("""<div class="cssf-header">
      <h1>\U0001f1f1\U0001f1fa CSSF Reporting</h1>
      <p>Luxembourg NCA \u00b7 SEPA_IPR \u00b7 EBA RF 4.2 \u00b7 ITS Annex I \u00b7 First remittance: 9 April 2026</p>
    </div>""", unsafe_allow_html=True)

    cs1, cs2 = st.tabs(["\U0001f4e1 SEPA_IPR", "\U0001f51c Future modules"])

    # ══════════════════════════════════════════════════════════════════════════
    # CSSF TAB 1 — SEPA_IPR
    # ══════════════════════════════════════════════════════════════════════════
    with cs1:
        st.markdown("### SEPA_IPR — Instant Payments Reporting")

        # ── Context banner ────────────────────────────────────────────────────
        ia, ib, ic, id_ = st.columns(4)
        ia.metric("Reference years", "2022\u20132025")
        ib.metric("Templates (euro-area PSP)", "4")
        ic.metric("First remittance", "9 Apr 2026")
        id_.metric("Entity types", "Banks + PIs + EMIs")

        st.divider()

        if ipr_euro:
            st.markdown('<div class="card-cssf">\U0001f1ea\U0001f1fa <b>Euro-area PSP selected</b> \u2014 '
                        'Templates <code>S 01.01</code>, <code>S 02.01</code>, <code>S 03.00</code>, '
                        '<code>S 04.00</code> will be filed. '
                        '<code>S 01.02</code> and <code>S 02.02</code> (non-euro) set to <code>filed: false</code>.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="card-cssf">\U0001f310 <b>Non-euro-area PSP</b> \u2014 '
                        'All 6 templates will be filed (national currency + EUR variants).</div>',
                        unsafe_allow_html=True)

        # ── Template overview ─────────────────────────────────────────────────
        st.markdown("#### \U0001f4cb Template scope (ITS Annex I)")
        tpl_rows = []
        for tpl_code, tpl in IPR_TEMPLATES.items():
            ind  = tpl["xbrl_filing_indicator"]
            filed = ind in (EURO_AREA_FILED if ipr_euro else NON_EURO_FILED)
            tpl_rows.append({
                "Template":  tpl_code,
                "Filing indicator": ind,
                "Content": {
                    "S 01.01":"Number & value of CTs — national currency (all PSPs)",
                    "S 01.02":"Number & value of CTs — EUR (non-euro MS only)",
                    "S 02.01":"Charges for CTs — national currency (all PSPs)",
                    "S 02.02":"Charges for CTs — EUR (non-euro MS only)",
                    "S 03.00":"Payment accounts & total charges (all PSPs)",
                    "S 04.00":"Rejected SCT Inst (all PSPs)",
                }.get(tpl_code,""),
                "Filed": "\u2705 Yes" if filed else "\u274c N/A",
            })
        st.dataframe(pd.DataFrame(tpl_rows), use_container_width=True, hide_index=True)

        st.divider()

        # ── Step 1: Sample ────────────────────────────────────────────────────
        se1, se2 = st.columns(2)

        with se1:
            st.markdown("#### 1 \u00b7 Download sample template")
            st.markdown("Generates a styled Excel workbook with one data-entry sheet "
                        "per reference year \u00d7 template. Yellow cells = fill in.")
            if st.button("\U0001f528 Generate IPR Excel template", key="ipr_sample_btn"):
                if not entity_id or len(entity_id) != 20:
                    st.error("Set a valid 20-character LEI in the sidebar.")
                elif not ipr_years:
                    st.error("Select at least one reference year in the sidebar.")
                else:
                    with st.spinner("Building workbook\u2026"):
                        xlsx = create_ipr_sample(entity_id, sorted(ipr_years),
                                                 is_euro_area=ipr_euro)
                    st.success(f"\u2705 {len(ipr_years) * (4 if ipr_euro else 6)} sheets generated")
                    st.download_button(
                        f"\u2b07\ufe0f IPR_Sample_{entity_id[:8]}.xlsx",
                        data=xlsx,
                        file_name=f"IPR_Sample_{entity_id}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="ipr_sample_dl",
                        use_container_width=True,
                        type="primary",
                    )

        # ── Step 2: Generate ZIPs ─────────────────────────────────────────────
        with se2:
            st.markdown("#### 2 \u00b7 Upload filled template \u2192 Generate ZIPs")
            st.markdown("Upload the filled workbook. One XBRL-CSV ZIP is generated "
                        "per reference year (submit each to CSSF eDesk separately).")
            ipr_up = st.file_uploader("Upload filled IPR Excel",
                                      type=["xlsx"], key="ipr_upload")
            if ipr_up and st.button("\U0001f4e6 Generate IPR ZIPs", key="ipr_gen_btn"):
                if not entity_id or len(entity_id) != 20:
                    st.error("Set a valid 20-character LEI in the sidebar.")
                elif not ipr_years:
                    st.error("Select at least one reference year in the sidebar.")
                else:
                    try:
                        with st.spinner("Reading Excel and generating ZIPs\u2026"):
                            filed   = EURO_AREA_FILED if ipr_euro else NON_EURO_FILED
                            data_by = read_ipr_excel(ipr_up, sorted(ipr_years))
                            zips    = generate_ipr_multi_year_zips(
                                lei=entity_id,
                                years=sorted(ipr_years),
                                decimals=int(ipr_dec),
                                data_by_year=data_by,
                                filed_indicators=filed,
                            )
                        st.success(f"\u2705 {len(zips)} XBRL-CSV ZIP(s) ready for CSSF eDesk")

                        # Matrix summary
                        summary = []
                        for yr, zb in zips.items():
                            t_count = len(data_by.get(yr, {}))
                            summary.append({"Year": yr,
                                            "Templates with data": t_count,
                                            "ZIP size": f"{len(zb)/1024:.1f} KB"})
                        st.dataframe(pd.DataFrame(summary), use_container_width=True,
                                     hide_index=True)

                        for yr, zb in sorted(zips.items()):
                            fname_z = f"SEPA_IPR_{entity_id}_{yr}1231.zip"
                            st.download_button(
                                f"\u2b07\ufe0f {fname_z}",
                                data=zb,
                                file_name=fname_z,
                                mime="application/zip",
                                key=f"ipr_dl_{yr}",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(f"Error generating ZIPs: {e}")
                        st.exception(e)

        st.divider()

        # ── Step 3: Submission checklist ──────────────────────────────────────
        st.markdown("#### 3 \u00b7 CSSF submission checklist")
        ca_sub, cb_sub = st.columns([1,1])
        with ca_sub:
            st.markdown("""
| Step | Action |
|------|--------|
| 1 | Login to [CSSF eDesk](https://edesk.apps.cssf.lu) |
| 2 | Select reporting type **SEPA_IPR** |
| 3 | Upload each ZIP separately (one per reference year) |
| 4 | Check the feedback file within 24h |
| \u26a0\ufe0f | First remittance covers **4 years at once** (2022\u20132025) |
""")
        with cb_sub:
            st.markdown('<div class="filetree">' +
                "One ZIP per year:<br><br>"
                "SEPA_IPR_{LEI}_20221231.zip<br>"
                "SEPA_IPR_{LEI}_20231231.zip<br>"
                "SEPA_IPR_{LEI}_20241231.zip<br>"
                "SEPA_IPR_{LEI}_20251231.zip<br><br>"
                "<span style='color:#6a9955'>Each ZIP: META-INF/ + reports/</span>"
                '</div>', unsafe_allow_html=True)

        # ── Package structure expander ─────────────────────────────────────────
        with st.expander("\U0001f4c1 ZIP package structure (per year)"):
            st.code("""SEPA_IPR_{LEI}_{YEAR}1231.zip
\u251c\u2500\u2500 META-INF/
\u2502   \u251c\u2500\u2500 reports.json          \u2190 taxonomy entry point + table templates
\u2502   \u2514\u2500\u2500 reportPackage.json    \u2190 XBRL report package manifest
\u2514\u2500\u2500 reports/
    \u251c\u2500\u2500 parameters.csv        \u2190 LEI, periodInstant, decimals
    \u251c\u2500\u2500 FilingIndicators.csv  \u2190 true/false per template
    \u251c\u2500\u2500 S_01_01_a.csv         \u2190 Volumes (national currency)
    \u251c\u2500\u2500 S_02_01_a.csv         \u2190 Charges
    \u251c\u2500\u2500 S_03_00_a.csv         \u2190 Accounts
    \u2514\u2500\u2500 S_04_00_a.csv         \u2190 Rejections""", language="text")

    # ══════════════════════════════════════════════════════════════════════════
    # CSSF TAB 2 — FUTURE
    # ══════════════════════════════════════════════════════════════════════════
    with cs2:
        st.info("\U0001f6a7 Future CSSF-specific modules will appear here (e.g. IORP, PSD2 ICT)")

# ── WIP FOOTER ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="wip-footer">
  <div style="display:flex;align-items:center;gap:8px">
    <span class="wip-badge">\u2699\ufe0f WORK IN PROGRESS</span>
    <span style="color:#b8d0ff;font-size:.85rem">
      xBRL-CSV Generator &nbsp;\u00b7&nbsp;
      Owner: <span class="wip-owner">Cl\u00e9ment Denorme</span>
    </span>
  </div>
  <div class="wip-right">
    EBA COREP 4.2 \u00b7 LCR DA \u00b7 C72\u2013C76 \u00b7 CSSF SEPA_IPR \u00b7 eba_met 5,112 mappings
  </div>
</div>
""", unsafe_allow_html=True)
