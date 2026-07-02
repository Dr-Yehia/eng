# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, streamlit as st, plotly.express as px
from core.data_loader import load_items

st.set_page_config(page_title="ML Support & Limitations", page_icon="🧠", layout="wide")
st.header("🧠 ML Support & Limitations")
items = load_items()

st.warning("**For FDOT roadway cases, the ML benchmark is SUPPORTING EVIDENCE ONLY.** "
           "Primary risk decisions use the contractor-market benchmark AND the official FDOT historical 2024 benchmark. "
           "ML never drives a risk flag here.")

vc = items.ml_match_status.value_counts()
c = st.columns(3)
c[0].metric("ML strong matches (≥0.85)", int(vc.get("strong", 0)))
c[1].metric("ML candidate matches (0.50–0.85)", int(vc.get("candidate_review", 0)))
c[2].metric("ML no-match", int(vc.get("no_match", 0)))

st.subheader("ML match status by case")
g = items.groupby(["case_id", "ml_match_status"]).size().reset_index(name="items")
fig = px.bar(g, x="case_id", y="items", color="ml_match_status", barmode="stack")
fig.update_layout(height=380); st.plotly_chart(fig, use_container_width=True)

if "ml_match_score" in items and items.ml_match_score.notna().any():
    st.subheader("ML match-score distribution")
    fig2 = px.histogram(items[items.ml_match_score.notna()], x="ml_match_score", nbins=30)
    fig2.add_vline(x=0.85, line_dash="dash", line_color="red", annotation_text="strong ≥ 0.85")
    fig2.update_layout(height=340); st.plotly_chart(fig2, use_container_width=True)

st.subheader("Limitations (stated honestly)")
st.markdown("""
- Risk = **pricing deviation** vs benchmarks — **not** proof of irregularity. No ground truth, so no false-alarm rate is claimed.
- FDOT highway pay items match the Eurasian-derived **DDC catalog** weakly → **near-zero strong ML matches**; ML is supporting only.
- The **FDOT historical 2024** benchmark is look-ahead-safe (prior to the 2025 lettings); 6-/12-month files are future-dated and used only as retrospective sensitivity.
- Validated on a small set of FDOT highway lettings; bridge/maintenance layouts and other DOTs need parser extension and more cases.
- **E7Q32** (2 bidders) is a *sensitivity* case, not weighted equally with the main validation cases.
- Wording throughout is **abnormal pricing risk / commercial review** — never *fraud*.
""")
