"""
XBeach indicator viewer: PMTiles map only (S3).

MVP slice of xbeach_app_integration/PLAN.md's step 5: prove the uploaded
XBeach indicator PMTiles (domains 01/02, storm 2020.03.15, novegetation)
render correctly, using the same MapLibre/PMTiles machinery as the SCHISM
dashboard. Deliberately does NOT include polygon-based area assessment
(stats/threshold-map/histogram panels) -- that needs the quad spatial index
(PLAN.md step 5.3) and the polygon-over-quads reduction (step 5.4), neither
built yet. Add those panels once that data exists, following
`app_pmtiles_assessment_s3.py`'s pattern.

Run: streamlit run app_xbeach_pmtiles_s3.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import folium
import streamlit as st
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

from pmtiles_s3_common import (
    CMAP_OPTIONS,
    SchismPMTilesLayer,
    add_map_legend,
    build_maplibre_style,
    default_cmap_index,
    load_pmtiles_info_from_s3,
    parse_s3_uri,
    public_s3_url,
    s3_object_size,
)
from xbeach_pmtiles_common import (
    XBEACH_DEFAULT_SCENARIO,
    XBEACH_DOMAIN_LABELS,
    XBEACH_INDICATOR_LAYERS,
    XBEACH_PUBLISHED_RUNS,
    XBEACH_SCENARIO_LABELS,
    XBEACH_STORMS,
    XBEACH_TAU_UNSTABLE_DOMAINS,
    xbeach_indicator_s3_uri,
)

REGION = "BULGARIA"

PANEL_BLUE = "#1e3a8a"
FOCCUS_LOGO = Path(__file__).resolve().parent / "FOCCUS_Logo_clean RGB_whiteBG.png"
if not FOCCUS_LOGO.is_file():
    FOCCUS_LOGO = Path(__file__).resolve().parent / "FOCCUS_Logo_clean RGB.png"


def _storm_label(storm: str) -> str:
    return storm.removeprefix("time_interval_")


@st.cache_data(show_spinner="Checking published runs…", ttl=3600)
def _pmtiles_exists(bucket: str, key: str) -> bool:
    # No fixed size floor here: unlike SCHISM's single continuous mesh,
    # XBeach's small per-beach domains can legitimately produce a tiny
    # (few-KB) PMTiles file when an indicator is genuinely all-zero (e.g.
    # domain 2's `dz` -- a BLOWUP run killed before real bed change
    # accumulated, per xbeach_app_integration/README.md). A 0-byte object
    # is the only reliable "actually missing/broken" signal.
    try:
        return s3_object_size(bucket, key) > 0
    except Exception:
        return False


def run_xbeach_dashboard(*, configure_page: bool = True) -> None:
    if configure_page:
        st.set_page_config(
            page_title="XBeach indicators (S3)",
            layout="wide",
            initial_sidebar_state="collapsed",
        )

    hdr_logo, hdr_text = st.columns([1.1, 6.9], vertical_alignment="center")
    with hdr_logo:
        if FOCCUS_LOGO.is_file():
            st.image(str(FOCCUS_LOGO), width=120)
    with hdr_text:
        st.markdown("**FOCCUS Demonstrator — XBeach storm-response indicators (Bulgaria)**")
        st.caption(
            "Per-beach XBeach runs, one storm and domain at a time — a different axis "
            "from the SCHISM dashboard's single continuous mesh."
        )

    with st.container(border=True):
        c_domain, c_storm, c_scenario, c_ind = st.columns([2, 2, 2, 2], vertical_alignment="bottom")
        with c_domain:
            domain_id = st.selectbox(
                "Domain",
                options=sorted(XBEACH_DOMAIN_LABELS),
                format_func=lambda d: XBEACH_DOMAIN_LABELS[d],
                index=0,
            )
        with c_storm:
            storm = st.selectbox(
                "Storm",
                options=XBEACH_STORMS,
                format_func=_storm_label,
                index=0,
            )
        with c_scenario:
            scenario_choice = st.selectbox(
                "Scenario",
                options=list(XBEACH_SCENARIO_LABELS.values()),
                index=list(XBEACH_SCENARIO_LABELS.keys()).index(XBEACH_DEFAULT_SCENARIO),
            )
            scenario = next(k for k, v in XBEACH_SCENARIO_LABELS.items() if v == scenario_choice)
        indicator_names = [
            name
            for name in XBEACH_INDICATOR_LAYERS
            if not (name == "Bed stress q95" and domain_id in XBEACH_TAU_UNSTABLE_DOMAINS)
        ]
        with c_ind:
            indicator_label = st.selectbox("Indicator", options=indicator_names, index=0)
        layer_cfg = XBEACH_INDICATOR_LAYERS[indicator_label]

    if (domain_id, storm) not in XBEACH_PUBLISHED_RUNS:
        st.warning(
            f"{XBEACH_DOMAIN_LABELS[domain_id]}, storm {_storm_label(storm)} isn't published to "
            "S3 yet — only domains 1 and 2 (storm 2020.03.15) are live so far. "
            "See xbeach_app_integration/PLAN.md steps 1-4 for the rest of the batch."
        )
        st.stop()

    pmtiles_uri = xbeach_indicator_s3_uri(REGION, domain_id, storm, scenario, layer_cfg["file"])

    try:
        p_bucket, p_key = parse_s3_uri(pmtiles_uri)
        if not _pmtiles_exists(p_bucket, p_key):
            st.warning(f"PMTiles file looks empty or missing ({pmtiles_uri}).")
            st.stop()
        info = load_pmtiles_info_from_s3(
            p_bucket,
            p_key,
            value_attribute=layer_cfg["attribute"],
        )
        pmtiles_url = public_s3_url(p_bucket, p_key)
    except Exception as exc:
        st.error(f"Failed to load data from S3: {exc}")
        st.stop()

    south, west, north, east = info["bounds"]
    center_lat = (south + north) / 2.0
    center_lon = (west + east) / 2.0
    value_attr = info["value_attribute"]
    unit = layer_cfg.get("unit", "")
    var_label = f"{indicator_label} ({unit})" if unit else indicator_label

    data_vmin = float(info["value_min"])
    data_vmax = float(info["value_max"])
    if data_vmin >= data_vmax:
        data_vmax = data_vmin + 1.0

    default_cmap = layer_cfg["cmap"]
    data_max_zoom = int(info["max_zoom"])
    data_min_zoom = int(info["min_zoom"])

    style_col, map_col = st.columns([1, 4], gap="medium")
    with style_col:
        with st.popover("Style", use_container_width=True):
            f_cmap = st.selectbox(
                "Colormap",
                options=list(CMAP_OPTIONS),
                index=default_cmap_index(default_cmap),
                key=f"xbeach_cmap_{indicator_label}",
            )
            f_basemap = st.selectbox(
                "Basemap",
                options=["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter"],
                index=1,
                key="xbeach_basemap_choice",
            )
            f_opacity = st.slider(
                "Mesh overlay opacity", 0.1, 1.0, 0.85, 0.05, key="xbeach_mesh_opacity"
            )
            f_vmin, f_vmax = st.slider(
                "Color scale range",
                min_value=float(min(data_vmin, 0.0)) if layer_cfg.get("cmap") == "RdYlBu_r" else float(data_vmin),
                max_value=float(data_vmax),
                value=(float(data_vmin), float(data_vmax)),
                step=max((data_vmax - data_vmin) / 200.0, 1e-4),
                key=f"xbeach_range_{indicator_label}",
            )
        st.metric("Value min", f"{data_vmin:.4g} {unit}")
        st.metric("Value max", f"{data_vmax:.4g} {unit}")

    with map_col:
        with st.container(height=560, border=True):
            fm = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=data_min_zoom,
                max_zoom=data_max_zoom + 1,
                tiles=f_basemap,
                control_scale=True,
            )
            Fullscreen().add_to(fm)
            fstyle = build_maplibre_style(
                pmtiles_url=pmtiles_url,
                source_layer=info["layer_id"],
                value_attribute=value_attr,
                vmin=float(f_vmin),
                vmax=float(f_vmax),
                opacity=float(f_opacity),
                cmap_name=f_cmap,
                tile_max_zoom=data_max_zoom,
            )
            SchismPMTilesLayer(fstyle, layer_name=indicator_label).add_to(fm)
            add_map_legend(
                fm,
                caption=var_label,
                cmap_name=f_cmap,
                vmin=float(f_vmin),
                vmax=float(f_vmax),
            )
            folium.FitBounds([[south, west], [north, east]]).add_to(fm)
            st_folium(fm, use_container_width=True, height=540, key="xbeach_indicator_map")


if __name__ == "__main__":
    run_xbeach_dashboard()
