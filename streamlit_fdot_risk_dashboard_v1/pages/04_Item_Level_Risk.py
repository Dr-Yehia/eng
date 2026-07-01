# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core.data_loader import load_items, RISK_ORDER, DISCLAIMER

st.set_page_config(page_title="Item-Level Risk", page_icon="⚠️", layout="wide")
st.header("⚠️ Item-Level Risk")
st.caption("Interactive, filterable dual-benchmark risk table. Download the filtered view as CSV.")
items = load_items()

sb = st.sidebar
sb.header("Filters")
cs = sb.multiselect("Case", sorted(items.case_id.unique()), default=sorted(items.case_id.unique()))
fl = sb.multiselect("Combined risk flag", [x for x in RISK_ORDER if x != "Not available"],
                    default=["High", "Critical"])
secs = sorted(items.section_name.dropna().unique())
sc = sb.multiselect("Section", secs)
ev = sb.multiselect("Evidence class", sorted(items.evidence_class.dropna().unique()))
kind = sb.radio("Item type", ["All", "Unit-rate only", "Lump-sum only"], index=0)
conf = sb.multiselect("Risk confidence", ["High", "Medium", "Low"])
min_exp = sb.number_input("Min market exposure ($)", value=0, step=1000)
min_dev = sb.number_input("Min |deviation vs market| (%)", value=0, step=5)

f = items[items.case_id.isin(cs) & items.combined_risk_flag.isin(fl)]
if sc: f = f[f.section_name.isin(sc)]
if ev: f = f[f.evidence_class.isin(ev)]
if conf: f = f[f.risk_confidence.isin(conf)]
if kind == "Unit-rate only": f = f[~f.is_lump_sum]
elif kind == "Lump-sum only": f = f[f.is_lump_sum]
f = f[(f.market_overpricing_exposure >= min_exp) & (f.deviation_vs_market.abs() >= min_dev)]

c = st.columns(4)
c[0].metric("Items shown", f"{len(f):,}")
c[1].metric("Market overpricing exposure", f"${f.market_overpricing_exposure.sum():,.0f}")
c[2].metric("High + Critical", int(f.combined_risk_flag.isin(['High', 'Critical']).sum()))
c[3].metric("Confirmed-by-both", int((f.evidence_class == 'confirmed_by_both').sum()))

show = ["case_id", "line_no", "item_id", "description", "section_name", "display_unit", "quantity_display", "is_lump_sum",
        "winner_unit_price", "market_benchmark_unit_price", "deviation_vs_market", "market_overpricing_exposure",
        "historical_benchmark_unit_price", "deviation_vs_historical",
        "market_risk_flag", "historical_risk_flag", "combined_risk_flag", "risk_direction",
        "evidence_class", "risk_confidence", "recommended_action"]
show = [c for c in show if c in f.columns]
st.dataframe(f[show].sort_values("market_overpricing_exposure", ascending=False),
             use_container_width=True, hide_index=True,
             column_config={"deviation_vs_market": st.column_config.NumberColumn("dev mkt %", format="%.1f"),
                            "deviation_vs_historical": st.column_config.NumberColumn("dev hist %", format="%.1f"),
                            "market_overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
                            "winner_unit_price": st.column_config.NumberColumn("winner $", format="$%.2f"),
                            "market_benchmark_unit_price": st.column_config.NumberColumn("market $", format="$%.2f"),
                            "historical_benchmark_unit_price": st.column_config.NumberColumn("FDOT hist $", format="$%.2f")})
st.download_button("⬇️ Download filtered items (CSV)", f[show].to_csv(index=False), "fdot_risk_filtered.csv", "text/csv")
st.info(DISCLAIMER)
