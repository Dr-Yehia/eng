# FINAL_REVIEW_NOTES — FDOT Risk Streamlit Dashboard (review package)

## What this package is
The **read-only research dashboard** plus the **validated outputs it displays** and the **validation reports**.
Data version = integrated dual-benchmark risk **v2.1.1**. App version = dashboard v1.

## How to run locally (from a fresh environment)
```bash
cd streamlit_fdot_risk_dashboard_v1
pip install -r requirements.txt
streamlit run app.py
```
- **Entry file:** `app.py` (Home = Executive Overview).
- **Internet:** NOT required. The app reads only bundled local files under `data/`. (No external API calls at runtime.)

## Pages
Home (Executive Overview) · 01 Data Lineage & Validation · 02 Case Explorer · 03 Bidder Competition ·
04 Item-Level Risk · 05 Risk Matrix · 06 Top Risk Items · 07 Benchmark Comparison ·
08 ML Support & Limitations · 09 Multi-Case Validation · 10 Reports & Downloads · 11 Methodology.

## Data shown
- 6 validated cases, 653 pay items (roadway, signals, bridge, maintenance).
- Cases: main validation = T5850, T6603, T1900, T4711 (bridge), E7U28 (maintenance); **sensitivity = E7Q32 (2 bidders)**.
- Parser v2 extracts all six official bid tabs with grand totals matching exactly (100% parser success).
- Benchmarks (risk): contractor **market** (non-winner median, 100%) + **FDOT historical 2024**. **ML = supporting only (~0% strong).**

## Package layout
- `app.py`, `pages/`, `core/`, `config/`, `.streamlit/config.toml`, `requirements.txt`, `README.md`, `.gitignore`
- `data/` — parquet/csv/json the app reads (self-contained)
- `reports/` — validation reports (integrated v2.1 & v2.1.1, multi-case), methodology note, full Excel report (18 sheets)
- `api/` — API-ready payloads + rich schemas
- `figures/` — 10 scientific figures from the integrated package
- `metadata/` — source_manifest.json (sha256, roles), package_summary.json
- `screenshots/` — 6 **page previews generated from the live data** (see note below)

## Screenshots note (honest)
`screenshots/*.png` are **page previews generated from the same live data**, NOT browser screenshots
(no headless browser is available in the build environment). For the true interactive UI, run
`streamlit run app.py`. Previews: 01 overview, 02 multi-case summary, 03 item-level risk, 04 risk matrix,
05 data lineage, 06 reports.

## Large raw files intentionally EXCLUDED (not needed by the app)
- The 40MB DDC source parquet, the 409MB FORMATTED xlsx, the 199MB leaked-model pkl, the 974MB Dubai folder,
  and all superseded `outputs_*_v1/` packages. The dashboard is self-contained on the small bundled `data/`.

## Remaining limitations (stated honestly)
- Read-only v1 (no PDF upload/login/DB — planned for v2).
- 6 FDOT lettings (5 main + 1 sensitivity) spanning roadway, signals, bridge and maintenance; other DOTs/agencies still need more cases for broader generalization.
- ML supporting only for FDOT items. Wording: abnormal pricing risk / commercial review — never fraud.

## Verification in this package
- `reports/validation_report_v2_1_1.md` (integrated, ALL PASS) · `reports/multi_case_validation_report.json` ·
  `data/predeploy_patch_report.json` (pre-deploy fixes, ALL PASS).
- App boots with `streamlit run app.py` → HTTP 200, no traceback (verified).


## Versioning & folder name
- App code version: **v1** (read-only). Risk data version: **v2.1.1**.
- In this review ZIP the root folder is **renamed to `streamlit_fdot_risk_dashboard_v2_1_1`** to match the data version and avoid confusion. Entry point unchanged: `app.py`.
- New page added: **11_Methodology** (market + FDOT historical benchmarks, ML supporting only, thresholds, limitations).
