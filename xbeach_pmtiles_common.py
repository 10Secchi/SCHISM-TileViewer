"""XBeach counterpart of `pmtiles_s3_common.py`'s S3 key/config helpers.

Generic PMTiles reading/rendering (parse_s3_uri, load_pmtiles_info_from_s3,
build_maplibre_style, SchismPMTilesLayer, add_map_legend, ...) is reused
as-is from `pmtiles_s3_common` -- none of that is SCHISM-specific. This
module only holds the pieces that differ: the S3 key layout, the
indicator set, and domain labels.

Updated 2026-09-22: replaced the original per-storm q95_Hrms/q95_tau/dz
export (one storm at a time, gated to the 2 (domain, storm) pairs that
had been manually uploaded) with the cross-storm `all_storms` indicator
set -- see `xbeach_app_integration/README.md`'s
"xbeach_cross_storm_indicators.py" section. Each of the 12 domains now
has ONE overall index built from all its valid storms (a median and a
95th-percentile map per indicator), so there is no storm axis anymore,
and the S3 key layout drops the old `<storm>/<scenario>` nesting to match
the local `xbeach_app_integration/<region>/all_storms/<domain>_veg
<scenario>/` folder shape exactly (domain ids are NOT zero-padded here,
matching those folder names, unlike the old per-storm layout).
"""
from __future__ import annotations

from typing import Any

# Same bucket as the SCHISM run, sibling prefix -- see PLAN.md's "Proposed
# S3 layout" for the open decision on whether that's actually right for
# your S3/EDITO setup long-term.
XBEACH_S3_BUCKET = "project-foccus"
XBEACH_S3_BASE_PREFIX = "Hereon/ESC1-123-BS/XBEACH"

# Region folder name on S3 -- kept uppercase on EDITO by the user's choice
# (2026-09-22), unlike the local `xbeach_app_integration/<region>/`
# directory name which is lowercase. No separate date-range period
# segment anymore: the cross-storm index isn't tied to one storm-batch
# period the way the old per-storm export was.
XBEACH_REGION_FOLDERS: dict[str, str] = {
    "BULGARIA": "BULGARIA",
}


def xbeach_s3_prefix(region: str) -> str:
    return f"{XBEACH_S3_BASE_PREFIX}/{XBEACH_REGION_FOLDERS[region]}"


# Only "veg0" (no vegetation, scenario 0 in run_status.csv) has been run
# so far. Add a "veg1" entry here once a vegetation-scenario batch exists.
XBEACH_SCENARIO_LABELS: dict[str, str] = {
    "veg0": "No vegetation",
}
XBEACH_DEFAULT_SCENARIO = "veg0"

# From storm_viewer.ipynb's DOMAIN_NAMES. All 12 are valid: every domain
# had >=10/12 valid storms feeding its cross-storm index (see
# `bulgaria/all_storms/domain_summary.csv`) and none was dropped.
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

# indicator key -> layer config. Matches xbeach_cross_storm_indicators.py's
# INDICATOR_KEYS/INDICATOR_SPECS. Each file holds BOTH statistics as two
# properties/variables (`<key>_median`, `<key>_p95`) rather than one file
# per statistic -- the UI's "Statistic" selector below picks the attribute
# within the already-loaded file, not a different S3 object.
XBEACH_INDICATOR_LAYERS: dict[str, dict[str, Any]] = {
    "roller_energy": {
        "file": "roller_energy_quads.pmtiles",
        "nc_file": "roller_energy.nc",
        "caption": "Roller energy dissipation",
        "unit": "Nm/m²",
        "cmap": "plasma",
    },
    "tau": {
        "file": "tau_quads.pmtiles",
        "nc_file": "tau.nc",
        "caption": "Bed shear stress",
        "unit": "N/m²",
        "cmap": "plasma",
    },
    "erosion": {
        "file": "erosion_quads.pmtiles",
        "nc_file": "erosion.nc",
        "caption": "Cumulative bed change",
        "unit": "m",
        "cmap": "RdYlBu_r",  # diverging: erosion vs. accretion
    },
    "flooded_depth": {
        "file": "flooded_depth_quads.pmtiles",
        "nc_file": "flooded_depth.nc",
        "caption": "Peak water-level rise",
        "unit": "m",
        "cmap": "viridis",
    },
    "flood_duration": {
        "file": "flood_duration_quads.pmtiles",
        "nc_file": "flood_duration.nc",
        "caption": "Flood duration",
        "unit": "h",
        "cmap": "YlOrRd",
    },
}
XBEACH_INDICATOR_LABELS: dict[str, str] = {
    "roller_energy": "Roller energy (q95 across storms)",
    "tau": "Bed shear stress (q95 across storms)",
    "erosion": "Bed-level change (erosion/accretion)",
    "flooded_depth": "Flooded depth (max rise)",
    "flood_duration": "Flood duration",
}

# The two statistics every indicator file carries, both computed across
# a domain's valid storms (xbeach_cross_storm_indicators.py) -- not two
# different files, two properties on the same one.
XBEACH_STAT_LABELS: dict[str, str] = {
    "median": "Median across storms",
    "p95": "95th percentile across storms",
}
XBEACH_DEFAULT_STAT = "median"


def xbeach_domain_folder(domain_id: int, scenario: str) -> str:
    return f"{domain_id}_{scenario}"


def xbeach_indicator_s3_uri(region: str, domain_id: int, scenario: str, filename: str) -> str:
    """s3://<bucket>/<base_prefix>/<region folder>/<domain_id>_<scenario>/<indicator_nc|indicator_pmtiles>/<filename>

    e.g. `.../XBEACH/BULGARIA/1_veg0/indicator_pmtiles/erosion_quads.pmtiles`.
    """
    folder = "indicator_pmtiles" if filename.endswith(".pmtiles") else "indicator_nc"
    prefix = xbeach_s3_prefix(region)
    domain_folder = xbeach_domain_folder(domain_id, scenario)
    return f"s3://{XBEACH_S3_BUCKET}/{prefix}/{domain_folder}/{folder}/{filename}"
