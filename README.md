# SPEAR Ensemble Drought Analysis (SPI)

A parallelized workflow for calculating the **Standardized Precipitation Index (SPI)** using GFDL SPEAR Large Ensemble climate model data.

This tool is designed to:
1.  Ingest massive, multi-member ensemble datasets (NetCDF).
2.  Calculate the **Ensemble Mean** precipitation (Running Sum method).
3.  Compute seasonal SPI-3 (Standardized Precipitation Index) values.
4.  Generate visualization frames and animations for the continental US.

## Installation

1.  Clone the repository:

    git clone https://github.com/soelemaafnan/SPEAR_SPI_Analysis.git
    cd SPEAR_SPI_Analysis

2.  Install dependencies:
    
    pip install -r requirements.txt

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

How to run:
  1. Update the "config.yaml" file with your desired input/output locations.
  2. Update the "myjob.sl" file with the correct location for the source file.
  3. Submit the job using "sbatch myjob.sl" command.

## [DISCLAIMER]
**THIS IS A TEST REPOSITORY.**
The code and data outputs provided here are for internal testing and development purposes only.
