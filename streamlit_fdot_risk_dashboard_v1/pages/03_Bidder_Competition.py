# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_bidders

st.set_page_config(page_title="Bidder Competition", page_icon="🏗️", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("🏗️ Bidder Competition")
st.caption("The real competitive market behind the primary benchmark: multiple contractors bidding the same items on the same date.")
bidders = load_bidders()
if bidders.empty:
    st.warning("Bidder summary not bundled."); st.stop()

cid = st.selectbox("Select case", sorted(bidders.case_id.unique()))
bb = bidders[bidders.case_id == cid].sort_values("bidder_rank")
st.subheader("Bidder ranking")
st.dataframe(bb[["bidder_rank", "bidder_name", "bid_status", "total_bid", "percent_of_low_bid"]],
             use_container_width=True, hide_index=True,
             column_config={"total_bid": st.column_config.NumberColumn("total bid $", format="$%.0f"),
                            "percent_of_low_bid": st.column_config.NumberColumn("% of low bid", format="%.2f%%")})
c1, c2 = st.columns(2)
with c1:
    fig = px.bar(bb, x="bidder_name", y="total_bid",
                 color=(bb.bid_status == "Winning bid").map({True: "winner", False: "other"}),
                 color_discrete_map={"winner": "#2ca25f", "other": "#9ecae1"}, title="Total bid by bidder")
    fig.update_layout(showlegend=False, height=380, xaxis_tickangle=-30); st.plotly_chart(fig, use_container_width=True)
with c2:
    fig2 = px.bar(bb, x="bidder_name", y="percent_of_low_bid", title="Percent over low bid")
    fig2.update_layout(height=380, xaxis_tickangle=-30); st.plotly_chart(fig2, use_container_width=True)

spread = (bb.total_bid.max() - bb.total_bid.min()) / bb.total_bid.min() * 100 if len(bb) else 0
st.metric("Bid spread (max vs low)", f"{spread:.1f}%", help="range of total bids relative to the low bid")
