"""XBeach counterpart of `pmtiles_s3_common.py`'s S3 key/config helpers.

Generic PMTiles reading/rendering (parse_s3_uri, load_pmtiles_info_from_s3,
build_maplibre_style, SchismPMTilesLayer, add_map_legend, ...) is reused
as-is from `pmtiles_s3_common` -- none of that is SCHISM-specific. This
module only holds the pieces that differ: the S3 key layout (XBeach has two
more axes than SCHISM's one continuous run -- domain and storm, see
`xbeach_app_integration/PLAN.md`), the indicator set, and domain labels.

Copied from `xbeach_app_integration/xbeach_pmtiles_common_draft.py` in the
NWBS-XB-2020 repo (2026-09-18), with `XBEACH_DOMAIN_LABELS` filled in from
`visualization/storm_viewer.ipynb`'s `DOMAIN_NAMES` (left as a placeholder
in the draft to avoid hand-retyping it out of sync with the notebook).
"""
from __future__ import annotations

from typing import Any

# Same bucket as the SCHISM run, sibling prefix -- see PLAN.md's "Proposed
# S3 layout" for the open decision on whether that's actually right for
# your S3/EDITO setup long-term.
XBEACH_S3_BUCKET = "project-foccus"
XBEACH_S3_BASE_PREFIX = "Hereon/ESC1-123-BS/XBEACH"

# Region goes BEFORE the date-range period (not after), on purpose: this
# repo only has Bulgaria today, but a future Romania coast dataset almost
# certainly won't share "2020-2021" as its storm-batch period, so the
# period has to live under the region, not be a sibling of it.
XBEACH_REGION_PERIODS: dict[str, str] = {
    "BULGARIA": "2020-2021",
}

# Zero-padded to this many digits in the S3 key (e.g. domain 1 -> "01"),
# per the manual EDITO layout worked out 2026-09-18. Bulgaria's 12 domains
# fit in 2 digits; bump this (or make it per-region) if a future region
# has 100+ domains.
XBEACH_DOMAIN_ID_WIDTH = 2


def xbeach_s3_prefix(region: str) -> str:
    period = XBEACH_REGION_PERIODS[region]
    return f"{XBEACH_S3_BASE_PREFIX}/{region}/{period}"


# Only "novegetation" (scenario 0 in this repo's run_status.csv) has been
# run so far. Add "vegetation" here once scenario 1 runs exist.
XBEACH_SCENARIO_FOLDERS: dict[str, dict[str, str]] = {
    "novegetation": {"pmtiles": "indicator_pmtiles", "nc": "indicator_nc"},
}
XBEACH_SCENARIO_LABELS: dict[str, str] = {
    "novegetation": "No vegetation",
}
XBEACH_DEFAULT_SCENARIO = "novegetation"

# From storm_viewer.ipynb's DOMAIN_NAMES.
XBEACH_DOMAIN_LABELS: dict[int, str] = {
    1: "1 — Dyavolska-Primorsko",
    2: "2 — Atliman",
    3: "3 — Arkutino-Alepu",
    4: "4 — Ropotamo",
    5: "5 — Kavatsite",
    6: "6 — Harmani-Sozopol",
    7: "7 — Campsite Gradina",
    8: "8 — North Burgas",
    9: "9 — South Burgas",
    10: "10 — Pomorie",
    11: "11 — Sunny Beach",
    12: "12 — Nessebar",
}

# Every storm in this project's batch (run_status.csv). Kept as the FULL
# "time_interval_<date>" string on purpose, matching run_status.csv's own
# `storm` column and the local repo's folder name exactly.
XBEACH_STORMS: list[str] = [
    "time_interval_2020.03.15", "time_interval_2020.03.23", "time_interval_2020.04.05",
    "time_interval_2020.07.18", "time_interval_2020.08.05", "time_interval_2020.09.12",
    "time_interval_2020.09.15", "time_interval_2020.12.07", "time_interval_2020.12.14",
    "time_interval_2021.01.11", "time_interval_2021.02.14", "time_interval_2021.02.15",
]

