"""FOCCUS demonstrator — Streamlit app (About + GCOAST-BS: SCHISM, XBeach).

Run:
  streamlit run app_pmtiles_assessment_two_paged_s3.py

Sidebar:
  About          -- ESC1GB.md documentation with embedded PDF (DF122.pdf).
  GCOAST-BS
    SCHISM       -- regional indicator map and polygon area assessment.
    XBeach       -- beach-scale storm-response indicators per domain.
"""

from __future__ import annotations

import streamlit as st

from foccus_about_page import render_about_page

st.set_page_config(
    page_title="FOCCUS Northwestern Black Sea demonstrator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

about = st.Page(render_about_page, title="About", icon="📖", default=True)
schism_dashboard = st.Page("foccus_dashboard_page.py", title="SCHISM", icon="🗺️")
xbeach_dashboard = st.Page("xbeach_dashboard_page.py", title="XBeach", icon="🏖️")

pg = st.navigation({
    "": [about],
    "GCOAST-BS": [schism_dashboard, xbeach_dashboard],
})
pg.run()
