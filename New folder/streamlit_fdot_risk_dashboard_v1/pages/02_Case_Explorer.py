# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_items, load_case_summary, load_bidders, RISK_ORDER, RISK_COLORS

st.set_page_config(page_title="Case Explorer", page_icon="📋", layout="wide")
st.header("📋 Case Explorer")
items = load_items(); cs = load_case_summary(); bidders = load_bidders()

cid = st.selectbox("Select case", sorted(items.case_id.unique()))
ci = items[items.case_id == cid]
meta = ci.iloc[0]
role = meta.get("case_role", "")
if role == "sensitivity":
    st.warning(f"**{cid}** is a **sensitivity case** ({int(meta.get('bidder_count',0))} bidders) — do not weight it equally with the main validation cases.")

m = st.columns(4)
m[0].markdown(f"**Contract**\n\n{meta.get('contract_id','-')}")
m[1].markdown(f"**Letting date**\n\n{meta.get('letting_date','-')}")
m[2].markdown(f"**District**\n\n{meta.get('district','-')}")
m[3].markdown(f"**Bidders**\n\n{int(meta.get('bidder_count',0))} ({meta.get('bidder_count_confidence','')})")
k = st.columns(4)
k[0].metric("Winner", str(meta.get("winner", "-"))[:24])
k[1].metric("Winning bid", f"${meta.get('winning_total_bid',0)/1e6:,.2f}M")
k[2].metric("Pay items", f"{len(ci)}")
k[3].metric("Market overpricing exposure", f"${ci['market_overpricing_exposure'].sum():,.0f}")
st.divider()

L, R = st.columns(2)
with L:
    st.subheader("Risk distribution")
    rd = ci["combined_risk_flag"].value_counts().reindex(RISK_ORDER).dropna().reset_index()
    rd.columns = ["risk_flag", "items"]
    fig = px.bar(rd, x="risk_flag", y="items", color="risk_flag", color_discrete_map=RISK_COLORS,
                 category_orders={"risk_flag": RISK_ORDER})
    fig.update_layout(showlegend=False, height=340, margin=dict(t=10)); st.plotly_chart(fig, use_container_width=True)
    lump = int(ci.is_lump_sum.sum())
    st.caption(f"Unit-rate items: **{len(ci)-lump}** · Lump-sum items (reviewed separately): **{lump}**")
with R:
    st.subheader("Bidder totals")
    bb = bidders[bidders.case_id == cid].sort_values("bidder_rank") if len(bidders) else pd.DataFrame()
    if len(bb):
        fig2 = px.bar(bb, x="total_bid", y="bidder_name", orientation="h",
                      color=(bb.bid_status == "Winning bid").map({True: "winner", False: "other"}),
                      color_discrete_map={"winner": "#2ca25f", "other": "#9ecae1"},
                      hover_data=["bidder_rank", "percent_of_low_bid"])
        fig2.update_layout(height=340, margin=dict(t=10), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

st.subheader(f"Top overpricing-exposure items — {cid}")
top = ci.nlargest(15, "market_overpricing_exposure")[
    ["line_no", "description", "display_unit", "quantity_display", "winner_unit_price", "market_benchmark_unit_price",
     "historical_benchmark_unit_price", "deviation_vs_market", "market_overpricing_exposure",
     "combined_risk_flag", "evidence_class", "risk_confidence"]]
st.dataframe(top, use_container_width=True, hide_index=True,
             column_config={"deviation_vs_market": st.column_config.NumberColumn("dev vs mkt %", format="%.1f"),
                            "market_overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f")})
