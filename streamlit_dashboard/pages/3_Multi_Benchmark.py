# -*- coding: utf-8 -*-
"""Multi-benchmark comparison for a chosen item: winner vs market vs non-winner vs ML."""
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from utils import load_items, DISCLAIMER, page_header

st.set_page_config(page_title="Multi-Benchmark", page_icon="📊", layout="wide")
items = load_items()

page_header("📊 Multi-Benchmark Comparison",
            "How the winning unit price compares to every benchmark for a single item.")
c1, c2 = st.columns(2)
cid = c1.selectbox("Case", sorted(items["case_id"].unique()))
ci = items[items["case_id"] == cid]
label = ci["line_no"].astype(str) + " — " + ci["description"].astype(str).str.slice(0, 60)
pick = c2.selectbox("Item", label.tolist())
row = ci.iloc[label.tolist().index(pick)]

st.markdown(f"### {row['description']}")
st.caption(f"Case {cid} · line {row['line_no']} · unit {row.get('unit','-')} · quantity {row.get('quantity','-')}")

benUS = {"Winner (actual)": row.get("actual_unit_price"),
         "Bidder market median": row.get("bidder_market_median_unit_price"),
         "Non-winner median (primary)": row.get("non_winner_median_unit_price"),
         "ML DDC (supporting)": row.get("ml_expected_unit_price_at_tender") if "ml_expected_unit_price_at_tender" in row else np.nan}
bdf = pd.DataFrame([{"benchmark": k, "unit_price": v} for k, v in benUS.items() if pd.notna(v)])
L, R = st.columns([2, 1])
with L:
    ch = (alt.Chart(bdf).mark_bar().encode(
        x=alt.X("unit_price:Q", title="unit price (USD)"),
        y=alt.Y("benchmark:N", sort="-x", title=None),
        color=alt.condition(alt.datum.benchmark == "Winner (actual)", alt.value("#cc4c02"), alt.value("#3182bd")),
        tooltip=["benchmark", "unit_price"]))
    st.altair_chart(ch, use_container_width=True)
with R:
    st.metric("Primary deviation", f"{row.get('primary_deviation_pct', float('nan')):.1f}%",
              help="winner vs non-winner median")
    st.metric("Overpricing exposure", f"${row.get('primary_financial_exposure', 0):,.0f}")
    st.metric("Winner unit rank", f"{int(row.get('winner_unit_rank', 0))} of {ci['winner_unit_rank'].max():.0f}",
              help="1 = lowest unit price among bidders")
    rf = row.get("risk_flag")
    st.markdown(f"**Risk flag:** {rf}  \n**Action:** {row.get('recommended_action','-')}")
    if "ml_match_status" in row:
        st.caption(f"ML match: {row.get('ml_match_status')} (score {row.get('ml_match_score', float('nan')):.2f}) — supporting only")

st.divider()
page_header("Bidder spread context", "Where the winner sits within the full bidder range for this item.")
spread = pd.DataFrame({
    "metric": ["bidder low", "non-winner median", "bidder median", "winner (actual)", "bidder high"],
    "value": [row.get("bidder_market_low_unit_price", np.nan), row.get("non_winner_median_unit_price", np.nan),
              row.get("bidder_market_median_unit_price", np.nan), row.get("actual_unit_price", np.nan),
              row.get("bidder_market_high_unit_price", np.nan)]}).dropna()
if len(spread):
    ch2 = (alt.Chart(spread).mark_circle(size=160).encode(
        x=alt.X("value:Q", title="unit price (USD)"),
        y=alt.Y("metric:N", sort=["bidder low", "non-winner median", "bidder median", "winner (actual)", "bidder high"], title=None),
        color=alt.condition(alt.datum.metric == "winner (actual)", alt.value("#cc4c02"), alt.value("#666")),
        tooltip=["metric", "value"]))
    st.altair_chart(ch2, use_container_width=True)
st.info(DISCLAIMER)
