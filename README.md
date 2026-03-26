# EBA XBRL-CSV Engine

Python + Streamlit engine that converts filled EBA Excel templates (C72–C76)
into compliant **xBRL-CSV report packages** per EBA Reporting Framework 4.2.

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud (free shareable URL)
1. `git push` this folder to a **public GitHub repo**
2. Go to https://share.streamlit.io → **New app**
3. Pick repo + branch + `app.py`
4. Click **Deploy** → get `https://your-app.streamlit.app`

## Supported Templates
| Code    | Name                          |
|---------|-------------------------------|
| C 72.00 | Liquid Assets                 |
| C 73.00 | Outflows                      |
| C 74.00 | Inflows                       |
| C 75.00 | Collateral Swaps              |
| C 76.00 | LCR Calculation               |

## References
- EBA Reporting Framework 4.2 — https://www.eba.europa.eu
- EBA Filing Rules v5.8
- xBRL-CSV 1.0 — https://www.xbrl.org/Specifications/xbrl-csv/
