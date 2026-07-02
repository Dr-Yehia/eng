# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from core.data_loader import load_items, load_case_summary, load_methodology_md, PRIMARY_NOTE, DISCLAIMER

st.set_page_config(page_title="Methodology", page_icon="📚", layout="wide")
import ui_common; ui_common.apply_ui()
st.header("📚 Methodology")
st.warning(DISCLAIMER)
items = load_items(); cs = load_case_summary()

hist_cov = (items.historical_match_status == "matched").mean() * 100 if "historical_match_status" in items else float("nan")
ml_strong = (items.ml_match_status == "strong").mean() * 100 if "ml_match_status" in items else 0.0

st.markdown(f"""
### Framework
A **composition-aware ML unit-price benchmark** (DDC surrogate, validated with GroupKFold, MdAPE ≈ 14% out-of-fold),
**time-adjusted** with official price indices and **regionally calibrated**, then applied to **real FDOT bid tabulations**
to flag **abnormal pricing risk**. Predictions are *benchmark* unit prices, not guaranteed market prices.

### Benchmarks used for the risk layer
| Benchmark | Role | Coverage | Notes |
|---|---|---|---|
| **A — Contractor market** (non-winner bidder median) | **Primary** | 100% | competitors on the same items/date; strongest internal benchmark |
| **H — FDOT historical 2024** (statewide weighted avg) | **Primary** | ~{hist_cov:.0f}% | external, official, look-ahead-safe (prior to 2025 lettings) |
| **B — ML DDC** | **Supporting only** | ~{ml_strong:.0f}% strong | FDOT roadway ≠ Eurasian DDC catalog → near-zero strong matches; **never drives a flag** |

{PRIMARY_NOTE}

### Deviation, exposure & thresholds
- `deviation = (winner − benchmark) / benchmark`; `overpricing_exposure = max(winner − benchmark, 0) × quantity`.
- Risk flags use **fixed %** *and* **robust z-score** *and* **data-driven P75/P90/P95** of |deviation| — not a single arbitrary cutoff.
- **Lump-sum** items are flagged separately (`risk_basis = lump_sum`, quantity = 1), not treated as unit-rate risk.

### Evidence classes (combined logic)
`confirmed_by_both` (market **and** historical elevated → high confidence) ·
`historical_only` · `market_only` · `low_evidence` · `no_benchmark`.
Confidence is reduced when a case has **< 3 bidders** (weak market benchmark).

### Cases
Main validation: **T5850, T6603, T1900, T4711 (bridge), E7U28 (maintenance)**.
Sensitivity (2 bidders, not weighted equally): **E7Q32**.
Parser v2 extracts all six official bid tabs with grand totals matching exactly (100% parser success; see *Data Lineage*).

### Limitations (stated honestly)
- Risk = pricing **deviation** vs benchmarks — not proof of irregularity. No ground truth → no false-alarm rate claimed.
- Six FDOT lettings across roadway, signals, bridge and maintenance work; other DOTs/agencies still need more cases for broader generalization.
- ML is supporting only for FDOT roadway items; the **bidder-market + FDOT-historical** benchmarks carry the analysis.
- Wording is **abnormal pricing risk / commercial review** — never *fraud*.
""")

st.divider()
st.subheader("Upstream methodology decision note")
st.markdown(load_methodology_md())

vp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metadata", "APP_VERSION.json")
if os.path.exists(vp):
    st.divider(); st.subheader("Version")
    st.json(json.load(open(vp)))
