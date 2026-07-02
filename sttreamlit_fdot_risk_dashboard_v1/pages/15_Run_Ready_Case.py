# -*- coding: utf-8 -*-
"""Ready Case Mode: pick a validated case → (optional) edit prices/qty → Run → live risk + downloads.
UI only; all risk computed by core_engine.case_runner (validated dual-benchmark logic)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core_engine import case_runner as cr, template_io as tio, audit_logger as al
from core_engine import assets

RC = os.path.join(assets.AST, "ready_cases")
RISK_COLORS = {"Normal": "#2ca25f", "Watch": "#4292c6", "Moderate": "#ffd92f", "High": "#fe9929", "Critical": "#cc4c02", "Not available": "#bdbdbd"}
ORDER = ["Normal", "Watch", "Moderate", "High", "Critical"]

st.set_page_config(page_title="Run Ready Case", page_icon="▶️", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("▶️ Ready Case — run live, item by item")
st.caption("Pick a validated FDOT case, optionally edit unit prices/quantities, then Run. "
           "Everything is computed live by the validated engine (bidder-market + FDOT historical + statistical thresholds).")
st.info("**Abnormal pricing risk / commercial review** — not fraud detection.")

man = json.load(open(os.path.join(RC, "_manifest.json"), encoding="utf-8"))
mdf = pd.DataFrame(man)
labels = {f"{m['case_id']} — {m['project_type']} ({m['n_bidders']} bidders, {m['n_items']} items)" + (" · SENSITIVITY" if m["case_role"] == "sensitivity" else ""): m["case_id"] for m in man}
pick = st.selectbox("Select case", list(labels))
cid = labels[pick]; meta = mdf[mdf.case_id == cid].iloc[0]
if meta["case_role"] == "sensitivity":
    st.warning(f"**{cid}** is a sensitivity case ({int(meta['n_bidders'])} bidders) — interpret with caution, not equal to main cases.")

df = pd.read_parquet(os.path.join(RC, f"{cid}.parquet"))
st.caption(f"Winner (bidder1): **{meta['winner']}** · winning total ${meta['winning_total_bid']:,.0f} · letting {meta['letting_date']}")

# Display-only unit: show 'LS' for lump-sum items (raw data stores unit=None); never alters values fed to the engine.
def _disp_unit(r):
    u = r.get("unit")
    if pd.notna(u) and str(u).strip() not in ("", "None"):
        return u
    return "LS" if r.get("is_lump_sum") else "—"
df_disp = df.copy()
if "unit" in df_disp.columns:
    df_disp["unit"] = df_disp.apply(_disp_unit, axis=1)

edit = st.toggle("✏️ Enable editing (adjust prices / quantities before running)", value=False)
if edit:
    st.caption("Edit cells then Run. Original validated data is untouched on disk. (Unit is display-only.)")
    edited = st.data_editor(df_disp, use_container_width=True, num_rows="fixed", height=300, key=f"ed_{cid}",
                            column_config={"unit": st.column_config.TextColumn("unit", disabled=True)})
    df_in = edited.copy()
    if "unit" in df_in.columns:
        df_in["unit"] = df["unit"].values  # restore original units for computation (reproducibility)
else:
    st.dataframe(df_disp.head(12), use_container_width=True, hide_index=True)
    df_in = df

if st.button("▶ Run risk analysis", type="primary"):
    v = cr.validate_bidtab(df_in)
    st.subheader("① Validation (before risk)")
    if v["errors"]:
        for e in v["errors"]: st.error(e)
        st.stop()
    st.success(f"Validation passed — {v['n_items']} items, {v['n_bidders']} bidders, mode = {v['mode']}.")
    for w in v["warnings"]: st.warning(w)

    with st.spinner("Running validated engine…"):
        res, summ = cr.run_case(df_in, winner_col="bidder1_unit_price", winning_total=float(meta["winning_total_bid"]))
    st.subheader("② Risk results")
    k = st.columns(4)
    k[0].metric("Overpricing exposure", f"${summ['overpricing_exposure']:,.0f}", f"{summ['exposure_pct_of_bid']:.1f}% of bid")
    k[1].metric("High + Critical", int(summ['risk_distribution']['High'] + summ['risk_distribution']['Critical']))
    k[2].metric("Confirmed-by-both", summ["confirmed_by_both"])
    k[3].metric("Historical coverage", f"{summ['historical_coverage_pct']:.0f}%")

    c1, c2 = st.columns(2)
    with c1:
        rd = pd.Series(summ["risk_distribution"]).reindex(ORDER).reset_index(); rd.columns = ["flag", "items"]
        fig = px.bar(rd, x="flag", y="items", color="flag", color_discrete_map=RISK_COLORS, category_orders={"flag": ORDER})
        fig.update_layout(showlegend=False, height=320, title="Combined risk distribution"); st.plotly_chart(fig, use_container_width=True)
    with c2:
        g = res.copy(); g["amt"] = g.actual_unit_price * g.quantity.clip(lower=1)
        fig2 = px.scatter(g, x=g.deviation_vs_market.clip(-150, 300), y="overpricing_exposure", color="combined_risk_flag",
                          color_discrete_map=RISK_COLORS, category_orders={"combined_risk_flag": ORDER},
                          hover_data=["item_id", "description"], labels={"x": "deviation vs market %"})
        fig2.update_yaxes(type="log"); fig2.update_layout(height=320, title="Risk matrix"); st.plotly_chart(fig2, use_container_width=True)

    st.subheader("③ Item-by-item (with confidence & data-quality)")
    cols = [c for c in tio.DISPLAY if c in res.columns]
    st.dataframe(res[cols].sort_values("overpricing_exposure", ascending=False), use_container_width=True, hide_index=True,
                 column_config={"deviation_vs_market": st.column_config.NumberColumn("dev mkt %", format="%.1f"),
                                "deviation_vs_historical": st.column_config.NumberColumn("dev hist %", format="%.1f"),
                                "overpricing_exposure": st.column_config.NumberColumn("exposure $", format="$%.0f"),
                                "actual_unit_price": st.column_config.NumberColumn("winner $", format="$%.2f")})

    st.subheader("④ Download official outputs")
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇️ Excel report", tio.result_excel(res, summ, cid), f"{cid}_risk_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d2.download_button("⬇️ CSV (item-level)", tio.result_csv(res), f"{cid}_risk_item_level.csv", "text/csv")
    d3.download_button("⬇️ JSON", tio.result_json(res, summ, cid), f"{cid}_risk.json", "application/json")
    al.log_run("ready_case", {"case_id": cid, "edited": edit, "items": summ["n_items"]},
               {"exposure": summ["overpricing_exposure"], "high_critical": int(summ['risk_distribution']['High'] + summ['risk_distribution']['Critical'])})
    with st.expander("🧾 Audit (engine versions used in this run)"):
        st.json(al.versions())
