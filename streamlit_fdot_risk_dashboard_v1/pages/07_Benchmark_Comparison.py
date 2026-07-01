# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_items, PRIMARY_NOTE

st.set_page_config(page_title="Benchmark Comparison", page_icon="📊", layout="wide")
st.header("📊 Benchmark Comparison")
st.caption(PRIMARY_NOTE)
items = load_items()

c1, c2 = st.columns(2)
cid = c1.selectbox("Case", sorted(items.case_id.unique()))
ci = items[items.case_id == cid]
label = ci.line_no.astype(str) + " — " + ci.description.astype(str).str.slice(0, 60)
pick = c2.selectbox("Item", label.tolist())
row = ci.iloc[label.tolist().index(pick)]

st.subheader(row["description"])
st.caption(f"Case {cid} · line {row['line_no']} · unit {row.get('unit','-')} · quantity {row.get('quantity','-')}")

benches = [
    ("Winner (actual)", row.get("winner_unit_price")),
    ("Contractor market (non-winner median) — PRIMARY", row.get("market_benchmark_unit_price")),
    ("FDOT historical 2024 (weighted avg) — PRIMARY", row.get("historical_benchmark_unit_price")),
]
rows = [{"benchmark": b, "unit_price": v, "available": pd.notna(v)} for b, v in benches]
# ML only if a strong match exists (integrated keeps ml supporting; show status)
ml_status = row.get("ml_match_status", "no_match")
rows.append({"benchmark": f"ML DDC (supporting — {ml_status})", "unit_price": np.nan, "available": False})
bdf = pd.DataFrame(rows)
avail = bdf[bdf.available]
L, R = st.columns([2, 1])
with L:
    fig = px.bar(avail, x="unit_price", y="benchmark", orientation="h",
                 color=avail.benchmark.str.contains("Winner").map({True: "winner", False: "benchmark"}),
                 color_discrete_map={"winner": "#cc4c02", "benchmark": "#3182bd"},
                 labels={"unit_price": "unit price (USD)"})
    fig.update_layout(showlegend=False, height=320, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Unavailable benchmarks are listed but NOT shown as zero:")
    for _, r in bdf[~bdf.available].iterrows():
        st.write(f"• {r['benchmark']}: **Not available in current version**")
with R:
    st.metric("Deviation vs market", f"{row.get('deviation_vs_market', float('nan')):.1f}%")
    if pd.notna(row.get("deviation_vs_historical")):
        st.metric("Deviation vs FDOT historical", f"{row.get('deviation_vs_historical'):.1f}%")
    st.metric("Market overpricing exposure", f"${row.get('market_overpricing_exposure',0):,.0f}")
    st.markdown(f"**Combined risk:** {row.get('combined_risk_flag')}  \n"
                f"**Evidence:** {row.get('evidence_class')}  \n"
                f"**Confidence:** {row.get('risk_confidence')}  \n"
                f"**Direction:** {row.get('risk_direction')}  \n"
                f"**Action:** {row.get('recommended_action')}")
