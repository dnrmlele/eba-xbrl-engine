
"""EBA XBRL-CSV Engine — Streamlit UI (multi-currency)"""
import streamlit as st, io, json, sys, os, pandas as pd
from datetime import date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from engine.validator      import EBAPackageValidator
from engine.reader         import EBAExcelReader
from engine.generator      import XBRLCSVGenerator
from engine.sample_creator import create_sample_workbook
from engine.definitions.lcr_templates import LCR_TEMPLATES

CCY_FLAGS = {"EUR":"🇪🇺","USD":"🇺🇸","GBP":"🇬🇧","CHF":"🇨🇭","JPY":"🇯🇵",
             "SEK":"🇸🇪","NOK":"🇳🇴","DKK":"🇩🇰","CAD":"🇨🇦","AUD":"🇦🇺","CNY":"🇨🇳"}

st.set_page_config(page_title="EBA XBRL-CSV Engine", page_icon="🏦",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.eba-header{background:linear-gradient(135deg,#003399,#0055CC);padding:1.4rem 2rem;
  border-radius:12px;margin-bottom:1.2rem;color:white}
.eba-header h1{color:white;margin:0;font-size:1.7rem}
.eba-header p{color:#b8d0ff;margin:.3rem 0 0;font-size:.9rem}
.card{background:#f0f6ff;border-left:4px solid #003399;padding:.9rem 1.1rem;
  border-radius:6px;margin:.4rem 0;font-size:.88rem;color:#1a1a2e !important}
.card *{color:#1a1a2e !important}
.card code{background:#dce8ff !important;color:#003399 !important;
  padding:1px 5px;border-radius:3px}
.ccy-pill{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.82rem;
  font-weight:700;margin:3px;border:1.5px solid;background:white}
.badge{display:inline-block;background:#003399;color:white;padding:1px 7px;
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

st.markdown("""<div class="eba-header">
  <h1>🏦 EBA XBRL-CSV Reporting Engine</h1>
  <p>LCR Delegated Act · C72–C76 · Framework 4.2 · eba_met concept IDs · EBA Filing Rules v5.8</p>
</div>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Report Parameters")
    entity_id = st.text_input("Entity LEI", value="7LTWFZYICNSX8D621K86")
    ref_date  = st.date_input("Reference Date", value=date(2025, 12, 31))
    base_ccy  = st.selectbox("Base Currency", ["EUR","USD","GBP","CHF"], index=0,
                              help="Consolidation currency of the institution")
    decimals  = st.selectbox("Decimal Accuracy", [-3,-6,0],
        format_func=lambda x:{-3:"-3 (thousands)",-6:"-6 (millions)",0:"0 (units)"}[x])
    st.divider()
    st.markdown("### 📋 Templates")
    for _,t in LCR_TEMPLATES.items():
        st.markdown(f'<span class="badge">{t["template_code"]}</span> {t["name"]}',
                    unsafe_allow_html=True)
    st.divider()
    st.markdown("""### 📐 Sheet Naming Rules
| Sheet name | Currency |
|---|---|
| `C 72.00` | EUR (default) |
| `C 72.00 USD` | USD |
| `C 72.00 GBP` | GBP |
| `C 72.00 CHF` | CHF |
""")

# ── TABS ──────────────────────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs(["📤 Convert", "📥 Sample Template", "🔍 Validate Package", "📖 Documentation"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CONVERT
# ══════════════════════════════════════════════════════════════════════════════
with t1:
    st.markdown("### Upload your filled EBA Excel template")
    c1, c2 = st.columns([2,1])
    with c1:
        uploaded = st.file_uploader("Choose .xlsx file", type=["xlsx"])
    with c2:
        st.markdown('<div class="card"><strong>Multi-currency support</strong><br>'
                    'The engine auto-detects currencies from sheet names.<br>'
                    'Add <code>C 72.00 USD</code>, <code>C 72.00 GBP</code>…'
                    ' alongside the base <code>C 72.00</code> sheet.</div>',
                    unsafe_allow_html=True)

    if uploaded:
        st.divider()
        try:
            with st.spinner("Reading Excel…"):
                reader = EBAExcelReader()
                data   = reader.read(io.BytesIO(uploaded.read()))

            if not data:
                st.error("No matching sheets found. Check sheet names.")
                st.stop()

            # ── Currency summary ──────────────────────────────────────────────
            currencies  = sorted(set(v["currency"] for v in data.values()),
                                 key=lambda x:(x!=base_ccy, x))
            templates   = sorted(set(v["template_key"] for v in data.values()))

            st.markdown("#### ✅ Detected currencies")
            ccy_html = ""
            colors = {"EUR":"#003399","USD":"#1a7a1a","GBP":"#7a1a1a",
                      "CHF":"#7a5a00","JPY":"#6a006a"}
            for c in currencies:
                col = colors.get(c, "#444")
                flag = CCY_FLAGS.get(c,"")
                ccy_html += (f'<span class="ccy-pill" style="color:{col};border-color:{col}">'
                             f'{flag} {c}</span>')
            st.markdown(ccy_html + "<br>", unsafe_allow_html=True)

            # ── Data point matrix ─────────────────────────────────────────────
            st.markdown("#### 📊 Data points per template × currency")
            matrix = defaultdict(dict)
            for key, v in data.items():
                matrix[v["template_code"]][v["currency"]] = len(v["data_points"])
            df = pd.DataFrame(matrix).T.fillna(0).astype(int)
            df.index.name = "Template"
            df["TOTAL"] = df.sum(axis=1)
            st.dataframe(df.style.highlight_max(axis=1, color="#D0E8FF"),
                         use_container_width=True)

            st.divider()

            # ── Generate package ──────────────────────────────────────────────
            with st.spinner("Generating xBRL-CSV package…"):
                gen     = XBRLCSVGenerator(entity_id, ref_date.isoformat(),
                                           decimals, base_ccy)
                zipdata = gen.generate_package(data)
                preview = gen.get_preview(data)

            total_pts = sum(len(v["data_points"]) for v in data.values())
            st.success(f"✅ Package ready — {len(currencies)} currencies · "
                       f"{len(data)} instances · {total_pts} data points · "
                       f"{len(zipdata)/1024:.1f} KB")

            fname = f"XBRL_LCR_{entity_id[:8]}_{ref_date:%Y%m%d}_{'_'.join(currencies)}.zip"
            cd, ci = st.columns([1,2])
            with cd:
                st.download_button("⬇️ Download XBRL-CSV Package", zipdata, fname,
                                   "application/zip", use_container_width=True, type="primary")
            with ci:
                st.markdown(
                    f'<div class="card">📦 <b>{fname}</b><br>'
                    f'Entity: <code>{entity_id}</code><br>'
                    f'Period: <code>{ref_date}</code> · Base CCY: <code>{base_ccy}</code><br>'
                    f'Currencies: <code>{", ".join(currencies)}</code></div>',
                    unsafe_allow_html=True)

            st.markdown("#### 📁 Package Contents")
            for fname_p, content in preview.items():
                with st.expander(f"📄 `{fname_p}`"):
                    if fname_p.endswith(".json"):
                        st.json(json.loads(content))
                    else:
                        st.code(content, language="text")

        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)
    else:
        st.info("Upload a file above, or grab a multi-currency sample from the **Sample Template** tab.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SAMPLE
# ══════════════════════════════════════════════════════════════════════════════
with t2:
    st.markdown("### Generate a multi-currency sample template")
    st.markdown("Choose which currencies to include. The workbook will contain "
                "one set of C72–C76 sheets per currency.")

    available = ["EUR","USD","GBP","CHF","JPY","SEK","NOK","DKK","CAD"]
    selected  = st.multiselect("Currencies to include",
                               available, default=["EUR","USD","GBP"],
                               help="EUR is mandatory (base currency)")
    if "EUR" not in selected:
        selected = ["EUR"] + selected

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"**Will generate:** {len(selected)} × 5 = "
                    f"**{len(selected)*5} sheets**")
        for c in selected:
            flag = CCY_FLAGS.get(c,"")
            st.markdown(f"- {flag} `{c}` → sheets: "
                        + ", ".join(f"`C 72.00{(' '+c if c!='EUR' else '')}`"[:15]
                                    for _ in [""])
                        + f"C 72.00{'  '+c if c!='EUR' else ''} … C 76.00{'  '+c if c!='EUR' else ''}")
    with cb:
        st.markdown("**Sheet naming convention:**")
        st.code("C 72.00        ← EUR (no suffix)\n"
                "C 72.00 USD    ← USD\n"
                "C 72.00 GBP    ← GBP\n"
                "C 73.00        ← EUR\n"
                "C 73.00 USD    ← USD\n"
                "…")

    if st.button("🔨 Generate Multi-Currency Template", type="primary"):
        with st.spinner(f"Building workbook with {selected}…"):
            buf = create_sample_workbook(
    currencies=selected,
    entity_lei=entity_id,
    ref_date=ref_date.isoformat(),
    base_currency=base_ccy,
)
            xb    = buf.getvalue()
        ccy_str = "_".join(selected)
        st.success(f"✅ {len(selected)*5} sheets created!")
        st.download_button(
            f"⬇️ Download EBA_LCR_Sample_{ccy_str}.xlsx", xb,
            f"EBA_LCR_Sample_{ccy_str}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VALIDATE
# ══════════════════════════════════════════════════════════════════════════════
with t3:
    st.markdown("### Pre-submission validation")
    st.markdown(
        "Upload a generated **xBRL-CSV package (.zip)** to check if it will be "
        "accepted by the EBA / NCA filing system. Covers **structural**, "
        "**format**, **dimension** and **business rule** checks per "
        "EBA Filing Rules v5.8.")

    st.info("ℹ️ This is a pre-flight simulation — it does not submit to EBA/EUCLID. "
            "No data leaves this application.", icon="ℹ️")

    val_file = st.file_uploader("Upload XBRL-CSV package (.zip)", type=["zip"],
                                 key="validator_upload")
    if val_file:
        st.divider()
        with st.spinner("Running validation checks…"):
            validator = EBAPackageValidator()
            rpt       = validator.validate(val_file.read(), val_file.name)

        # ── Overall verdict ────────────────────────────────────────────────────
        n_err  = len(rpt.errors)
        n_warn = len(rpt.warnings)
        n_info = len(rpt.infos)

        if rpt.acceptable:
            verdict_color = "#1a7a1a" if n_warn == 0 else "#7a5a00"
            verdict_icon  = "✅" if n_warn == 0 else "⚠️"
            verdict_text  = ("LIKELY TO BE ACCEPTED" if n_warn == 0
                             else "LIKELY ACCEPTED — WITH WARNINGS")
            verdict_sub   = ("No errors or warnings detected."
                             if n_warn == 0
                             else f"{n_warn} warning(s) may require attention.")
        else:
            verdict_color = "#7a1a1a"
            verdict_icon  = "❌"
            verdict_text  = "WILL BE REJECTED"
            verdict_sub   = f"{n_err} critical error(s) must be fixed before submission."

        st.markdown(f"""
        <div style="background:{verdict_color}22;border:2px solid {verdict_color};
             border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:1rem;text-align:center">
          <div style="font-size:2rem">{verdict_icon}</div>
          <div style="font-size:1.3rem;font-weight:700;color:{verdict_color}">{verdict_text}</div>
          <div style="color:#555;margin-top:.3rem">{verdict_sub}</div>
        </div>""", unsafe_allow_html=True)

        # ── Score bar ──────────────────────────────────────────────────────────
        score = rpt.score
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

        # ── Summary metrics ────────────────────────────────────────────────────
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("✅ Passed",   rpt.passed_count)
        mc2.metric("❌ Errors",   n_err,  delta=f"-{n_err}"  if n_err  else None,
                   delta_color="inverse")
        mc3.metric("⚠️ Warnings", n_warn, delta=f"-{n_warn}" if n_warn else None,
                   delta_color="inverse")
        mc4.metric("ℹ️ Info",     n_info)

        st.divider()

        # ── Detailed results ───────────────────────────────────────────────────
        st.markdown("#### Detailed Check Results")

        LEVEL_CFG = {
            "ERROR":   {"icon":"❌", "color":"#7a1a1a", "bg":"#fff0f0"},
            "WARNING": {"icon":"⚠️", "color":"#7a5a00", "bg":"#fffbf0"},
            "INFO":    {"icon":"ℹ️", "color":"#1a4a7a", "bg":"#f0f6ff"},
        }

        # Group by category
        categories = {
            "S": "📦 Structure",
            "J": "📄 reports.json",
            "P": "🔑 parameters.csv",
            "F": "📋 Filing Indicators",
            "T": "📊 Template CSVs",
            "C": "💱 Currency Dimensions",
            "B": "📐 Business Rules",
        }

        for prefix, cat_label in categories.items():
            cat_results = [r for r in rpt.results if r.rule_id.startswith(prefix)]
            if not cat_results:
                continue
            cat_pass  = sum(1 for r in cat_results if r.passed)
            cat_total = len(cat_results)
            cat_ok    = cat_pass == cat_total

            with st.expander(
                f"{'✅' if cat_ok else '❌' if any(not r.passed and r.level=='ERROR' for r in cat_results) else '⚠️'} "
                f"{cat_label} — {cat_pass}/{cat_total}",
                expanded=not cat_ok):

                for res in cat_results:
                    cfg = LEVEL_CFG[res.level]
                    icon = "✅" if res.passed else cfg["icon"]
                    bg   = "#f0fff0" if res.passed else cfg["bg"]
                    color = "#1a7a1a" if res.passed else cfg["color"]
                    detail_html = (f'<div style="font-size:.8rem;color:#666;margin-top:2px">'
                                   f'💬 {res.detail}</div>' if res.detail else "")
                    st.markdown(f"""
                    <div style="background:{bg};border-left:3px solid {color};
                         padding:.5rem .8rem;border-radius:4px;margin:4px 0">
                      <span style="font-weight:600;color:{color}">{icon} [{res.rule_id}]</span>
                      <span style="margin-left:.5rem">{res.message}</span>
                      {detail_html}
                    </div>""", unsafe_allow_html=True)

        # ── Fix suggestions ────────────────────────────────────────────────────
        failed = [r for r in rpt.results if not r.passed and r.level=="ERROR"]
        if failed:
            st.divider()
            st.markdown("#### 🔧 How to fix the errors")
            FIX_GUIDE = {
                "S001": "Add META-INF/reports.json to your ZIP. Use the Convert tab to regenerate.",
                "S002": "Add reports/parameters.csv. Use the Convert tab to regenerate.",
                "S003": "Add reports/FilingIndicators.csv. Use the Convert tab to regenerate.",
                "S004": "Remove .xbrl/.xml files — EBA only accepts xBRL-CSV format since March 2026.",
                "J001": 'Set documentType to exactly "https://xbrl.org/2021/xbrl-csv".',
                "J002": "Taxonomy URL must point to an EBA framework (eba.europa.eu/eu/fr/xbrl/crr/).",
                "J004": "Ensure every URL in reports.json has a matching CSV file in the ZIP.",
                "P001": "Add entityIdentifier row to parameters.csv.",
                "P003": "Set periodInstant to YYYY-MM-DD format (e.g. 2025-12-31).",
                "F001": "Add at least one row with reported=true to FilingIndicators.csv.",
                "T001": "Row IDs must follow r[0-9]{4} format (e.g. r0010, r0020).",
                "T002": "Column IDs must follow c[0-9]{4} format (e.g. c0010, c0020).",
                "C001": "Currency dimension values must use ISO4217: prefix (e.g. ISO4217:EUR).",
            }
            for res in failed:
                fix = FIX_GUIDE.get(res.rule_id,
                    "Use the Convert tab to regenerate the package from a corrected template.")
                st.markdown(f"- **[{res.rule_id}] {res.message}**  →  {fix}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DOCS
# ══════════════════════════════════════════════════════════════════════════════
with t4:
    st.markdown("### Architecture & Multi-Currency Reference")
    da, db = st.columns(2)
    with da:
        st.markdown("""
**Multi-currency flow:**

1. Business fills `C 72.00` (EUR) + `C 72.00 USD` + `C 72.00 GBP`…  
2. `EBAExcelReader.read()` auto-detects currencies from sheet names  
3. Returns flat dict: `C_72_00_EUR`, `C_72_00_USD`, `C_72_00_GBP`…  
4. `XBRLCSVGenerator` adds `eba_LCI:CUS → ISO4217:XXX` dimension  
   to each CSV entry in `reports.json`  
5. Each currency gets its own CSV: `C_72_00_USD.csv`

**EBA regulatory rule:**  
Any currency ≥ 5% of total liabilities must be reported separately  
(Art. 415(2) CRR). All instances go in **one single ZIP**.
""")
    with db:
        st.markdown('<div class="filetree">' +
            "📦 XBRL_LCR_EUR_USD_GBP.zip<br>"
            "├── 📁 META-INF/<br>"
            "│   └── reports.json<br>"
            "│   &nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#6a9955'>← eba_LCI:CUS: ISO4217:USD…</span><br>"
            "└── 📁 reports/<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── parameters.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── FilingIndicators.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── C_72_00_EUR.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── C_72_00_USD.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── C_72_00_GBP.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── C_73_00_EUR.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── C_73_00_USD.csv<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;└── …"
            '</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Template × Currency Mapping Table")
    import pandas as pd
    rows_doc = []
    for key, t in LCR_TEMPLATES.items():
        for ccy in ["EUR","USD","GBP"]:
            sname = t["template_code"] if ccy=="EUR" else f"{t['template_code']} {ccy}"
            csv_f = f"{key}_{ccy}.csv"
            dim   = f"eba_LCI:CUS = ISO4217:{ccy}"
            rows_doc.append({"Template": t["template_code"], "Currency": ccy,
                             "Excel Sheet": sname, "CSV File": csv_f,
                             "XBRL Dimension": dim})
    st.dataframe(pd.DataFrame(rows_doc), use_container_width=True, hide_index=True)

  # ── WIP FOOTER ────────────────────────────────────────────────────────────────

st.markdown("""
<div class="wip-footer">
  <div style="display:flex;align-items:center;gap:8px">
    <span class="wip-badge">⚙️ WORK IN PROGRESS</span>
    <span style="color:#b8d0ff;font-size:.85rem">
      EBA XBRL-CSV Engine &nbsp;·&nbsp;
      Owner: <span class="wip-owner">Clément Denorme</span>
    </span>
  </div>
  <div class="wip-right">
    COREP 4.2 · LCR DA · C72–C76 · eba_met concept IDs · 5,112 mappings
  </div>
</div>
""", unsafe_allow_html=True)
