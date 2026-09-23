"""
XBeach indicator viewer: PMTiles map only (S3).

MVP slice of xbeach_app_integration/PLAN.md's step 5, using the same
MapLibre/PMTiles machinery as the SCHISM dashboard. Deliberately does NOT
include polygon-based area assessment (stats/threshold-map/histogram
panels) -- that needs the quad spatial index (PLAN.md step 5.3) and the
polygon-over-quads reduction (step 5.4), neither built yet. Add those
panels once that data exists, following `app_pmtiles_assessment_s3.py`'s
pattern.

Updated 2026-09-22: switched from one storm's indicators at a time (with
a Storm selector, gated to 2 manually-uploaded (domain, storm) pairs) to
the cross-storm `all_storms` overall index -- every domain is a single
median/p95-across-storms summary now, so there's no storm to pick and no
publish allowlist; all 12 domains are listed (see
`xbeach_pmtiles_common.py`'s XBEACH_DOMAIN_LABELS docstring).

Updated 2026-09-23: added a Region selector (Bulgaria / Romania). Same S3
layout per region (`XBEACH/<REGION>/2020-2021/indicator_{nc,pmtiles}/`),
per-region domain labels from XBEACH_REGION_DOMAIN_LABELS, and an optional
per-region note (XBEACH_REGION_NOTES) -- Romania is a preliminary
single-storm test for now.

Updated 2026-09-23 (later): user-facing cleanup, now the "XBeach" page
under the "GCOAST-BS" sidebar section. No development notes, S3 paths or
internal task references are shown to the user: the Indicator selector
lists only indicators whose PMTiles exist for the chosen domain, a
domain with none gets a neutral "no data" message, and load failures
show a generic message (details go to the server log only). The
per-region note was removed.

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
    XBEACH_DEFAULT_REGION,
    XBEACH_DEFAULT_SCENARIO,
    XBEACH_DEFAULT_STAT,
    XBEACH_INDICATOR_LABELS,
    XBEACH_INDICATOR_LAYERS,
    XBEACH_REGION_DOMAIN_LABELS,
    XBEACH_REGION_LABELS,
    XBEACH_SCENARIO_LABELS,
    XBEACH_STAT_LABELS,
    xbeach_indicator_s3_uri,
)

# EDITO's OpenStreetMap tiles work with no key; the other folium basemap
# options (CartoDB positron/dark_matter) started requiring an API key and
# were dropped from the picker rather than left in as a dead-end choice.
BASEMAP = "OpenStreetMap"

PANEL_BLUE = "#1e3a8a"
FOCCUS_LOGO = Path(__file__).resolve().parent / "FOCCUS_Logo_clean RGB_whiteBG.png"
if not FOCCUS_LOGO.is_file():
    FOCCUS_LOGO = Path(__file__).resolve().parent / "FOCCUS_Logo_clean RGB.png"


@st.cache_data(show_spinner="Loading…", ttl=3600)
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
            page_title="GCOAST-BS — XBeach",
            layout="wide",
            initial_sidebar_state="collapsed",
        )

    hdr_logo, hdr_text = st.columns([1.1, 6.9], vertical_alignment="center")
    with hdr_logo:
        if FOCCUS_LOGO.is_file():
            st.image(str(FOCCUS_LOGO), width=120)
    header_slot = hdr_text.empty()

    with st.container(border=True):
        c_region, c_domain, c_scenario, c_ind, c_stat = st.columns(
            [2, 2, 2, 3, 2], vertical_alignment="bottom"
        )
        with c_region:
            region = st.selectbox(
                "Region",
                options=list(XBEACH_REGION_LABELS),
                format_func=lambda r: XBEACH_REGION_LABELS[r],
                index=list(XBEACH_REGION_LABELS).index(XBEACH_DEFAULT_REGION),
                key="xbeach_region",
            )
        domain_labels = XBEACH_REGION_DOMAIN_LABELS[region]
        with c_domain:
            domain_id = st.selectbox(
                "Domain",
                options=sorted(domain_labels),
                format_func=lambda d: domain_labels[d],
                index=0,
                key=f"xbeach_domain_{region}",
            )
        with c_scenario:
            scenario_choice = st.selectbox(
                "Scenario",
                options=list(XBEACH_SCENARIO_LABELS.values()),
                index=list(XBEACH_SCENARIO_LABELS.keys()).index(XBEACH_DEFAULT_SCENARIO),
            )
            scenario = next(k for k, v in XBEACH_SCENARIO_LABELS.items() if v == scenario_choice)
        # Offer only indicators that are actually published for this domain,
        # so the user never lands on a missing file.
        available = [
            k for k, cfg in XBEACH_INDICATOR_LAYERS.items()
            if _pmtiles_exists(*parse_s3_uri(xbeach_indicator_s3_uri(region, domain_id, scenario, cfg["file"])))
        ]
        with c_ind:
            indicator_key = st.selectbox(
                "Indicator",
                options=available,
                format_func=lambda k: XBEACH_INDICATOR_LABELS[k],
                index=0,
                disabled=not available,
                placeholder="No indicators available",
            )
        with c_stat:
            stat_key = st.selectbox(
                "Statistic",
                options=list(XBEACH_STAT_LABELS),
                format_func=lambda k: XBEACH_STAT_LABELS[k],
                index=list(XBEACH_STAT_LABELS).index(XBEACH_DEFAULT_STAT),
            )

    with header_slot.container():
        st.markdown(
            f"**FOCCUS Demonstrator — GCOAST-BS XBeach: beach storm-response indicators "
            f"({XBEACH_REGION_LABELS[region]})**"
        )
        st.caption(
            "High-resolution beach-scale indicators per coastal domain: median and 95th "
            "percentile over the simulated storm events."
        )

    if indicator_key is None:
        st.info("No data is available for the selected domain.")
        return
    layer_cfg = XBEACH_INDICATOR_LAYERS[indicator_key]

    pmtiles_uri = xbeach_indicator_s3_uri(region, domain_id, scenario, layer_cfg["file"])
    value_attribute = f"{indicator_key}_{stat_key}"

    try:
        p_bucket, p_key = parse_s3_uri(pmtiles_uri)
        info = load_pmtiles_info_from_s3(
            p_bucket,
            p_key,
            value_attribute=value_attribute,
        )
        pmtiles_url = public_s3_url(p_bucket, p_key)
    except Exception as exc:
        print(f"[xbeach] failed to load {pmtiles_uri}: {exc!r}")  # server log only
        st.info("The map for this selection could not be loaded. Please try again later.")
        return

    south, west, north, east = info["bounds"]
    center_lat = (south + north) / 2.0
    center_lon = (west + east) / 2.0
    value_attr = info["value_attribute"]
    unit = layer_cfg.get("unit", "")
    indicator_label = XBEACH_INDICATOR_LABELS[indicator_key]
    stat_label = XBEACH_STAT_LABELS[stat_key]
    var_label = f"{layer_cfg['caption']} — {stat_label} ({unit})" if unit else f"{layer_cfg['caption']} — {stat_label}"

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
                key=f"xbeach_cmap_{value_attribute}",
            )
            f_opacity = st.slider(
                "Overlay opacity", 0.1, 1.0, 0.85, 0.05, key="xbeach_mesh_opacity"
            )
            f_vmin, f_vmax = st.slider(
                "Color scale range",
                min_value=float(min(data_vmin, 0.0)) if layer_cfg.get("cmap") == "RdYlBu_r" else float(data_vmin),
                max_value=float(data_vmax),
                value=(float(data_vmin), float(data_vmax)),
                step=max((data_vmax - data_vmin) / 200.0, 1e-4),
                key=f"xbeach_range_{value_attribute}",
            )
        st.metric("Value min", f"{data_vmin:.4g} {unit}")
        st.metric("Value max", f"{data_vmax:.4g} {unit}")

    with map_col:
        with st.container(height=560, border=True):
            fm = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=data_min_zoom,
                max_zoom=data_max_zoom + 1,
                tiles=BASEMAP,
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
            st_folium(fm, use_container_width=True, height=540, key=f"xbeach_indicator_map_{region}")


if __name__ == "__main__":
    run_xbeach_dashboard()
