# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_items, RISK_ORDER, RISK_COLORS

st.set_page_config(page_title="Risk Matrix", page_icon="🎯", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("🎯 Risk Matrix — deviation vs financial exposure")
st.caption("Separates 'large % deviation but small value' from 'moderate deviation but large financial impact'.")
items = load_items().copy()

mode = st.radio("Items", ["All", "Unit-rate only", "Lump-sum only"], horizontal=True)
if mode == "Unit-rate only": items = items[~items.is_lump_sum]
elif mode == "Lump-sum only": items = items[items.is_lump_sum]
items["item_amount"] = items.winner_unit_price * items.quantity.clip(lower=1)
items["dev_clip"] = items.deviation_vs_market.clip(-150, 300)

# The log Y-axis only shows items that actually carry market-overpricing exposure (>0);
# items priced at/below market have zero exposure and are not part of the overpricing matrix.
n_total = len(items)
plot = items[items.market_overpricing_exposure > 0].copy()
n_zero = n_total - len(plot)
# Compress bubble sizing so a few very-large lump-sum items don't swamp the rest.
plot["bubble"] = np.sqrt(plot["item_amount"].clip(lower=1))

fig = px.scatter(plot, x="dev_clip", y="market_overpricing_exposure",
                 color="combined_risk_flag", color_discrete_map=RISK_COLORS,
                 category_orders={"combined_risk_flag": RISK_ORDER},
                 size="bubble", size_max=18, opacity=0.55,
                 hover_data={"case_id": True, "item_id": True, "description": True,
                             "deviation_vs_market": ":.1f", "market_overpricing_exposure": ":,.0f",
                             "dev_clip": False, "bubble": False},
                 labels={"dev_clip": "deviation vs market (%)", "market_overpricing_exposure": "market overpricing exposure ($)"})
fig.update_layout(height=560, legend_title="risk flag")
fig.update_yaxes(type="log")
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Showing {len(plot):,} items with market-overpricing exposure > 0. "
           f"{n_zero:,} items priced at/below market (zero exposure) are omitted from this log-scaled view. "
           "Bubble size ≈ √(item total amount); Y-axis is log-scaled exposure.")
