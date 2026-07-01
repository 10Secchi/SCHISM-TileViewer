<div style="display: flex; justify-content: space-between; align-items: center;">
  <img src="FOCCUS_Logo_clean RGB_whiteBG.png" alt="FOCCUS" width="180">
  <img src="https://www.hereon.de/cms60/res/assets/logos/hereon_logo.svg" alt="Hereon" width="220">
</div>

# FOCCUS Demonstrator: Management and Protection of the Coastal Area - Western Black Sea

## WHY? - Objective and Background

The objective of this demonstrator is to showcase the results of Application 2.1.2.3 ([D8.1](https://docs.google.com/document/d/1AXOMLxra9OLt3CGxj5IWgSxqhNLrOAe-/edit)), which addresses the Environmental and Societal Challenge (ESC) from Topic Group 1: **Coastal Erosion Dynamics** for the Northwestern Black Sea pilot area.

Coastal hazards are becoming increasingly severe due to the combined effects of storms and the reduction in sediment supply. Addressing the driving mechanisms behind these hazards requires process-based models to resolve hydrodynamic, wave, and morphodynamic processes. In FOCCUS ESC1, the [GCOAST-BS](https://www.hereon.de/institutes/coastal_systems_analysis_modeling/research/gcoast/applications/index.php.en) forecasting system has been enhanced and extended across coastal modelling capabilities in the Northwestern Black Sea. This downstream application can be launched as a dashboard from the sidebar menu and has been developed to support coastal assessment and provide insights for adaptation plans against coastal hazards.

<img src="ToggleB.png" width="30%">

The application aims to:

- assess coastal hazard risks using dedicated indicators from the process-based model GCOAST-BS;
- provide actionable metrics for policy- and decision-makers;
- demonstrate capabilities for providing assessments with seamless-scale interactivity.

## Target Audience

This application is aimed at MSCS operators, coastal managers, and stakeholders for early warning and decision-making in the planning of nature-based coastal protection.

The audience is invited to navigate interactively through the dashboard and check the results from ESC1 for their area of interest.

# WHAT? - What is Assessed

The application evaluates the erosion risk class for coastal hazards based on hindcast simulations. These outcomes allow seamless-scale assessments along the entire coastal domain. The results can: i) identify hotspots for coastal hazards across the entire coastal domain; and ii) help plan Nature-based Solutions at hotspots for coastal erosion identified by the indicator metrics.

## Assessments, Metrics, and Indicators

The following indicator metrics summarise extreme and erosion-relevant conditions over the forecast period. They are derived from SCHISM/GCOAST-BS simulations on the native unstructured mesh and exported for interactive viewing and polygon-based area assessment.

| Indicator | Symbol / variable | Description | Unit |
|-----------|-------------------|-------------|------|
| Sea-surface height q95 | SSH q95 | 95th percentile of sea-surface height | m |
| Significant wave height q95 | Hs q95 | 95th percentile of significant wave height | m |
| Bottom stress q95 | τ q95 | 95th percentile of bed shear stress | Pa |
| Bedload transport rate q95 | sed q95 | 95th percentile of bedload transport rate | kg m⁻¹ s⁻¹ |
| Erosion risk ratio | R1 (ERI) | Relative duration of critical shear-stress exceedance (wet timesteps only) | — |

### Erosion Risk Index (ERI)

The erosion risk index (R1) expresses the temporal fraction of non-dry timesteps during which the critical bed shear stress is exceeded, relative to a grain-size-distribution-dependent threshold. Values below 0.12 are masked (no risk). This quantity is commonly used in process-based models employed over continental shelves worldwide, making it useful for cross-comparison and discussion with areas undergoing similar conditions.

The categorical risk bins are:

| ERI class | Risk level | Critical shear-stress exceedance duration |
|------------|------------|-------------------------------------------|
| — | No risk | < 25% |
| 0.25 – 0.50 | Low | 25 – 50% |
| 0.50 – 0.75 | Increased | 50 – 75% |
| ≥ 0.75 | High | ≥ 75% |

In the web application, R1 is shown with a stepped colour scale (yellow/orange/red) and can be assessed against selectable critical levels of **Low**, **Increased**, or **High** (no colour denotes no risk or areas outside the domain).

### Interactive Display and Area Assessment

The application allows users to **explore coastal hazard indicators** across the Northwestern Black Sea and perform **area-based assessments** for locations of interest.

Users can:

1. **Select a forecast and indicator** – Choose a simulation date and the indicator to explore (e.g. wave height, bed stress, erosion risk, or vegetation cover).
2. **Explore the map** – View the selected indicator on an interactive map. The colour scale, opacity, and basemap can be adjusted to improve visualization.
3. **Define an area of interest** – Draw a polygon around any coastal zone, such as a beach, harbour approach, or Nature-based Solution (NbS) site.
4. **Analyse the selected area** – The application provides:
   - summary statistics (mean, minimum, maximum, and total area);
   - the proportion of the area above or below a selected threshold;
   - the distribution of indicator values within the selected area;
   - a map highlighting where the threshold is exceeded.

## HOW? - How Was This Application Made and Improved within FOCCUS

Simulations are performed on an unstructured grid with coastward-increasing resolution (3 km to 100 m), enabling the representation of large-scale coastal processes while resolving nearshore dynamics with coupled modules (SCHISM-SED3D-WWM). To assess beach-scale erosion and morphodynamic response, a high-resolution XBeach sub-nest (10–50 m) is implemented for regions of interest. Both models allow the evaluation of scenarios and the influence of hydrodynamics, wave attenuation over the seabed, and consequently sediment transport, which are the driving mechanisms of coastal erosion.

<img src="NestingSystem.png" width="101%">

The application workflow's modelling system integration within (among other inputs and developments) Copernicus Marine Services and FOCCUS developments, with links to the respective deliverables and milestones, are given in the flowchart for ESC 1.2.3 through the PDF content (better visualization with the Firefox web browser):

```python
streamlit_insert_pdf = "DF122.pdf"
```

The GCOAST-BS system has undergone FOCCUS-specific improvements related to different WP activities, such as:

- Upgrading river forcing from climatological to E-HYPE, enabling the representation of small rivers and improving simulated coastal salinities.
- Implementing improved physics parameterizations with water types and suitable turbulence closure.
- Improving bathymetry and seabed morphology using newer datasets from EMODnet.
- Interfacing with regional reanalysis products using a parametric 2D wave spectrum derived from CMEMS.

<img src="WPs.png" width="40%">

The assessment methodology in this demonstrator is a combination of previously published work by [(Gramcianinov et al. 2026)](https://doi.org/10.1016/j.ocemod.2026.102749) and detailed beach-scale erosion studies at Norderney [(Silva et al. 2026)](https://doi.org/10.1016/j.jenvman.2026.128756).
