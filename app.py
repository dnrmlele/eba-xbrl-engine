
"""EBA XBRL-CSV Engine — Streamlit UI (multi-currency)"""
import streamlit as st, io, json, sys, os, pandas as pd
from datetime import date
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
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
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="eba-header">
  <h1>🏦 EBA XBRL-CSV Reporting Engine</h1>
  <p>Multi-currency · C72–C76 LCR · Framework 4.2 · EBA Filing Rules v5.8</p>
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
t1, t2, t3 = st.tabs(["📤 Convert", "📥 Sample Template", "📖 Documentation"])

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
            buf   = create_sample_workbook(currencies=selected)
            xb    = buf.getvalue()
        ccy_str = "_".join(selected)
        st.success(f"✅ {len(selected)*5} sheets created!")
        st.download_button(
            f"⬇️ Download EBA_LCR_Sample_{ccy_str}.xlsx", xb,
            f"EBA_LCR_Sample_{ccy_str}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DOCS
# ══════════════════════════════════════════════════════════════════════════════
with t3:
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
            sname = t["sheet_name"] if ccy=="EUR" else f"{t['sheet_name']} {ccy}"
            csv_f = f"{key}_{ccy}.csv"
            dim   = f"eba_LCI:CUS = ISO4217:{ccy}"
            rows_doc.append({"Template": t["template_code"], "Currency": ccy,
                             "Excel Sheet": sname, "CSV File": csv_f,
                             "XBRL Dimension": dim})
    st.dataframe(pd.DataFrame(rows_doc), use_container_width=True, hide_index=True)
