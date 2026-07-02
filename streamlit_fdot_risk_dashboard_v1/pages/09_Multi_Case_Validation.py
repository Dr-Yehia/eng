# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_items, load_case_summary, load_lineage, RISK_ORDER, RISK_COLORS

st.set_page_config(page_title="Multi-Case Validation", page_icon="🧪", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("🧪 Multi-Case Validation")
st.caption("Evidence that the methodology is stable across projects — not a single case.")
items = load_items(); cs = load_case_summary(); lin = load_lineage()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Combined risk distribution by case")
    g = items.groupby(["case_id", "combined_risk_flag"]).size().reset_index(name="items")
    fig = px.bar(g, x="case_id", y="items", color="combined_risk_flag", color_discrete_map=RISK_COLORS,
                 category_orders={"combined_risk_flag": RISK_ORDER}, barmode="stack")
    fig.update_layout(height=380); st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Market overpricing exposure (% of bid) by case")
    ec = cs.copy(); ec["pct"] = ec.market_overpricing_exposure / ec.winning_total_bid * 100
    fig2 = px.bar(ec.sort_values("pct"), x="case_id", y="pct", color="case_role",
                  labels={"pct": "% of winning bid"}, hover_data=["confirmed_by_both"])
    fig2.update_layout(height=380); st.plotly_chart(fig2, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.subheader("Lump-sum vs unit-rate items by case")
    lu = items.assign(kind=items.is_lump_sum.map({True: "lump_sum", False: "unit_rate"})).groupby(["case_id", "kind"]).size().reset_index(name="items")
    fig3 = px.bar(lu, x="case_id", y="items", color="kind", barmode="group"); fig3.update_layout(height=340)
    st.plotly_chart(fig3, use_container_width=True)
with c4:
    st.subheader("Historical benchmark coverage by case")
    fig4 = px.bar(cs.sort_values("historical_coverage"), x="case_id", y="historical_coverage",
                  labels={"historical_coverage": "FDOT historical coverage %"})
    fig4.add_hline(y=90, line_dash="dash", line_color="red")
    fig4.update_layout(height=340); st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.subheader("Validated vs excluded cases")
if len(lin):
    tab = lin[["case_id", "project_type", "n_bidders", "n_items", "extraction_all_pass", "included_in_combined"]].copy()
    tab["status"] = tab.extraction_all_pass.map({True: "✅ validated", False: "⛔ excluded (layout differs)"})
    st.dataframe(tab.drop(columns=["extraction_all_pass"]), use_container_width=True, hide_index=True)
    st.caption("Parser success across all attempted cases: "
               f"**{lin.extraction_all_pass.mean()*100:.0f}%** ({int((lin.extraction_all_pass==True).sum())}/{len(lin)}).")
