# FDOT Abnormal Pricing Risk — Research Dashboard (read-only, v1)

> **Versioning:** dashboard **app version = v1** (read-only prototype) · risk **data package version = v2.1.1** (integrated dual-benchmark). The review ZIP's root folder is named `streamlit_fdot_risk_dashboard_v2_1_1` to match the data version.


A professional **research decision-support dashboard** over the completed FDOT multi-case
**dual-benchmark abnormal-pricing-risk** framework. It is **read-only**: all calculations happen
upstream in validated, reproducible scripts; the dashboard only reads their outputs.

> **Abnormal pricing risk / commercial review** — this dashboard does **not** claim fraud detection.

## Scientific flow (how the pages are ordered)
**Data Sources → Validation → Risk Analysis → Multi-case Evidence → Exportable Reports.**

- **Home — Executive Overview**: KPIs, risk distribution, exposure by case, top items, disclaimer.
- **01 Data Lineage & Validation**: every attempted case (incl. EXCLUDED T4711/E7U28), extraction/risk status.
- **02 Case Explorer** · **03 Bidder Competition** · **04 Item-Level Risk** (filter + CSV download).
- **05 Risk Matrix** · **06 Top Risk Items** · **07 Benchmark Comparison** (market + FDOT historical + ML status).
- **08 ML Support & Limitations** · **09 Multi-Case Validation** · **10 Reports & Downloads**.

## Benchmarks
- **Primary (two independent):** contractor **market** (non-winner median) + official **FDOT historical 2024** weighted average.
- **Supporting only:** ML DDC benchmark (~0% strong matches for FDOT roadway items; never drives a flag).

## Data source
Bundled, self-contained copies of validated outputs:
- Risk (primary): `outputs_fdot_integrated_risk_v2_1_1/` → `data/integrated_dashboard_ready.parquet`, `integrated_case_summary.parquet`.
- Lineage (failed/excluded cases): `outputs_fdot_multi_case_validation_v1_1/` → `data/lineage_case_summary.parquet`, `bidder_summary.parquet`.
The dashboard shows a clear error (it does not crash) if a required file is missing.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
Push this folder to GitHub, create an app pointing at `app.py`. `requirements.txt` installs automatically;
bundled `data/` makes it self-contained.

## Scope of v1 (and roadmap)
- v1 = **read-only** dashboard over validated outputs (no PDF upload, no login, no DB).
- v2 = upload a new FDOT bid tab and run the parser.
- v3 = generic BoQ upload for other agencies.
