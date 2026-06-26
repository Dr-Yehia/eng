# -*- coding: utf-8 -*-
"""Per-case explorer: metadata, bidders, risk distribution, item-level risk."""
import pandas as pd
import streamlit as st
import altair as alt
from utils import (load_items, load_cases, load_bidders, RISK_ORDER, RISK_COLORS,
                   DISCLAIMER, kpi_row, page_header)

st.set_page_config(page_title="Case Explorer", page_icon="📋", layout="wide")
items = load_items(); cases = load_cases(); bidders = load_bidders()

page_header("📋 Case Explorer", "Drill into a single validated FDOT project.")
case_ids = sorted(items["case_id"].unique())
cid = st.selectbox("Select case", case_ids)
ci = items[items["case_id"] == cid]
meta = cases[cases["case_id"] == cid].iloc[0] if (cases["case_id"] == cid).any() else None

if meta is not None:
    c = st.columns(4)
    c[0].markdown(f"**Contract**\n\n{meta.get('contract_id','-')}")
    c[1].markdown(f"**Letting date**\n\n{meta.get('letting_date','-')}")
    c[2].markdown(f"**District**\n\n{meta.get('district','-')}")
    c[3].markdown(f"**Work type**\n\n{meta.get('project_type','-')}")

win_total = float(ci["winning_total_bid"].iloc[0]) if "winning_total_bid" in ci else float("nan")
kpi_row([
    ("Winner", str(ci["winner"].iloc[0]) if "winner" in ci else "-", None),
    ("Winning total bid", f"${win_total:,.0f}", None),
    ("Pay items", f"{len(ci)}", None),
    ("Overpricing exposure", f"${ci['primary_financial_exposure'].sum():,.0f}",
     f"{ci['primary_financial_exposure'].sum()/win_total*100:.1f}% of bid" if win_total else None),
])

st.divider()
L, R = st.columns(2)
with L:
    page_header("Bidder ranking")
    bb = bidders[bidders["case_id"] == cid].sort_values("bidder_rank")
    if len(bb):
        ch = (alt.Chart(bb).mark_bar()
              .encode(x=alt.X("total_bid:Q", title="total bid (USD)"),
                      y=alt.Y("bidder_name:N", sort="x", title=None),
                      color=alt.condition(alt.datum.bid_status == "Winning bid",
                                          alt.value("#238b45"), alt.value("#9ecae1")),
                      tooltip=["bidder_rank", "bidder_name", "total_bid", "percent_of_low_bid"]))
        st.altair_chart(ch, use_container_width=True)
with R:
    page_header("Risk distribution")
    rd = ci["risk_flag"].value_counts().reindex(RISK_ORDER).fillna(0).reset_index()
    rd.columns = ["risk_flag", "items"]
    ch = (alt.Chart(rd).mark_bar().encode(
        x=alt.X("risk_flag:N", sort=RISK_ORDER, title=None), y="items:Q",
        color=alt.Color("risk_flag:N", scale=alt.Scale(domain=RISK_ORDER, range=[RISK_COLORS[k] for k in RISK_ORDER]), legend=None),
        tooltip=["risk_flag", "items"]))
    st.altair_chart(ch, use_container_width=True)
    lump = int(ci["is_lump_sum"].sum()); unit = len(ci) - lump
    st.caption(f"Unit-rate items: **{unit}** · Lump-sum items (reviewed separately): **{lump}**")

st.divider()
page_header("Item-level risk", "Sorted by overpricing exposure. Filter by risk level.")
flags = st.multiselect("Risk flag", RISK_ORDER, default=["High", "Critical"])
view = ci[ci["risk_flag"].isin(flags)] if flags else ci
cols = ["line_no", "description", "section_name", "unit", "quantity", "actual_unit_price",
        "primary_benchmark_unit_price", "primary_deviation_pct", "primary_financial_exposure",
        "winner_unit_rank", "risk_flag", "recommended_action"]
cols = [c for c in cols if c in view.columns]
st.dataframe(view[cols].sort_values("primary_financial_exposure", ascending=False),
             use_container_width=True, hide_index=True,
             column_config={"primary_deviation_pct": st.column_config.NumberColumn("deviation %", format="%.1f"),
                            "primary_financial_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
                            "actual_unit_price": st.column_config.NumberColumn("winner unit $", format="$%.2f"),
                            "primary_benchmark_unit_price": st.column_config.NumberColumn("benchmark $", format="$%.2f")})
st.download_button("⬇️ Download this case (CSV)", view[cols].to_csv(index=False), f"{cid}_risk.csv", "text/csv")
st.info(DISCLAIMER)
