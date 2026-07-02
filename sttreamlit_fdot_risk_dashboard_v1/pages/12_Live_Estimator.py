# -*- coding: utf-8 -*-
"""Live Estimator — Mode B (Risk Checker, default) + Mode A (Benchmark Estimator).
UI ONLY: every number comes from core_engine (the validated research engines)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st
from core_engine import prediction_engine as pe, escalation_engine as ee
from core_engine import calibration_engine as ce, risk_engine as rk
from core_engine import matching_engine as me, audit_logger as al

st.set_page_config(page_title="Live Estimator", page_icon="🧮", layout="wide")
st.header("🧮 Live Estimator — interactive engine")
st.caption("Calls the SAME validated engines (model, escalation, calibration, risk thresholds). "
           "Output = **expected benchmark unit price** — never a guaranteed market/'fair' price.")
st.info("**Abnormal pricing risk / commercial review** — this tool does not claim fraud detection.")

mode = st.radio("Mode", ["🅱️ Risk Checker — is this quoted price abnormal?",
                         "🅰️ Benchmark Estimator — expected benchmark price"], horizontal=True)
is_b = mode.startswith("🅱️")
market = st.radio("Market", ["🇺🇸 United States", "🇦🇪 UAE (region-calibrated benchmark)"], horizontal=True)
uae = market.startswith("🇦🇪")

with st.form("estimator"):
    c1, c2 = st.columns([2, 1])
    desc = c1.text_input("Item description *", placeholder="e.g. Milling existing asphalt pavement, 1.5 inch avg depth")
    unit = c2.selectbox("Unit *", ["SY", "TN", "LF", "SF", "CY", "EA", "GAL", "AC", "LS", "DA", "AS", "PI"])
    c3, c4, c5 = st.columns(3)
    qty = c3.number_input("Quantity *", min_value=0.0, value=1000.0)
    tdate = c4.date_input("Target pricing date *", value=pd.Timestamp("2026-05-01"))
    actual = c5.number_input("Actual / quoted unit price ($)" + (" *" if is_b else " (optional)"),
                             min_value=0.0, value=0.0)
    with st.expander("Optional inputs — RAISE confidence (item_id unlocks the official FDOT historical benchmark)"):
        o1, o2 = st.columns(2)
        item_id = o1.text_input("FDOT pay item number", placeholder="e.g. 0327 70 2")
        division = o2.text_input("MasterFormat division", placeholder="e.g. 32 10 00")
        o3, o4, o5, o6 = st.columns(4)
        mat = o3.number_input("Material count", min_value=0, value=0)
        mach = o4.number_input("Machine count", min_value=0, value=0)
        lab = o5.number_input("Labor hours / unit", min_value=0.0, value=0.0)
        elec = o6.number_input("Electricity kWh", min_value=0.0, value=0.0)
        res_txt = st.text_input("Resource names (free text)", placeholder="e.g. milling machine, sweeper, operator")
        is_ls = st.checkbox("Lump-sum item", value=(unit == "LS"))
    go = st.form_submit_button("▶ Run engines", type="primary")

if go:
    if not desc.strip():
        st.error("Description is required."); st.stop()
    if is_b and actual <= 0:
        st.error("Risk Checker needs the actual/quoted unit price."); st.stop()
    comp = {k: v for k, v in {"material_count": mat or None, "machine_count": mach or None,
                              "labor_hours": lab or None, "electricity_kwh": elec or None,
                              "resource_names": res_txt or None}.items() if v}
    with st.spinner("Running validated engines…"):
        pred = pe.predict_benchmark(desc, unit, division=division or None, composition=comp or None)
        esc = ee.escalate(pred["expected_benchmark_unit_price"], tdate, composition=comp or None)
        hist = me.match_fdot_historical(item_id, unit) if item_id.strip() else None
        hist_ok = bool(hist and hist.get("status") == "matched")
        conf = "High" if hist_ok else pred["confidence"]

    # ---------- result card ----------
    st.divider()
    price = esc["escalated_price"]
    k = st.columns(4)
    k[0].metric("Expected benchmark unit price", f"${price:,.2f} / {unit}",
                help=f"base ${pred['expected_benchmark_unit_price']:,.2f} at {pred['base_date'][:7]} × escalation {esc['escalation_factor']:.4f}")
    k[1].metric("Prediction interval (indicative)",
                f"${pred['interval_low']*esc['escalation_factor']:,.2f} – ${pred['interval_high']*esc['escalation_factor']:,.2f}")
    k[2].metric("Estimated item total", f"${price * (1 if is_ls else qty):,.0f}")
    badge = {"High": "🟢", "Medium-High": "🟡", "Medium": "🟡", "Medium-Low": "🟠", "Low": "🔴"}.get(conf, "⚪")
    k[3].metric("Confidence", f"{badge} {conf}")
    st.caption(f"**Why this confidence:** {('FDOT item_id matched to the official 2024 historical benchmark.') if hist_ok else pred['confidence_reason']}  ·  {pred['imputation_note']}")

    if hist_ok:
        st.success(f"🏛️ **FDOT historical 2024 benchmark matched**: ${hist['wavg']:,.2f} / {hist['hunit']} "
                   "(official statewide weighted average — strongest single-item benchmark).")
    elif hist and hist.get("status") == "unit_mismatch":
        st.warning(f"item_id found but unit differs (FDOT unit = {hist['hunit']}) — historical benchmark not applied.")

    with st.expander("⏱ Escalation breakdown (frozen BLS snapshot)"):
        st.write(f"Base {esc['base_month'][:7]} → target used {esc['target_month_used'][:7]} · "
                 f"indices as of **{esc['index_as_of']}** · {esc['weights_note']}")
        st.dataframe(pd.DataFrame({"family": list(esc["F_by_family"]),
                                   "F (target/base)": [f"{v:.4f}" for v in esc["F_by_family"].values()],
                                   "weight": [f"{esc['weights'][f]:.2f}" for f in esc["F_by_family"]]}),
                     hide_index=True, use_container_width=True)
        for w in esc["warnings"]: st.warning(w)
    with st.expander("🔎 Nearest DDC catalog reference (retrieval cross-check)"):
        st.dataframe(pd.DataFrame(pred["ddc_matches"])[["rate_final_name", "score", "match_status",
                                                        "predicted_base_unit_price", "base_unit"]],
                     hide_index=True, use_container_width=True)

    if uae:
        u = ce.to_uae(price, pe._dimension(unit), division or None)
        st.subheader("🇦🇪 UAE — region-calibrated benchmark")
        u1, u2, u3 = st.columns(3)
        u1.metric("Expected benchmark price", f"{u['expected_benchmark_price_aed']:,.2f} AED / {u['aed_unit']}")
        u2.metric("Calibration factor", f"{u['calibration_factor']:.3f}", help=u["calibration_level"])
        u3.metric("Unit × FX", f"×{u['unit_conversion_factor']:.3f} · {u['fx_usd_aed']} AED/USD")
        st.warning(u["caveat"])

    if is_b:
        st.subheader("⚠️ Abnormal-pricing-risk assessment")
        r = rk.assess(actual, qty, price, historical=hist, is_lump_sum=is_ls, benchmark_confidence=conf)
        b1, b2, b3, b4 = st.columns(4)
        col = {"Normal": "🟢", "Watch": "🔵", "Moderate": "🟡", "High": "🟠", "Critical": "🔴"}.get(r["combined_risk_flag"], "⚪")
        b1.metric("Risk flag", f"{col} {r['combined_risk_flag']}")
        b2.metric("Primary deviation", f"{r['primary_deviation_pct']:+.1f}%" if r["primary_deviation_pct"] is not None else "—",
                  help=f"evidence: {r['evidence_class']}")
        b3.metric("Overpricing exposure", f"${r['overpricing_exposure']:,.0f}")
        b4.metric("Risk confidence", r["risk_confidence"])
        st.markdown(f"**Recommended action:** {r['recommended_action']}  ·  direction: *{r['risk_direction']}*")
        st.dataframe(pd.DataFrame([{"benchmark": k2, **v} for k2, v in r["benchmarks"].items()]),
                     hide_index=True, use_container_width=True)
        al.log_run("risk_checker", {"desc": desc[:60], "unit": unit, "qty": qty, "actual": actual,
                                    "item_id": item_id, "uae": uae},
                   {"flag": r["combined_risk_flag"], "dev": r["primary_deviation_pct"],
                    "exposure": r["overpricing_exposure"], "confidence": r["risk_confidence"]})
    else:
        al.log_run("benchmark_estimator", {"desc": desc[:60], "unit": unit, "qty": qty, "uae": uae},
                   {"price": price, "confidence": conf})
    with st.expander("🧾 Audit trail (versions used in THIS run)"):
        st.json(al.versions())
