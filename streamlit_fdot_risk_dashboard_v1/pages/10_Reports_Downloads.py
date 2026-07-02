# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from core.data_loader import (load_items, load_case_summary, load_methodology_md, file_bytes)

st.set_page_config(page_title="Reports & Downloads", page_icon="📥", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("📥 Reports & Downloads")
st.caption("Everything shown here is generated upstream by validated, reproducible scripts (not computed in the dashboard).")

items = load_items(); cs = load_case_summary()
c1, c2 = st.columns(2)
with c1:
    st.subheader("Data (CSV)")
    st.download_button("⬇️ Item-level dual-benchmark risk (CSV)", items.to_csv(index=False), "integrated_risk_item_level.csv", "text/csv")
    st.download_button("⬇️ Case summary (CSV)", cs.to_csv(index=False), "integrated_case_summary.csv", "text/csv")
    x = file_bytes("integrated_risk_item_level.csv")
    if x: st.download_button("⬇️ Item-level (source CSV file)", x, "integrated_risk_item_level_source.csv", "text/csv")
with c2:
    st.subheader("Reports / API")
    xr = file_bytes("integrated_fdot_risk_report.xlsx")
    if xr: st.download_button("⬇️ Full Excel report (18 sheets)", xr, "integrated_fdot_risk_report.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    for nm, out in [("integrated_risk_items_api_ready.json", "risk_items_api_ready.json"),
                    ("integrated_project_summary_api_ready.json", "project_summary_api_ready.json")]:
        b = file_bytes(nm)
        if b: st.download_button(f"⬇️ {out}", b, out, "application/json")

st.divider()
st.subheader("Methodology decision note")
st.markdown(load_methodology_md())
