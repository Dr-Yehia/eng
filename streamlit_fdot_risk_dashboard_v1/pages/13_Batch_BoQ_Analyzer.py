# -*- coding: utf-8 -*-
"""Batch BoQ Analyzer — upload a table, run the SAME engines per row, download results."""
import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core_engine import prediction_engine as pe, escalation_engine as ee, risk_engine as rk
from core_engine import matching_engine as me, audit_logger as al

st.set_page_config(page_title="Batch BoQ Analyzer", page_icon="📥", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("📥 Batch BoQ Analyzer")
st.caption("Upload a BoQ table → each row runs through the validated engines "
           "(prediction → escalation → risk when actual price given). Max 300 rows per run.")
st.info("**Abnormal pricing risk / commercial review** — not fraud detection. "
        "Rows without item_id or composition get LOW/preliminary confidence by design.")

TEMPLATE = pd.DataFrame([{"description": "Milling existing asphalt pavement, 1.5 inch", "unit": "SY",
                          "quantity": 64672, "target_date": "2026-05-01", "item_id": "0327 70 2",
                          "division": "", "actual_unit_price": 4.65, "is_lump_sum": False},
                         {"description": "Maintenance of traffic", "unit": "LS", "quantity": 1,
                          "target_date": "2026-05-01", "item_id": "", "division": "",
                          "actual_unit_price": 216730, "is_lump_sum": True}])
st.download_button("⬇️ Download input template (CSV)", TEMPLATE.to_csv(index=False),
                   "boq_template.csv", "text/csv")

up = st.file_uploader("Upload BoQ (CSV or Excel with the template columns)", type=["csv", "xlsx"])
if up:
    df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
    need = {"description", "unit", "quantity", "target_date"}
    if not need.issubset(df.columns):
        st.error(f"Missing required columns: {sorted(need - set(df.columns))}"); st.stop()
    df = df.head(300)
    rows, prog = [], st.progress(0.0, text="Running engines…")
    for i, r in df.iterrows():
        try:
            pred = pe.predict_benchmark(str(r["description"]), str(r["unit"]),
                                        division=(str(r.get("division")) or None) if pd.notna(r.get("division")) else None)
            esc = ee.escalate(pred["expected_benchmark_unit_price"], r["target_date"])
            hist = me.match_fdot_historical(str(r.get("item_id", "")), str(r["unit"])) if pd.notna(r.get("item_id")) and str(r.get("item_id")).strip() else None
            hist_ok = bool(hist and hist.get("status") == "matched")
            conf = "High" if hist_ok else pred["confidence"]
            out = {"description": str(r["description"])[:60], "unit": r["unit"], "quantity": r["quantity"],
                   "expected_benchmark_unit_price": round(esc["escalated_price"], 4),
                   "interval_low": round(pred["interval_low"] * esc["escalation_factor"], 4),
                   "interval_high": round(pred["interval_high"] * esc["escalation_factor"], 4),
                   "escalation_factor": round(esc["escalation_factor"], 4),
                   "fdot_historical": hist["wavg"] if hist_ok else None, "confidence": conf}
            actual = r.get("actual_unit_price")
            if pd.notna(actual) and float(actual) > 0:
                a = rk.assess(float(actual), float(r["quantity"]), esc["escalated_price"],
                              historical=hist, is_lump_sum=bool(r.get("is_lump_sum", False)),
                              benchmark_confidence=conf)
                out.update({"actual_unit_price": float(actual),
                            "risk_flag": a["combined_risk_flag"],
                            "deviation_pct": None if a["primary_deviation_pct"] is None else round(a["primary_deviation_pct"], 1),
                            "evidence_class": a["evidence_class"], "risk_confidence": a["risk_confidence"],
                            "overpricing_exposure": round(a["overpricing_exposure"], 0),
                            "recommended_action": a["recommended_action"]})
            rows.append(out)
        except Exception as ex:
            rows.append({"description": str(r.get("description", ""))[:60], "error": str(ex)[:100]})
        prog.progress((i + 1) / len(df), text=f"Row {i+1}/{len(df)}")
    res = pd.DataFrame(rows)
    st.success(f"Done — {len(res)} rows processed.")
    if "risk_flag" in res:
        k = st.columns(4)
        k[0].metric("High + Critical", int(res["risk_flag"].isin(["High", "Critical"]).sum()))
        k[1].metric("Total overpricing exposure", f"${pd.to_numeric(res.get('overpricing_exposure'), errors='coerce').sum():,.0f}")
        k[2].metric("Historical-matched rows", int(res["fdot_historical"].notna().sum()))
        k[3].metric("Low-confidence rows", int((res["confidence"] == "Low").sum()))
    st.dataframe(res, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download results (CSV)", res.to_csv(index=False), "boq_engine_results.csv", "text/csv")
    al.log_run("batch_boq", {"rows": len(res), "file": up.name},
               {"high_critical": int(res.get("risk_flag", pd.Series(dtype=str)).isin(["High", "Critical"]).sum())})
    with st.expander("🧾 Audit trail (versions)"):
        st.json(al.versions())
