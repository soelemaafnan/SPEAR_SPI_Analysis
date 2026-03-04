# SPEAR Ensemble Drought Analysis (SPI)

A parallelized workflow for calculating the **Standardized Precipitation Index (SPI)** using GFDL SPEAR Large Ensemble climate model data.

This tool is designed to:
1.  Ingest massive, multi-member ensemble datasets (NetCDF).
2.  Calculate the **Ensemble Mean** precipitation (Running Sum method).
3.  Compute seasonal SPI-3 (Standardized Precipitation Index) values.
4.  Generate visualization frames and animations for the continental US.

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/SPEAR_SPI_Analysis.git](https://github.com/yourusername/SPEAR_SPI_Analysis.git)
    cd SPEAR_SPI_Analysis
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Configuration
Edit `config/config.yaml` to point to your data directories.
```yaml
ensemble:
  base_dir: "/path/to/GFDL/data/"
  dir_prefix: "pp_ens_"
  start_member: 1
  end_member: 30

region:
  lat_min: 24  # USA Crop
  lat_max: 50
  lon_min: 235
  lon_max: 295