# As of 2026-09-18, only these (domain, storm) pairs have indicator PMTiles
# actually uploaded to S3 (see xbeach_app_integration/PLAN.md steps 1-4 for
# the rest of the batch). Selecting anything else shows a clear "not
# published yet" message instead of a raw S3 error.
XBEACH_PUBLISHED_RUNS: set[tuple[int, str]] = {
    (1, "time_interval_2020.03.15"),
    (2, "time_interval_2020.03.15"),
}

# indicator key -> layer config, same shape as SCHISM's INDICATOR_LAYERS.
XBEACH_INDICATOR_LAYERS: dict[str, dict[str, Any]] = {
    "Hrms wave height q95": {
        "file": "q95_Hrms_quads.pmtiles",
        "nc_file": "q95_Hrms.nc",
        "nc_variable": "q95_Hrms",
        "attribute": "q95_Hrms",
        "caption": "Hrms q95 (m)",
        "unit": "m",
        "cmap": "plasma",
        "critical_default": 1.5,
    },
    "Bed stress q95": {
        "file": "q95_tau_quads.pmtiles",
        "nc_file": "q95_tau.nc",
        "nc_variable": "q95_tau",
        "attribute": "q95_tau",
        "caption": "Bed stress q95 (N/m²)",
        "unit": "Pa",
        "cmap": "plasma",
        "critical_default": 0.5,
        # NOT enabled for domains 6/9/11 until the near-drying-cell
        # instability in xbeach_app_integration/README.md is resolved -- a
        # single bad cell reading 600+ Pa would swamp the color scale for
        # the whole domain. Filtered in the UI layer below, not here.
    },
    "Bed-level change (dz)": {
        "file": "dz_quads.pmtiles",
        "nc_file": "dz.nc",
        "nc_variable": "dz",
        "attribute": "dz",
        "caption": "Cumulative bed change (m)",
        "unit": "m",
        "cmap": "RdYlBu_r",  # diverging: erosion vs. accretion
        "critical_default": -0.5,
    },
}

# Domains where q95_tau is known to have the near-drying-cell instability
# (README.md's "Known issue" section) -- hidden from the indicator picker
# for those domains until xbeach_app_integration/PLAN.md step 1a is resolved.
XBEACH_TAU_UNSTABLE_DOMAINS: set[int] = {6, 9, 11}


def xbeach_scenario_folder(scenario: str, kind: str) -> str:
    return XBEACH_SCENARIO_FOLDERS[scenario][kind]


def xbeach_indicator_s3_uri(region: str, domain_id: int, storm: str, scenario: str, filename: str) -> str:
    """s3://<bucket>/<base_prefix>/<REGION>/<period>/<domain_id (zero-padded)>/<storm>/<scenario>/<kind_folder>/<filename>"""
    kind = "pmtiles" if filename.endswith(".pmtiles") else "nc"
    folder = xbeach_scenario_folder(scenario, kind)
    domain_key = f"{domain_id:0{XBEACH_DOMAIN_ID_WIDTH}d}"
    prefix = xbeach_s3_prefix(region)
    return f"s3://{XBEACH_S3_BUCKET}/{prefix}/{domain_key}/{storm}/{scenario}/{folder}/{filename}"


def xbeach_quad_index_s3_uri(region: str, domain_id: int, storm: str, scenario: str) -> str:
    """S3 URI for the per-(domain, storm) quad spatial index -- NOT built yet
    (xbeach_app_integration/PLAN.md step 5.3), used only once polygon-based
    area assessment is wired up for XBeach."""
    folder = xbeach_scenario_folder(scenario, "nc")
    domain_key = f"{domain_id:0{XBEACH_DOMAIN_ID_WIDTH}d}"
    prefix = xbeach_s3_prefix(region)
    return f"s3://{XBEACH_S3_BUCKET}/{prefix}/{domain_key}/{storm}/{scenario}/{folder}/quad_spatial_index.npz"
