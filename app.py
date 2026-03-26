
"""EBA XBRL-CSV Reporting Engine — Streamlit UI"""
import streamlit as st, io, json, sys, os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from engine.reader        import EBAExcelReader
from engine.generator     import XBRLCSVGenerator
from engine.sample_creator import create_sample_workbook
from engine.definitions.lcr_templates import LCR_TEMPLATES

st.set_page_config(page_title="EBA XBRL-CSV Engine", page_icon="🏦",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.eba-header{background:linear-gradient(135deg,#003399,#0055CC);padding:1.4rem 2rem;
  border-radius:12px;margin-bottom:1.2rem;color:white}
.eba-header h1{color:white;margin:0;font-size:1.7rem}
.eba-header p{color:#b8d0ff;margin:.3rem 0 0;font-size:.9rem}
.card{background:#f0f6ff;border-left:4px solid #003399;padding:.9rem 1.1rem;
  border-radius:6px;margin:.4rem 0;font-size:.88rem}
.badge{display:inline-block;background:#003399;color:white;padding:1px 7px;
  border-radius:4px;font-size:.78rem;font-weight:700;margin:2px}
.filetree{font-family:monospace;background:#1e1e1e;color:#d4d4d4;padding:1rem;
  border-radius:8px;font-size:.83rem;line-height:1.65}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="eba-header">
  <h1>🏦 EBA XBRL-CSV Reporting Engine</h1>
  <p>Convert filled EBA Excel templates (C72–C76) to compliant xBRL-CSV packages
  · Framework 4.2 · LCR / Liquidity Reporting</p>
</div>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Report Parameters")
    entity_id = st.text_input("Entity LEI", value="7LTWFZYICNSX8D621K86",
                               help="20-char Legal Entity Identifier")
    ref_date  = st.date_input("Reference Date", value=date(2025, 12, 31))
    decimals  = st.selectbox("Decimal Accuracy", [-3, -6, 0],
        format_func=lambda x:{-3:"-3 (thousands)",-6:"-6 (millions)",0:"0 (units)"}[x])
    st.divider()
    st.markdown("### 📋 Templates")
    for _,t in LCR_TEMPLATES.items():
        st.markdown(f'<span class="badge">{t["template_code"]}</span> {t["name"]}',
                    unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📚 References")
    st.markdown("- [EBA Framework 4.2](https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks/reporting-framework-42)\n"
                "- [EBA Filing Rules v5.8](https://www.eba.europa.eu/)\n"
                "- [xBRL-CSV 1.0 Spec](https://www.xbrl.org/Specifications/xbrl-csv/)")

# ── TABS ──────────────────────────────────────────────────────────────────────
t1, t2, t3 = st.tabs(["📤 Convert Template", "📥 Sample Template", "📖 Documentation"])

# ── TAB 1: CONVERT ────────────────────────────────────────────────────────────
with t1:
    st.markdown("### Upload your filled EBA Excel template")
    c1, c2 = st.columns([2, 1])
    with c1:
        uploaded = st.file_uploader("Choose .xlsx file", type=["xlsx"])
    with c2:
        st.markdown('<div class="card"><strong>Expected sheet names:</strong><br>'
                    'C 72.00 · C 73.00 · C 74.00 · C 75.00 · C 76.00</div>',
                    unsafe_allow_html=True)

    if uploaded:
        st.divider()
        try:
            with st.spinner("Reading Excel template…"):
                reader = EBAExcelReader()
                data   = reader.read(uploaded)
            if not data:
                st.error("No matching sheets found. Check sheet names.")
                st.stop()

            st.markdown("#### ✅ Extraction Summary")
            total = sum(len(v["data_points"]) for v in data.values())
            cols  = st.columns(len(data) + 1)
            cols[0].metric("Total Data Points", total)
            for i,(k,v) in enumerate(data.items(), 1):
                cols[i].metric(v["template_code"], f"{len(v['data_points'])} pts")

            st.divider()
            with st.spinner("Generating xBRL-CSV package…"):
                gen     = XBRLCSVGenerator(entity_id, ref_date.isoformat(), decimals)
                zipdata = gen.generate_package(data)
                preview = gen.get_preview(data)

            st.success(f"✅ Package ready — {len(zipdata)/1024:.1f} KB")
            fname = f"XBRL_LCR_{entity_id[:8]}_{ref_date:%Y%m%d}.zip"
            cd, ci = st.columns([1, 2])
            with cd:
                st.download_button("⬇️ Download XBRL-CSV Package", zipdata,
                                   fname, "application/zip",
                                   use_container_width=True, type="primary")
            with ci:
                st.markdown(f'<div class="card">📦 <strong>{fname}</strong><br>'
                            f'Entity: <code>{entity_id}</code> · Period: <code>{ref_date}</code>'
                            f'· Decimals: <code>{decimals}</code></div>',
                            unsafe_allow_html=True)

            st.markdown("#### 📁 Package Contents Preview")
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
        st.info("Upload a file above, or grab a sample from the **Sample Template** tab.")

# ── TAB 2: SAMPLE ─────────────────────────────────────────────────────────────
with t2:
    st.markdown("### Download a ready-to-use sample template")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Included:**\n- All 5 sheets (C 72.00 – C 76.00)\n"
                    "- EBA-style formatting (blue headers, L1/L2A/L2B coloring)\n"
                    "- Row & column IDs matching xBRL taxonomy\n"
                    "- Realistic sample data for immediate testing")
    with cb:
        st.markdown("**Usage:**\n1. Download & open in Excel\n"
                    "2. Replace sample values with real figures\n"
                    "3. **Do not rename sheets or move rows/columns**\n"
                    "4. Save and upload to the Convert tab")
    if st.button("🔨 Generate Sample Workbook", type="primary"):
        with st.spinner("Building Excel template…"):
            buf   = create_sample_workbook()
            xbytes = buf.getvalue()
        st.success("✅ Template ready!")
        st.download_button("⬇️ Download EBA_LCR_Sample_C72_C76.xlsx", xbytes,
                           "EBA_LCR_Sample_C72_C76.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, type="primary")

# ── TAB 3: DOCS ───────────────────────────────────────────────────────────────
with t3:
    st.markdown("### Architecture & Mapping Reference")
    da, db = st.columns(2)
    with da:
        st.markdown("""
**Engine modules:**

`engine/reader.py` — `EBAExcelReader`  
Reads Excel, locates sheets by name, extracts cell values from
predefined row/column positions.

`engine/generator.py` — `XBRLCSVGenerator`  
Builds the xBRL-CSV ZIP: `reports.json`, `parameters.csv`,
`FilingIndicators.csv`, one CSV per template.

`engine/definitions/lcr_templates.py`  
Configuration-driven mapping: row IDs (`r0020`…), column IDs
(`c0010`…), Excel positions, XBRL filing indicators.
""")
    with db:
        st.markdown('<div class="filetree">' +
            "📦 XBRL_LCR_package.zip<br>"
            "├── 📁 META-INF/<br>"
            "│   └── 📄 reports.json   <span style='color:#6a9955'>← taxonomy+module metadata</span><br>"
            "└── 📁 reports/<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 parameters.csv      <span style='color:#6a9955'>← LEI + date</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 FilingIndicators.csv <span style='color:#6a9955'>← filed templates</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 C_72_00.csv          <span style='color:#6a9955'>← Liquid Assets</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 C_73_00.csv          <span style='color:#6a9955'>← Outflows</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 C_74_00.csv          <span style='color:#6a9955'>← Inflows</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;├── 📄 C_75_00.csv          <span style='color:#6a9955'>← Collateral Swaps</span><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;└── 📄 C_76_00.csv          <span style='color:#6a9955'>← LCR Calculation</span>"
            '</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Template Mapping Details")
    import pandas as pd
    for key, tdef in LCR_TEMPLATES.items():
        with st.expander(f"**{tdef['template_code']}** — {tdef['name']}"):
            ra, rb = st.columns(2)
            with ra:
                st.markdown("**Rows → Excel row**")
                st.dataframe(pd.DataFrame([{"Row ID":k,"Label":v["label"],"Excel Row":v["excel_row"]}
                    for k,v in tdef["rows"].items()]), use_container_width=True, hide_index=True)
            with rb:
                st.markdown("**Columns → Excel col**")
                st.dataframe(pd.DataFrame([{"Col ID":k,"Label":v["label"],"Excel Col":v["excel_col"]}
                    for k,v in tdef["columns"].items()]), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("""#### Extending to COREP / FINREP
1. Create `engine/definitions/corep_templates.py` with row/col/Excel mappings  
2. Import and merge into `EBAExcelReader`  
3. No changes to the generator — it's fully data-driven  
4. Update the Streamlit sidebar and tabs as needed
""")
