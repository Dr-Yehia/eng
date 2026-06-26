# -*- coding: utf-8 -*-
"""FDOT Abnormal Pricing Risk — Scientific multi-case dashboard (Home / Overview)."""
import pandas as pd
import streamlit as st
import altair as alt
from utils import (load_items, load_cases, load_project_summary, DISCLAIMER,
                   RISK_ORDER, RISK_COLORS, kpi_row, page_header)

st.set_page_config(page_title="FDOT Pricing Risk Benchmarking", page_icon="🛣️", layout="wide")

items = load_items()
cases = load_cases()
proj = load_project_summary()
projects = pd.DataFrame(proj["projects"])

st.title("🛣️ Construction Work-Item Unit-Price Benchmarking & Abnormal Pricing Risk")
st.markdown(
    "A surrogate **machine-learning benchmark** for construction unit prices, time-adjusted with official "
    "price indices and applied to **real FDOT bid tabulations** to flag abnormal pricing risk across multiple projects.")
st.info(DISCLAIMER)

# ---- headline KPIs ----
val_cases = projects[projects["case_status"] == "validated"] if "case_status" in projects else projects
kpi_row([
    ("Validated cases", f"{len(val_cases)}", "FDOT projects that passed extraction + risk validation"),
    ("Pay items analysed", f"{int(items.shape[0]):,}", "one row per item per validated case"),
    ("Total overpricing exposure", f"${items['primary_financial_exposure'].sum():,.0f}",
     "winner unit price above the non-winner bidder median × quantity"),
    ("High / Critical items", f"{int(items['risk_flag'].isin(['High','Critical']).sum()):,}",
     "items flagged for review by primary deviation/exposure"),
])

st.divider()
left, right = st.columns(2)

with left:
    page_header("Winning bid by case")
    c = (alt.Chart(val_cases).mark_bar(color="#3182bd")
         .encode(x=alt.X("case_id:N", title="case"),
                 y=alt.Y("winning_total_bid:Q", title="winning total bid (USD)"),
                 tooltip=["case_id", "contract_id", "winner", "winning_total_bid", "letting_date"]))
    st.altair_chart(c, use_container_width=True)

    page_header("Overpricing exposure (% of winning bid)")
    c2 = (alt.Chart(val_cases).mark_bar(color="#cb181d")
          .encode(x=alt.X("case_id:N", title="case"),
                  y=alt.Y("exposure_pct_of_bid:Q", title="exposure (% of bid)"),
                  tooltip=["case_id", "exposure_pct_of_bid", "overpricing_exposure"]))
    st.altair_chart(c2, use_container_width=True)

with right:
    page_header("Risk distribution by case")
    rows = []
    for _, p in val_cases.iterrows():
        for k, v in (p["risk_distribution"] or {}).items():
            rows.append({"case_id": p["case_id"], "risk_flag": k, "items": v})
    rd = pd.DataFrame(rows)
    if len(rd):
        ch = (alt.Chart(rd).mark_bar().encode(
            x=alt.X("case_id:N", title="case"), y=alt.Y("items:Q", stack="normalize", title="share of items"),
            color=alt.Color("risk_flag:N", scale=alt.Scale(domain=RISK_ORDER, range=[RISK_COLORS[k] for k in RISK_ORDER]),
                            sort=RISK_ORDER),
            order=alt.Order("risk_flag:N"), tooltip=["case_id", "risk_flag", "items"]))
        st.altair_chart(ch, use_container_width=True)

    page_header("Case overview")
    show = val_cases[["case_id", "project_type", "n_bidders", "n_items", "exposure_pct_of_bid",
                      "n_critical", "n_high", "letting_date"]].copy() if "project_type" in val_cases else val_cases
    st.dataframe(show, use_container_width=True, hide_index=True)

st.divider()
page_header("Research framework", "Each stage is a validated, reproducible package.")
st.markdown("""
| Stage | What it does | Status |
|---|---|---|
| **1. Clean dataset** | 55,610 work items, no leakage, GroupKFold-ready | ✅ |
| **2. ML benchmark** | XGBoost unit-price model (MdAPE ≈ 14%, out-of-fold) | ✅ |
| **3. Dynamic escalation** | Weighted multi-index, real BLS PPI/CES indices | ✅ |
| **3A. Regional calibration** | US → Dubai (AED) benchmark transfer | ✅ |
| **3B–3C. Risk + multi-case** | Real FDOT bid tabs, abnormal-pricing risk, multi-case validation | ✅ |
| **4. This dashboard** | Interactive decision-support layer | ▶ you are here |

**Primary benchmark = the competitive bidder market** (non-winner median of 6+ rival bids on the same items/date).
The ML benchmark is **supporting evidence only** — it never drives a risk flag. See the *Methodology* page.
""")
st.caption("Use the pages in the left sidebar: Case Explorer · Risk Analysis · Multi-Benchmark · Methodology.")
