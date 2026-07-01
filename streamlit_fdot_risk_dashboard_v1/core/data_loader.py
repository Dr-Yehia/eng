# -*- coding: utf-8 -*-
"""Cached data loaders + constants for the FDOT Risk research dashboard (read-only).
All heavy computation happens upstream; this layer only READS validated outputs."""
import os, json
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

RISK_ORDER = ["Normal", "Watch", "Moderate", "High", "Critical", "Not available"]
RISK_COLORS = {"Normal": "#2ca25f", "Watch": "#4292c6", "Moderate": "#ffd92f",
               "High": "#fe9929", "Critical": "#cc4c02", "Not available": "#bdbdbd"}
CONF_COLORS = {"High": "#2ca25f", "Medium": "#ffd92f", "Low": "#9e9ac8"}
DISCLAIMER = ("This dashboard identifies **abnormal pricing risk** and commercial-review flags. "
              "It does **not** claim fraud detection or legal non-compliance.")
PRIMARY_NOTE = ("Risk is driven by TWO independent benchmarks: the contractor **market** (non-winner median) "
                "and the official **FDOT historical 2024** weighted average. The **ML** benchmark is **supporting only** "
                "(~0% strong matches for FDOT roadway items) and never drives a flag.")


def _path(name): return os.path.join(DATA, name)


def _require(name):
    p = _path(name)
    if not os.path.exists(p):
        st.error(f"Missing input file: `data/{name}`.\n\nPlease regenerate the integrated risk package "
                 "(`build_fdot_integrated_risk_v2.py` + patches) and rebuild the dashboard data folder.")
        st.stop()
    return p


@st.cache_data
def load_items():
    """Item-level dual-benchmark risk (integrated v2.1.1). One row per pay item per case."""
    df = pd.read_parquet(_require("integrated_dashboard_ready.parquet"))
    if "combined_risk_flag" in df:
        df["combined_risk_flag"] = pd.Categorical(df["combined_risk_flag"], categories=RISK_ORDER, ordered=True)
    return df


@st.cache_data
def load_case_summary():
    return pd.read_parquet(_require("integrated_case_summary.parquet"))


@st.cache_data
def load_lineage():
    """Multi-case lineage: includes FAILED/excluded cases (T4711, E7U28) for transparency."""
    p = _path("lineage_case_summary.parquet")
    return pd.read_parquet(p) if os.path.exists(p) else pd.DataFrame()


@st.cache_data
def load_bidders():
    p = _path("bidder_summary.parquet")
    return pd.read_parquet(p) if os.path.exists(p) else pd.DataFrame()


@st.cache_data
def load_project_summary():
    p = _path("integrated_project_summary_api_ready.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


@st.cache_data
def load_methodology_md():
    p = _path("methodology_decision_note.md")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else "Methodology note not found."


def file_bytes(name):
    p = _path(name)
    return open(p, "rb").read() if os.path.exists(p) else None


def kpi_cards(items):
    cols = st.columns(len(items))
    for c, (label, value, help_) in zip(cols, items):
        c.metric(label, value, help=help_)


def page_setup(title, icon="📊"):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
