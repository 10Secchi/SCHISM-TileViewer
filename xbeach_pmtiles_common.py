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
95th-percentile map per indicator), so there is no storm axis anymore.
The period folder (`2020-2021`) is KEPT below the region folder (a first
guess that dropped it turned out wrong; confirmed by `head_object`
against several real keys before this was fixed).

Updated again 2026-09-22 (same day, later): the per-domain S3 "folder"
nesting (`<domain>_veg<scenario>/indicator_{nc,pmtiles}/<indicator>.*`)
was replaced with a FLAT layout -- two folders directly under the period
folder, domain+scenario folded into the filename instead:
`indicator_{nc,pmtiles}/<domain_id>_<scenario>_<indicator>[_quads].*`.
Reason: nesting meant uploading 12 separate per-domain folders by hand;
flat means one `indicator_nc/` and one `indicator_pmtiles/` folder can be
uploaded in a single pass. See `xbeach_app_integration/
build_edito_upload_bundle.py`, which builds this exact flat tree locally
from the existing per-domain `all_storms/<domain>_veg<scenario>/
indicator_{nc,pmtiles_v2}/` files (PMTiles source is `indicator_pmtiles_v2/`,
the tile-size-cap fix, not the currently-live `indicator_pmtiles/` -- see
that script's docstring and `README.md`'s tippecanoe tile-size-cap
section). **This changes the S3 keys this module resolves -- the actual
objects on EDITO have not been re-uploaded to the new keys yet as of this
edit, so `load_pmtiles_info_from_s3` will 404 against real S3 until the
`edito_upload/BULGARIA/2020-2021/` bundle is uploaded to replace the old
per-domain-folder objects.**

Updated 2026-09-23: added Romania (`XBEACH/ROMANIA/2020-2021/`, same flat
layout, uploaded and checked by HTTP HEAD: all 60 objects match the local
files byte for byte). Domain labels are now per region
(XBEACH_REGION_DOMAIN_LABELS); XBEACH_DOMAIN_LABELS is still Bulgaria's.
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
# directory name which is lowercase.
XBEACH_REGION_FOLDERS: dict[str, str] = {
    "BULGARIA": "BULGARIA",
    "ROMANIA": "ROMANIA",
}

# Date-range period folder, still present under the region on S3 even
# though the cross-storm index itself isn't really tied to one storm
# batch's period -- kept only because that's where the real upload landed.
XBEACH_REGION_PERIODS: dict[str, str] = {
    "BULGARIA": "2020-2021",
    "ROMANIA": "2020-2021",
}

# UI label per region key, in the order the Region selector lists them.
XBEACH_REGION_LABELS: dict[str, str] = {
    "BULGARIA": "Bulgaria",
    "ROMANIA": "Romania",
}
XBEACH_DEFAULT_REGION = "BULGARIA"


def xbeach_s3_prefix(region: str) -> str:
    return f"{XBEACH_S3_BASE_PREFIX}/{XBEACH_REGION_FOLDERS[region]}/{XBEACH_REGION_PERIODS[region]}"


# Only "veg0" (no vegetation, scenario 0 in run_status.csv) has been run
# so far. Add a "veg1" entry here once a vegetation-scenario batch exists.
XBEACH_SCENARIO_LABELS: dict[str, str] = {
    "veg0": "No vegetation",
}
XBEACH_DEFAULT_SCENARIO = "veg0"

# Bulgaria: from storm_viewer.ipynb's DOMAIN_NAMES. All 12 are valid: every
# domain had >=10/12 valid storms feeding its cross-storm index (see
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

# Romania: names from NWBS-XB-2020-RO/domain_mapping.csv (grid_01..09 =
# chilia1, chilia2, sulina, george, spit, portita, portita2, constanta,
# eforie, north to south). Only the domains actually published on S3 are
# listed: 1 and 9 are not run, 6 has no output yet. FIRST TEST (2026-09-23):
# each domain's index is built from ONE storm (2020.03.23), and the runs
# were still in progress, so median == p95 and the storm is only partly
# covered -- see NWBS-XB-2020-RO/xbeach_app_integration/README.md. Add 6
# (and re-upload all) once the full Romania batch is processed.
XBEACH_ROMANIA_DOMAIN_LABELS: dict[int, str] = {
    2: "2 — Chilia II",
    3: "3 — Sulina",
    4: "4 — Sfântu Gheorghe",
    5: "5 — Sacalin Spit",
    7: "7 — Portița II",
    8: "8 — Constanța",
}

XBEACH_REGION_DOMAIN_LABELS: dict[str, dict[int, str]] = {
    "BULGARIA": XBEACH_DOMAIN_LABELS,
    "ROMANIA": XBEACH_ROMANIA_DOMAIN_LABELS,
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


def xbeach_indicator_s3_uri(region: str, domain_id: int, scenario: str, filename: str) -> str:
    """s3://<bucket>/<base_prefix>/<region folder>/<period>/<indicator_nc|indicator_pmtiles>/<domain_id>_<scenario>_<filename>

    e.g. `.../XBEACH/BULGARIA/2020-2021/indicator_pmtiles/1_veg0_erosion_quads.pmtiles`.

    Flat layout (2026-09-22): domain+scenario is folded into the filename
    rather than being its own S3 "folder", so all 12 domains' files sit in
    one `indicator_nc/` and one `indicator_pmtiles/` folder -- see this
    module's docstring and `build_edito_upload_bundle.py`.
    """
    folder = "indicator_pmtiles" if filename.endswith(".pmtiles") else "indicator_nc"
    prefix = xbeach_s3_prefix(region)
    return f"s3://{XBEACH_S3_BUCKET}/{prefix}/{folder}/{domain_id}_{scenario}_{filename}"
