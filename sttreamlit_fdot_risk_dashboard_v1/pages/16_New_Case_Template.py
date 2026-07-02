# -*- coding: utf-8 -*-
"""New Case Mode: download the official Excel template → fill → upload → validate → Run → outputs.
No automatic PDF parsing. All risk computed by core_engine.case_runner (validated logic)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core_engine import case_runner as cr, template_io as tio, audit_logger as al

RISK_COLORS = {"Normal": "#2ca25f", "Watch": "#4292c6", "Moderate": "#ffd92f", "High": "#fe9929", "Critical": "#cc4c02", "Not available": "#bdbdbd"}
ORDER = ["Normal", "Watch", "Moderate", "High", "Critical"]

st.set_page_config(page_title="New Case (Template)", page_icon="🆕", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("🆕 New Case — official input template")
st.caption("Bring ANY new project by filling the standardized template (we do NOT auto-parse arbitrary PDFs). "
           "The filled file runs through the SAME validated engine as the built-in cases.")
st.info("**Abnormal pricing risk / commercial review** — not fraud detection.")

st.subheader("① Download the official template")
c1, c2 = st.columns([1, 3])
nb = c1.number_input("Number of bidder columns", 1, 12, 4)
c2.download_button("⬇️ Download Bid-Tab template (.xlsx)", tio.build_template(int(nb)),
                   "fdot_bidtab_input_template.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("bidder1 = winning bidder. Use `actual_unit_price` (single column) instead of bidder columns if you only have the awarded price. "
           "Filling `item_id` + matching unit unlocks the official FDOT 2024 historical benchmark.")

st.subheader("② Upload the filled template")
case_id = st.text_input("Case name / id", value="NEW_CASE_001")
up = st.file_uploader("Upload filled template (.xlsx or .csv)", type=["xlsx", "csv"])
if up:
    if up.name.endswith(".csv"):
        df = pd.read_csv(up)
    else:
        xl = pd.ExcelFile(up)
        sheet = "BidTab_Input" if "BidTab_Input" in xl.sheet_names else xl.sheet_names[0]
        df = pd.read_excel(up, sheet_name=sheet)
    df = df.dropna(how="all")
    st.caption(f"Loaded {len(df)} rows from `{up.name}`.")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    st.subheader("③ Validation (before risk)")
    v = cr.validate_bidtab(df)
    if v["errors"]:
        for e in v["errors"]: st.error(e)
        st.stop()
    st.success(f"Validation passed — {v['n_items']} items, {v['n_bidders']} bidders, mode = {v['mode']}.")
    for w in v["warnings"]: st.warning(w)

    if st.button("▶ Run risk analysis", type="primary"):
        with st.spinner("Running validated engine…"):
            res, summ = cr.run_case(df, winner_col="bidder1_unit_price")
        st.subheader("④ Risk results")
        k = st.columns(4)
        k[0].metric("Overpricing exposure", f"${summ['overpricing_exposure']:,.0f}",
                    f"{summ['exposure_pct_of_bid']:.1f}% of bid" if pd.notna(summ['exposure_pct_of_bid']) else None)
        k[1].metric("High + Critical", int(summ['risk_distribution']['High'] + summ['risk_distribution']['Critical']))
        k[2].metric("Confirmed-by-both", summ["confirmed_by_both"])
        k[3].metric("Historical coverage", f"{summ['historical_coverage_pct']:.0f}%")

        c1, c2 = st.columns(2)
        with c1:
            rd = pd.Series(summ["risk_distribution"]).reindex(ORDER).reset_index(); rd.columns = ["flag", "items"]
            fig = px.bar(rd, x="flag", y="items", color="flag", color_discrete_map=RISK_COLORS, category_orders={"flag": ORDER})
            fig.update_layout(showlegend=False, height=320, title="Combined risk distribution"); st.plotly_chart(fig, use_container_width=True)
        with c2:
            g = res.copy();
            fig2 = px.scatter(g, x=g.deviation_vs_market.clip(-150, 300), y="overpricing_exposure", color="combined_risk_flag",
                              color_discrete_map=RISK_COLORS, category_orders={"combined_risk_flag": ORDER},
                              hover_data=["item_id", "description"], labels={"x": "deviation vs market %"})
            fig2.update_yaxes(type="log"); fig2.update_layout(height=320, title="Risk matrix"); st.plotly_chart(fig2, use_container_width=True)

        st.subheader("⑤ Item-by-item (with confidence & data-quality)")
        cols = [c for c in tio.DISPLAY if c in res.columns]
        st.dataframe(res[cols].sort_values("overpricing_exposure", ascending=False), use_container_width=True, hide_index=True,
                     column_config={"deviation_vs_market": st.column_config.NumberColumn("dev mkt %", format="%.1f"),
                                    "overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
                                    "actual_unit_price": st.column_config.NumberColumn("winner $", format="$%.2f")})

        st.subheader("⑥ Download official outputs")
        d1, d2, d3 = st.columns(3)
        d1.download_button("⬇️ Excel report", tio.result_excel(res, summ, case_id), f"{case_id}_risk_report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        d2.download_button("⬇️ CSV (item-level)", tio.result_csv(res), f"{case_id}_risk_item_level.csv", "text/csv")
        d3.download_button("⬇️ JSON", tio.result_json(res, summ, case_id), f"{case_id}_risk.json", "application/json")
        al.log_run("new_case_template", {"case_id": case_id, "file": up.name, "items": summ["n_items"]},
                   {"exposure": summ["overpricing_exposure"]})
        with st.expander("🧾 Audit (engine versions used in this run)"):
            st.json(al.versions())
