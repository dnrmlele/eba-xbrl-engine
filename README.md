# EBA XBRL-CSV Engine

**Project:** eba-xbrl-engine

A modern open-source engine to generate EBA-compliant xBRL-CSV packages from Excel templates.

## 1. Project Structure (modern src layout)

```
eba-xbrl-engine/
├── pyproject.toml
├── requirements.txt
├── README.md
├── app.py
├── src/
│   └── eba_xbrl_engine/
│       └── __init__.py
├── engine/
│   └── ... (core package, backwards-compatible)
├── tests/
│   └── test_reader.py
├── generate_ipr_templates.py
├── generate_lcr_templates.py
└── .gitignore
```

- `src/eba_xbrl_engine`: optional package wrapper for standard Python packaging
- `engine/*`: core business logic (readers, generators, templates, validation)
- `app.py`: Streamlit UI that orchestrates workflows
- `tests/*`: unit tests with `pytest`

## 2. Install & run

```bash
python3 -m pip install -r requirements.txt
pytest -q
streamlit run app.py
```

## 3. What the app does

### EBA LCR reporting
- Generates sample C72–C76 workbooks
- Loads populated sheets from user uploads
- Builds xBRL-CSV zip package with final report files

### CSSF SEPA IPR reporting
- Generates IPR Excel template based on ANNEX schema
- Applies highlight rules (fillable/non-fillable) correctly
- Reads filled IPR template and produces xBRL-CSV records

### Validation
- Pre-submission validation checks for xBRL-CSV package structure.

## 4. Key modules

- `engine/generator.py`: xBRL-CSV package builder
- `engine/ipr_generator.py`: multi-year IPR zip generation
- `engine/reader.py`: EBA template reader + data-point extraction
- `engine/ipr_reader.py`: IPR sheet parser with robust scanning
- `engine/sample_creator.py`: styled sample sheet exporter
- `engine/ipr_sample_creator.py`: IPR-template-specific cell coloring and row logic
- `engine/definitions/*`: template definitions and cell->concept mapping

## 5. Developer workflow

1. Update templates or mapping in `engine/definitions/*.py`
2. Regenerate mapping if required:
   - `python3 generate_ipr_templates.py DPM_4.2_Annotated.xlsx`
3. Run tests:
   - `pytest -q`
4. Run app:
   - `streamlit run app.py`

## 6. Best practice checks added

- strict row/column code extraction (rows may be `0010` etc.)
- numeric value normalization in `engine/ipr_reader.py` (handles `1 234`, `5,678` etc.)
- sheet name tolerance (`S_01_01`, `S 01.01`, `2025_S_01.01`)
- no custom uploads path for IPR template (app template only)

## 7. Packaging and installation

- `pyproject.toml` exists for `setuptools` build. Package is installable via:
  - `pip install -e .`

- local entrypoint `eba-xbrl` is available (if Streamlit path is configured).

## 8. Useful commands

- `python3 -m pytest -q`
- `black .` (format)
- `ruff check .` (lint if configured)
- `python3 generate_ipr_templates.py <path_to_annotated_excel>`

## 9. Add notes for future contributors

- Update `engine/definitions/` first for new reporting versions.
- Keep `engine/ipr_sample_creator.py` consistent with listing of fillable rows and colors.
- Use `tests/test_reader.py` as pattern for new coverage.
- Ensure `app.py` is stable and referenced by UI tests.
