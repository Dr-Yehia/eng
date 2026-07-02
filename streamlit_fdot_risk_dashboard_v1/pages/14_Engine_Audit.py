# -*- coding: utf-8 -*-
"""Engine & Methodology Audit — versions, frozen snapshots, thresholds, confidence tiers, run log."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core_engine import assets, audit_logger as al

st.set_page_config(page_title="Engine Audit", page_icon="🧾", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("🧾 Engine & Methodology Audit")
st.caption("Full reproducibility record: every interactive result is produced by these exact frozen components.")

st.subheader("Component versions (used by every run)")
v = assets.versions()
st.dataframe(pd.DataFrame([{"component": k, "version": str(val)} for k, val in v.items()]),
             hide_index=True, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Frozen index snapshot")
    idx = assets.indices()
    st.write(f"**{idx.index_code.nunique()} BLS series**, monthly, "
             f"{idx.date.min():%Y-%m} → **{idx.date.max():%Y-%m}** (frozen; no live fetch at runtime).")
    st.dataframe(idx.groupby(["index_code", "index_family"]).agg(
        first=("index_value", "first"), last=("index_value", "last"), months=("index_value", "count")).reset_index(),
        hide_index=True, use_container_width=True)
with c2:
    st.subheader("Statistical risk thresholds (validated, 6-case)")
    th = assets.risk_thresholds()
    st.dataframe(pd.DataFrame([{"benchmark": k, **{m: round(x, 2) for m, x in d.items()}} for k, d in th.items()]),
                 hide_index=True, use_container_width=True)
    st.caption("Classification = fixed % AND robust z-score AND per-benchmark P75/P90/P95 — identical to integrated_risk_v2.")

st.subheader("Input-completeness confidence tiers (honesty guard)")
st.markdown("""
| Inputs provided | Confidence | Behaviour |
|---|---|---|
| FDOT `item_id` + matching unit | **High** | official 2024 historical benchmark drives the assessment |
| description + unit + **resource composition** | **Medium-High** | validated ML uses its composition features |
| description + unit only | **Medium-Low / preliminary** | numeric features imputed with division medians — flagged explicitly |
| weak catalog match (<0.50) & no composition | **Low** | *No reliable benchmark — manual review*; model output shown for reference only and **never** used as risk evidence |
""")

st.subheader("Scope & limitations")
st.markdown("""
- Output is an **expected benchmark unit price** — not a guaranteed market or "fair" price.
- Risk wording is **abnormal pricing risk / commercial review** — never fraud.
- UAE mode = **region-calibrated benchmark estimate** (US benchmark → unit/FX → Dubai factor), not a confirmed UAE market price.
- Escalation uses the **frozen** BLS snapshot; targets beyond it are clamped (no forecasting). A live-API refresh can be added later and would log `index_source / download_date / series_id`.
- Single-item entry has **no bidder-market benchmark** (that requires a full bid tab — see the Case Study pages).
""")

st.subheader("Session run log")
runs = al.runs_df()
if len(runs):
    st.dataframe(runs, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download run log (CSV)", runs.to_csv(index=False), "engine_run_log.csv", "text/csv")
else:
    st.caption("No runs in this session yet — use the Live Estimator or Batch Analyzer.")
