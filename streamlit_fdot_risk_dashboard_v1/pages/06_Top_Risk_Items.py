# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core.data_loader import load_items

st.set_page_config(page_title="Top Risk Items", page_icon="🔺", layout="wide")
st.header("🔺 Top Risk Items")
items = load_items()
COLS = ["case_id", "item_id", "description", "display_unit", "quantity_display", "winner_unit_price",
        "market_benchmark_unit_price", "deviation_vs_market", "market_overpricing_exposure",
        "combined_risk_flag", "risk_direction", "recommended_action"]
COLS = [c for c in COLS if c in items.columns]
cfg = {"deviation_vs_market": st.column_config.NumberColumn("dev vs mkt %", format="%.1f"),
       "market_overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
       "winner_unit_price": st.column_config.NumberColumn("winner $", format="$%.2f"),
       "market_benchmark_unit_price": st.column_config.NumberColumn("market $", format="$%.2f")}

t1, t2, t3, t4 = st.tabs(["🔺 Top overpricing exposure", "🔻 Top underpricing", "🚨 Top Critical", "↔️ Widest deviation"])
with t1:
    st.dataframe(items.nlargest(20, "market_overpricing_exposure")[COLS], use_container_width=True, hide_index=True, column_config=cfg)
with t2:
    st.caption("Winner far BELOW market — possible unbalanced underpricing (review, not necessarily good).")
    st.dataframe(items.nsmallest(20, "deviation_vs_market")[COLS], use_container_width=True, hide_index=True, column_config=cfg)
with t3:
    st.dataframe(items[items.combined_risk_flag == "Critical"].nlargest(20, "market_overpricing_exposure")[COLS],
                 use_container_width=True, hide_index=True, column_config=cfg)
with t4:
    it = items.assign(absdev=items.deviation_vs_market.abs())
    st.dataframe(it.nlargest(20, "absdev")[COLS], use_container_width=True, hide_index=True, column_config=cfg)
