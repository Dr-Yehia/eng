# FDOT Construction Unit-Price Benchmarking & Abnormal Pricing Risk — Dashboard

Interactive, multi-page **Streamlit** dashboard for a PhD framework that:

1. predicts construction work-item **benchmark unit prices** with a no-leakage ML model,
2. **time-adjusts** them with official price indices,
3. applies them to **real FDOT bid tabulations** to flag **abnormal pricing risk** across multiple projects.

> **Abnormal pricing risk** analysis — it flags unit-rate deviations that warrant commercial review.
> It does **not** allege fraud or intent.

## Pages
- **Home / Overview** — KPIs, winning bids, exposure and risk distribution across validated cases.
- **Case Explorer** — drill into one project: metadata, bidder ranking, item-level risk, CSV download.
- **Risk Analysis** — cross-case filters, risk matrix, deviation distribution, top over/under-pricing.
- **Multi-Benchmark** — winner vs bidder market vs non-winner median vs ML for a single item.
- **Methodology** — full documentation, benchmarks, thresholds, honest limitations.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this `streamlit_dashboard/` folder to a GitHub repository.
2. On https://share.streamlit.io create an app pointing at `app.py` on your branch.
3. Streamlit Cloud installs `requirements.txt` automatically. The bundled `data/` files make the app self-contained.

## Data
Self-contained validated outputs (4 FDOT cases: T5850, T6603, T1900, E7Q32):
`data/all_cases_dashboard_ready.parquet`, `all_cases_case_summary.parquet`, `all_cases_bidder_summary.parquet`,
`project_summary.json`. Failed-extraction cases (bridge/maintenance layouts) are intentionally excluded.

Primary benchmark = competitive **bidder market** (non-winner median). The ML benchmark is **supporting only**.
