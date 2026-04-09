# Bobcat Fire Pre-Fire UAVSAR Burn Severity Dataset

Pre-fire L-band polarimetric SAR dataset for the 2020 Bobcat Fire (Los Angeles County, CA), 
used in the study: *Pre-Fire Wildfire Burn Severity Modeling with Polarimetric UAVSAR Data 
and Deep Learning*.

## Contents

Feature rasters are provided at two resolutions. Ground truth is provided at 20 m only.

| File/Folder | Description |
|-------------|-------------|
| `20m/` | Feature rasters at 20 m resolution |
| `30m/` | Feature rasters at 30 m resolution |
| `Bobcat_SBS_final.tif` | BAER Soil Burn Severity — ground truth label (20 m) |

**20m/ and 30m/ each contain:**

| File | Description | Units | Resampling |
|------|-------------|-------|------------|
| `HHHH_reprojected_26911_[res]m_average_output.tif` | HH polarization (surface scattering) | dB | Average |
| `HVHV_reprojected_26911_[res]m_average_output.tif` | HV polarization (volume scattering / fuel load) | dB | Average |
| `VVVV_reprojected_26911_[res]m_average_output.tif` | VV polarization (moisture sensitivity) | dB | Average |
| `alpha1_reprojected_26911_[res]m_bilinear_output.tif` | Alpha 1 angle — Cloude-Pottier decomposition | degrees | Bilinear |
| `slope_1arc_reprojected_26911_[res]m_bilinear_output.tif` | Terrain slope derived from SRTM V3 DEM | degrees | Bilinear |

**Burn severity classes (`Bobcat_SBS_final.tif`):**
- 0 — Unburned/Very Low
- 1 — Low
- 2 — Moderate
- 3 — High

## Spatial Reference

- CRS: EPSG:26911 (UTM Zone 11N)
- Resolutions available: 20 m, 30 m

## Data Sources

- SAR data: [NASA UAVSAR](https://uavsar.jpl.nasa.gov) — flight lines SanAnd_08527 and SanAnd_26528/26526 (pre-fire: Feb 5, 2018; post-fire: Oct 11, 2018)
- Burn severity labels: [USDA Forest Service BAER](https://burnseverity.cr.usgs.gov)
- Fire perimeter: [MTBS Program](https://www.mtbs.gov)
- DEM: NASA EarthData SRTM V3 1-arc second

## Citation

If you use this dataset, please cite:

> Mannino, K. (2025). *Pre-Fire Wildfire Burn Severity Modeling with Polarimetric UAVSAR
> Data and Deep Learning*. Master's Thesis, Winston-Salem State University.

> Mannino, K., Deb, D., & An, K. (2025). Pre-ignition wildfire burn severity modeling with
> polarimetric UAVSAR data and machine learning. *SoutheastCon 2025*, Concord, NC, USA,
> pp. 1070–1071. https://doi.org/10.1109/SoutheastCon56624.2025.10971599

> Mannino, K., Deb, D., & An, K. (2026). Predicting wildfire burn severity from pre-fire SAR
> signatures: A deep learning approach. *Accepted to AAIML 2026*, Tokyo, Japan.

## Acknowledgments

This research was supported by NASA MUREP/DEAP IMPACT Award No. 80NSSC23M0054.