# -*- coding: utf-8 -*-
"""Small shared UI helpers for the Streamlit layer (presentation only, no analytics logic)."""
import streamlit as st

_HOME_LABEL = "Home"


def apply_ui():
    """Relabel Streamlit's auto-generated 'app' home entry in the sidebar nav to 'Home'.
    Purely cosmetic; degrades to a no-op if Streamlit changes its sidebar DOM."""
    st.markdown(
        f"""<style>
        [data-testid="stSidebarNav"] span[label="app"] {{
            visibility: hidden; position: relative; overflow: visible; }}
        [data-testid="stSidebarNav"] span[label="app"]::after {{
            content: "{_HOME_LABEL}"; visibility: visible;
            position: absolute; left: 0; top: 0; white-space: nowrap; }}
        </style>""",
        unsafe_allow_html=True,
    )
