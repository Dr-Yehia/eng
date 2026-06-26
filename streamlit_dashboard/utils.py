# -*- coding: utf-8 -*-
"""Shared helpers for the FDOT Abnormal Pricing Risk dashboard."""
import os, json
import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FIG = os.path.join(HERE, "figures")
RISK_ORDER = ["Normal", "Watch", "Moderate", "High", "Critical"]
RISK_COLORS = {"Normal": "#41ab5d", "Watch": "#d9c40b", "Moderate": "#fec44f",
               "High": "#fe9929", "Critical": "#cc4c02"}
DISCLAIMER = ("This is an **abnormal pricing risk** analysis — it flags unit-rate deviations that warrant "
              "commercial review. It does **not** allege fraud or intent.")


@st.cache_data
def load_items():
    df = pd.read_parquet(os.path.join(DATA, "all_cases_dashboard_ready.parquet"))
    if "risk_flag" in df:
        df["risk_flag"] = pd.Categorical(df["risk_flag"], categories=RISK_ORDER, ordered=True)
    return df


@st.cache_data
def load_cases():
    df = pd.read_parquet(os.path.join(DATA, "all_cases_case_summary.parquet"))
    return df[df.get("extraction_all_pass") == True].copy() if "extraction_all_pass" in df else df


@st.cache_data
def load_bidders():
    return pd.read_parquet(os.path.join(DATA, "all_cases_bidder_summary.parquet"))


@st.cache_data
def load_project_summary():
    with open(os.path.join(DATA, "project_summary.json"), encoding="utf-8") as f:
        return json.load(f)


def fig_path(name):
    p = os.path.join(FIG, name)
    return p if os.path.exists(p) else None


def page_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def risk_badge(flag):
    c = RISK_COLORS.get(flag, "#888")
    return f'<span style="background:{c};color:#111;padding:2px 8px;border-radius:6px;font-weight:600">{flag}</span>'


def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, help_) in zip(cols, items):
        col.metric(label, value, help=help_)


def style_risk(df):
    def color(v):
        return f"background-color:{RISK_COLORS.get(v,'')};color:#111" if v in RISK_COLORS else ""
    if "risk_flag" in df:
        return df.style.applymap(color, subset=["risk_flag"])
    return df.style
