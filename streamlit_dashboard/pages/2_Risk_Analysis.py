# -*- coding: utf-8 -*-
"""Cross-case risk analysis: filters, exposure, top items, unbalanced flags, risk matrix."""
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from utils import load_items, RISK_ORDER, RISK_COLORS, DISCLAIMER, kpi_row, page_header

st.set_page_config(page_title="Risk Analysis", page_icon="⚠️", layout="wide")
items = load_items()

page_header("⚠️ Risk Analysis", "Abnormal pricing risk across all validated cases.")
st.sidebar.header("Filters")
cs = st.sidebar.multiselect("Case", sorted(items["case_id"].unique()), default=sorted(items["case_id"].unique()))
fl = st.sidebar.multiselect("Risk flag", RISK_ORDER, default=RISK_ORDER)
secs = sorted(items["section_name"].dropna().unique())
sc = st.sidebar.multiselect("Section", secs)
kind = st.sidebar.radio("Item type", ["All", "Unit-rate only", "Lump-sum only"], index=0)
only_unbal = st.sidebar.checkbox("Possible unbalanced only", value=False)

f = items[items["case_id"].isin(cs) & items["risk_flag"].isin(fl)]
if sc: f = f[f["section_name"].isin(sc)]
if kind == "Unit-rate only": f = f[~f["is_lump_sum"]]
elif kind == "Lump-sum only": f = f[f["is_lump_sum"]]
if only_unbal and "possible_unbalanced_item" in f: f = f[f["possible_unbalanced_item"]]

kpi_row([
    ("Items shown", f"{len(f):,}", None),
    ("Overpricing exposure", f"${f['primary_financial_exposure'].sum():,.0f}", None),
    ("High / Critical", f"{int(f['risk_flag'].isin(['High','Critical']).sum()):,}", None),
    ("Possible unbalanced", f"{int(f.get('possible_unbalanced_item', pd.Series(dtype=bool)).sum()):,}",
     "|dev vs bidder median|>50% AND >2% of bid"),
])
st.divider()

c1, c2 = st.columns(2)
with c1:
    page_header("Risk matrix", "Exposure vs primary deviation (color = risk flag)")
    g = f.copy(); g["dev_clip"] = g["primary_deviation_pct"].clip(-150, 250)
    ch = (alt.Chart(g).mark_circle(size=60, opacity=0.6).encode(
        x=alt.X("dev_clip:Q", title="primary deviation %"),
        y=alt.Y("primary_financial_exposure:Q", title="overpricing exposure (USD)", scale=alt.Scale(type="symlog")),
        color=alt.Color("risk_flag:N", scale=alt.Scale(domain=RISK_ORDER, range=[RISK_COLORS[k] for k in RISK_ORDER]), sort=RISK_ORDER),
        tooltip=["case_id", "description", "primary_deviation_pct", "primary_financial_exposure", "risk_flag"]))
    st.altair_chart(ch, use_container_width=True)
with c2:
    page_header("Deviation distribution")
    g2 = f.copy(); g2["dev_clip"] = g2["primary_deviation_pct"].clip(-150, 150)
    ch2 = (alt.Chart(g2).mark_bar(color="#993404").encode(
        x=alt.X("dev_clip:Q", bin=alt.Bin(maxbins=40), title="winner deviation vs non-winner median (%)"),
        y="count()"))
    st.altair_chart(ch2, use_container_width=True)

st.divider()
t1, t2 = st.tabs(["🔺 Top overpricing exposure", "🔻 Top underpricing"])
base = ["case_id", "line_no", "description", "unit", "quantity", "actual_unit_price",
        "primary_benchmark_unit_price", "primary_deviation_pct", "primary_financial_exposure", "risk_flag"]
base = [c for c in base if c in f.columns]
with t1:
    st.dataframe(f.nlargest(30, "primary_financial_exposure")[base], use_container_width=True, hide_index=True)
with t2:
    st.dataframe(f.nsmallest(30, "primary_deviation_pct")[base], use_container_width=True, hide_index=True)

st.download_button("⬇️ Download filtered items (CSV)", f[base].to_csv(index=False), "risk_filtered.csv", "text/csv")
st.info(DISCLAIMER)
