# EBA XBRL-CSV Engine

**Project:** eba-xbrl-engine

A Python + Streamlit application for converting EBA Excel templates into fully compliant xBRL-CSV reporting packages for EBA Reporting Framework 4.2.

## 🚀 Overview
This engine supports the standard EBA templates and generates:
- xBRL-CSV data packages compliant with Annex I and Annex III
- SEPA IPR reporting templates (S 01.01, S 01.02, S 02.01, S 02.02, S 03.00, S 04.00)
- CSV export and XLSX user-friendly templates for data entry and validation

## 🧩 What’s included
- `app.py` — main Streamlit web UI, file upload and report generation workflow
- `engine/` — core engine functions:
  - `generator.py` — CSV package builder
  - `ipr_generator.py` — SEPA IPR mapping engine
  - `reader.py` — input Excel reader and value extraction
  - `sample_creator.py` / `ipr_sample_creator.py` — XLSX template creator
  - `validator.py` — data validation against EBA rules
- `generate_ipr_templates.py` — CLI helper to build IPR row/column concept mapping from annotated official templates
- `engine/definitions/` — stable template definitions and concept mappings

## 🛠️ Quick Start
```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

Open browser at `http://localhost:8501` and use the UI to:
1. Choose report type (LCR, IPR, etc.)
2. Download the built-in sample template
3. Fill values and upload the filled template
4. Generate xBRL-CSV report package

## ✅ CI / Repository Flow
- Main branch always holds runnable application with valid IPR template generation
- Feature branches for mapping and template updates
- Direct commit policy: fix on main (patch branches avoided for minimal infra)

## 📌 Supported EBA Templates
| Template | Description |
|----------|-------------|
| C 72.00 | Liquid Assets |
| C 73.00 | Outflows |
| C 74.00 | Inflows |
| C 75.00 | Collateral Swaps |
| C 76.00 | LCR Calculation |
| S 01.01 | SEPA Credit Transfers (National Currency) |
| S 01.02 | SEPA Credit Transfers (Euro) |
| S 02.01 | SEPA Charges (National Currency) |
| S 02.02 | SEPA Charges (Euro) |
| S 03.00 | Payment Accounts and Total Charges |
| S 04.00 | Rejected Instant Credit Transfers |

## 🔁 Development Workflow
1. Clone repository
2. Install requirements (`pip install -r requirements.txt`)
3. Run app locally (`streamlit run app.py`)
4. Update mapping in `engine/definitions/ipr_templates.py` and generator code
5. Run `python3 generate_ipr_templates.py <template.xlsx>` to refresh mapping if needed
6. Run unit tests (add test framework as needed)
7. Commit, push, create PR

## 📌 Notes for future devs
- Template generation now enforces app-provided styling and mapping (`IPR_TEMPLATES` concept map).
- `engine/ipr_sample_creator.py` is authoritative for read/write color logic.
- `generate_ipr_templates.py` script must run manually for new policy versions or sheet structure updates.

## ⚙️ Validation / Testing
- Check `app.py` UI and export function after updates.
- Use sample templates in `engine/definitions` to verify branch behavior.
- Validate output CSVs with reference `xBRL-CSV` compliance if available.

## 📚 References
- EBA Reporting Framework 4.2 — https://www.eba.europa.eu
- EBA Filing Rules v5.8
- xBRL-CSV 1.0 — https://www.xbrl.org/Specifications/xbrl-csv/

