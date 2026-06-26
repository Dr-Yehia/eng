# -*- coding: utf-8 -*-
"""Methodology & documentation page."""
import os
import streamlit as st
from utils import DISCLAIMER, fig_path, page_header

st.set_page_config(page_title="Methodology", page_icon="📚", layout="wide")
page_header("📚 Methodology & Documentation")
st.warning(DISCLAIMER)

st.markdown(r"""
### 1. What this system is
A **composition-aware surrogate benchmark** for construction work-item unit prices, built on a resource-based
normative cost standard (DDC/CWICR), then **time-adjusted** with official price indices and applied to **real
public bid tabulations** (FDOT) to detect abnormal pricing risk. It predicts a *benchmark* unit price, not a
guaranteed market price.

### 2. Pipeline
1. **Clean dataset** — 900k resource-level rows → 55,610 work items (one row per item). No price-derived leakage columns.
2. **ML benchmark** — XGBoost / CatBoost, validated with **GroupKFold by item name** (unseen names in test). Headline metric MdAPE ≈ 14% (out-of-fold). R²(log) is high but inflated by the wide price range, so **MdAPE / within-±20%** are the reported metrics.
3. **Dynamic escalation** — `time_adjusted = predicted × exp(Σ wₖ·ln(Fₖ))` over **real BLS** indices (labor, material, equipment, energy, general construction). Weights from non-cost proxy intensities.
4. **Regional calibration** — US → Dubai (AED) transfer factor (≈0.62) as a separate, documented step.
5. **Case-study risk** — extract every bidder's unit price + quantity from the official PDF; compute deviations, exposure and risk flags.
6. **Multi-case validation** — repeat across projects to test stability.

### 3. Benchmarks (ranked by strength here)
| Benchmark | Role | Why |
|---|---|---|
| **Non-winner bidder median** | **Primary** | 6+ real competitors on the *same* items, date and project — the strongest, FDOT-style benchmark |
| All-bidder median / dispersion (IQR, MAD, robust-z) | Secondary | unbalanced-bid detection |
| FDOT historical 6m/12m | Reserved | the provided “2025 BID DATA PROGRAM.xlsx” is a per-item *calculator*, not a bulk-joinable table |
| ML DDC time-adjusted | **Supporting only** | FDOT highway pay items vs a Eurasian-derived catalog match weakly (≈0 strong matches); **never drives a risk flag** |

### 4. Risk thresholds (on the primary deviation)
| Level | Condition |
|---|---|
| Normal | ≤ 10% |
| Watch | 10–20% |
| Moderate | 20–35% |
| High | 35–60% |
| Critical | > 60%, or robust z-score > 3 |

Exposure escalation: overpricing exposure > 1% of the bid raises the level by 1; > 3% raises it by 2.
**Lump-sum items** (mobilization, MOT, markings) are flagged separately and not treated as unit-rate risk.

### 5. Financial exposure
`overpricing_exposure = max(winner_unit − benchmark_unit, 0) × quantity`  (quantity = 1 for lump-sum items).

### 6. Honest limitations
- Risk = pricing **deviation** vs benchmarks — **not proof of irregularity**. Low bidder spread inflates %-deviations on small items.
- Validated on a small set of FDOT highway lettings; bridge/maintenance layouts and other DOTs need parser extension and more cases.
- The ML benchmark is structurally low-coverage for highway pay items; the **bidder-market benchmark carries the analysis**.
- Wording is deliberately *abnormal pricing risk / commercial review* — never *fraud*.
""")

st.divider()
page_header("Reference figures")
for nm, cap in [("fig_02_risk_distribution_by_case.png", "Risk distribution by case"),
                ("fig_03_exposure_by_case.png", "Exposure (% of bid) by case"),
                ("fig_08_benchmark_coverage_by_case.png", "Benchmark coverage status")]:
    p = fig_path(nm)
    if p:
        st.image(p, caption=cap, use_container_width=True)
