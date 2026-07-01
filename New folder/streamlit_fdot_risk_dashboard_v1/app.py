# -*- coding: utf-8 -*-
"""FDOT Abnormal Pricing Risk — Research Dashboard (read-only). Home = Executive Overview."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import streamlit as st
import plotly.express as px
from core.data_loader import (load_items, load_case_summary, load_lineage, load_project_summary,
                              RISK_ORDER, RISK_COLORS, DISCLAIMER, PRIMARY_NOTE, kpi_cards)

st.set_page_config(page_title="FDOT Pricing Risk — Research Dashboard", page_icon="🛣️", layout="wide")
items = load_items()
cs = load_case_summary()
lin = load_lineage()
proj = load_project_summary()

st.title("🛣️ FDOT Construction Bid — Abnormal Pricing Risk")
st.caption("Research decision-support prototype · read-only · dual-benchmark (market + FDOT historical) · ML supporting only")
st.info(DISCLAIMER)

# ---- KPIs ----
n_val = items.case_id.nunique()
n_failed = int((lin["extraction_all_pass"] == False).sum()) if len(lin) and "extraction_all_pass" in lin else 0
total_bid = cs["winning_total_bid"].sum()
mkt_exposure = items["market_overpricing_exposure"].sum()
elev = items["combined_risk_flag"].isin(["High", "Critical"]).sum()
parser_rate = (lin["extraction_all_pass"].mean() * 100) if len(lin) and "extraction_all_pass" in lin else 100.0
kpi_cards([
    ("Validated cases", f"{n_val}", "cases passing extraction + risk validation"),
    ("Failed / excluded", f"{n_failed}", "cases that failed extraction (0 after parser v2) — see Data Lineage page"),
    ("Pay items", f"{len(items):,}", "one row per item per validated case"),
    ("Winning bid value", f"${total_bid/1e6:,.1f}M", "sum of winning bids across validated cases"),
])
kpi_cards([
    ("Market overpricing exposure", f"${mkt_exposure/1e6:,.2f}M", "winner above non-winner median × qty"),
    ("High + Critical items", f"{int(elev):,}", "combined risk flag High or Critical"),
    ("Confirmed-by-both", f"{int(cs['confirmed_by_both'].sum()):,}", "flagged by BOTH market & FDOT historical = high confidence"),
    ("Parser success", f"{parser_rate:.0f}%", "extraction success across all attempted cases"),
])
st.caption(PRIMARY_NOTE)
st.divider()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Risk distribution (all validated items)")
    rd = items["combined_risk_flag"].value_counts().reindex(RISK_ORDER).dropna().reset_index()
    rd.columns = ["risk_flag", "items"]
    fig = px.bar(rd, x="risk_flag", y="items", color="risk_flag",
                 color_discrete_map=RISK_COLORS, category_orders={"risk_flag": RISK_ORDER})
    fig.update_layout(showlegend=False, height=360, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Market overpricing exposure by case")
    ec = cs.copy(); ec["exposure_pct"] = ec["market_overpricing_exposure"] / ec["winning_total_bid"] * 100
    fig2 = px.bar(ec.sort_values("exposure_pct"), x="case_id", y="exposure_pct", color="case_role",
                  hover_data=["market_overpricing_exposure", "winning_total_bid"],
                  labels={"exposure_pct": "exposure (% of winning bid)"})
    fig2.update_layout(height=360, margin=dict(t=10))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top 10 items by market overpricing exposure")
top = items.nlargest(10, "market_overpricing_exposure")[
    ["case_id", "line_no", "description", "unit", "quantity", "winner_unit_price",
     "market_benchmark_unit_price", "deviation_vs_market", "market_overpricing_exposure",
     "combined_risk_flag", "evidence_class"]]
st.dataframe(top, use_container_width=True, hide_index=True,
             column_config={"deviation_vs_market": st.column_config.NumberColumn("dev vs market %", format="%.1f"),
                            "market_overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
                            "winner_unit_price": st.column_config.NumberColumn("winner $", format="$%.2f"),
                            "market_benchmark_unit_price": st.column_config.NumberColumn("market $", format="$%.2f")})

st.divider()
st.markdown("""
**How to read this dashboard** — the scientific flow is: **Data Sources → Validation → Risk Analysis → Multi-case Evidence → Exportable Reports.**
Use the sidebar pages: *Data Lineage & Validation* first (transparency), then *Case Explorer*, *Item-Level Risk*,
*Risk Matrix*, *Benchmark Comparison*, *ML Support & Limitations*, *Multi-Case Validation*, *Reports & Downloads*.
""")
