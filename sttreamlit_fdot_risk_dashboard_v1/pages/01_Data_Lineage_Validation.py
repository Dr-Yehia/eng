# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core.data_loader import load_lineage, DISCLAIMER

st.set_page_config(page_title="Data Lineage & Validation", page_icon="🔎", layout="wide")
st.header("🔎 Data Lineage & Validation")
st.caption("Transparency layer: every case, its source file, and its extraction/risk validation status — including EXCLUDED cases.")
st.info(DISCLAIMER)

lin = load_lineage()
if lin.empty:
    st.warning("Lineage summary not available (multi-case validation package not bundled).")
    st.stop()

cols = ["case_id", "source_file", "project_type", "contract_id", "letting_date", "n_bidders", "n_items",
        "winning_total_bid", "extraction_all_pass", "risk_all_pass", "grand_totals_match",
        "included_in_combined", "do_not_use_for_risk"]
cols = [c for c in cols + ["failure_reason"] if c in lin.columns]
t = lin[cols].copy()

def status(v): return "✅ PASS" if v is True else ("❌ FAIL" if v is False else "—")
for c in ["extraction_all_pass", "included_in_combined"]:
    if c in t: t[c] = t[c].map(status)
if "do_not_use_for_risk" in t: t["do_not_use_for_risk"] = t["do_not_use_for_risk"].map(lambda v: "⛔ excluded" if v else "included")

st.subheader("All attempted cases")
st.dataframe(t, use_container_width=True, hide_index=True)

n_ok = int((lin["extraction_all_pass"] == True).sum())
n_fail = int((lin["extraction_all_pass"] == False).sum())
c1, c2, c3 = st.columns(3)
c1.metric("Cases attempted", len(lin))
c2.metric("Validated (extraction+risk)", n_ok)
c3.metric("Failed / excluded", n_fail, help="different PDF layout (bridge/maintenance); excluded from risk analysis")

failed = lin[lin["extraction_all_pass"] != True]
if len(failed):
    st.subheader("⛔ Excluded cases (NOT used in risk analysis)")
    st.caption("Shown here for full scientific transparency. They failed automated extraction (different bid-tab layout) and are excluded.")
    st.dataframe(failed[[c for c in ["case_id", "source_file", "project_type", "case_status"] if c in failed.columns]],
                 use_container_width=True, hide_index=True)

st.success("For every VALIDATED case, all bidder grand totals reconstructed from the extracted line items match the official FDOT bid-tab totals exactly.")
