import xarray as xr
import numpy as np
import glob
import os
import yaml
from dask.distributed import Client, LocalCluster
from climate_indices import indices, compute

# ==========================================
# 1. LOAD CONFIGURATION
# ==========================================
config_file = "config.yaml"
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Config file not found: {config_file}")

with open(config_file, "r") as f:
    cfg = yaml.safe_load(f)

os.makedirs(cfg['output_directory'], exist_ok=True)

# ==========================================
# 2. DEFINE WORKER FUNCTION
# ==========================================
def calc_spi_1d(values, scale, start_year, end_year):
    if np.all(np.isnan(values)) or np.all(values == 0):
        return values
    try:
        return indices.spi(
            values,
            scale=scale,
            distribution=indices.Distribution.gamma,
            data_start_year=start_year,
            calibration_year_initial=start_year,
            calibration_year_final=end_year,
            periodicity=compute.Periodicity.monthly
        )
    except ValueError:
        return np.full_like(values, np.nan)

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("Initializing Dask Cluster...")

    # --- SLURM DETECTION ---
    slurm_cpus = os.environ.get('SLURM_CPUS_PER_TASK')
    slurm_tasks = os.environ.get('SLURM_NTASKS')
    
    if slurm_cpus:
        n_workers = int(slurm_cpus)
    elif slurm_tasks:
        n_workers = int(slurm_tasks)
    else:
        n_workers = 4
        
    print(f"  -> Using {n_workers} workers.")
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1)
    client = Client(cluster)
    print(f"  -> Dashboard: {client.dashboard_link}")

    # ==========================================
    # 4. CALCULATE ENSEMBLE MEAN (RUNNING SUM)
    # ==========================================
    print("\n--- Starting Ensemble Averaging ---")
    
    ensemble_sum = None
    member_count = 0
    
    start_id = cfg['ensemble']['start_member']
    end_id = cfg['ensemble']['end_member']
    
    # Loop through Members 1 to 30
    for member_id in range(start_id, end_id + 1):
        member_str = f"{member_id:02d}"  # Formats 1 as "01"
        
        # Construct path: Base + pp_ens_XX + SubDir
        member_path = os.path.join(
            cfg['ensemble']['base_dir'],
            f"{cfg['ensemble']['dir_prefix']}{member_str}",
            cfg['ensemble']['sub_dir']
        )
        
        # Find files for this member
        pattern = os.path.join(member_path, cfg['file_pattern'])
        files = sorted(glob.glob(pattern))
        
        if not files:
            print(f"  WARNING: No files found for member {member_str}. Skipping.")
            continue
            
        print(f"  Processing Member {member_str} ({len(files)} files)...")

        # A. Load Lazy
        ds = xr.open_mfdataset(
            files, 
            concat_dim="time", 
            combine="nested", 
            parallel=True,
            chunks={'lat': 45, 'lon': 45}, 
            decode_timedelta=False 
        )

        # B. Crop to USA (Crucial for memory!)
        ds_cropped = ds.sel(
            lat=slice(cfg['region']['lat_min'], cfg['region']['lat_max']), 
            lon=slice(cfg['region']['lon_min'], cfg['region']['lon_max'])
        )

        # C. Resample to Monthly (Reduce Data Size)
        var_name = cfg['variable_name']
        monthly_rate = ds_cropped[var_name].resample(time="1MS").mean()
        
        # Calculate Monthly Total (mm)
        # We compute this immediately to free up the memory of the raw files
        seconds_in_month = monthly_rate.time.dt.days_in_month * 86400
        da_monthly = monthly_rate * seconds_in_month
        
        # D. Add to Running Sum
        if ensemble_sum is None:
            # First member initializes the sum array
            ensemble_sum = da_monthly
        else:
            # Subsequent members add to it
            ensemble_sum = ensemble_sum + da_monthly
            
        member_count += 1

    if member_count == 0:
        raise RuntimeError("No ensemble members were successfully processed!")

    print(f"\nComputing final average of {member_count} members...")
    
    # Divide sum by count to get the Mean
    ensemble_mean = ensemble_sum / member_count
    
    # Re-chunk for time-series calculation
    ensemble_mean = ensemble_mean.chunk({'time': -1, 'lat': 45, 'lon': 45})

    # ==========================================
    # 5. CALCULATE SPI ON ENSEMBLE MEAN
    # ==========================================
    start_year = cfg['spi']['base_period_start']
    end_year = cfg['spi']['base_period_end']
    scale = cfg['spi']['scale']
    
    print(f"Calculating SPI-{scale} on Ensemble Mean ({start_year}-{end_year})...")

    spi_full = xr.apply_ufunc(
        calc_spi_1d,
        ensemble_mean,
        input_core_dims=[['time']],
        output_core_dims=[['time']],
        kwargs={'scale': scale, 'start_year': start_year, 'end_year': end_year},
        vectorize=True,
        dask='parallelized',
        output_dtypes=[np.float64]
    )
    
    spi_full = spi_full.assign_coords(time=ensemble_mean.time)

    # ==========================================
    # 6. EXTRACT SEASONS & SAVE
    # ==========================================
    seasons = {
        "Winter": 2, "Spring": 5, "Summer": 8, "Fall": 11
    }
    encoding = {'spi3': {'zlib': True, 'complevel': 5}}
    
    print("Saving Ensemble Mean Seasonal Files...")

    for season_name, month_idx in seasons.items():
        print(f"  -> Extracting {season_name}...")
        season_data = spi_full.sel(time=spi_full.time.dt.month == month_idx)
        season_data.name = f"spi{scale}"
        
        # Updated Filename to reflect "EnsembleMean"
        filename = f"SPI{scale}_USA_EnsembleMean_{season_name}_{start_year}-{end_year}.nc"
        output_path = os.path.join(cfg['output_directory'], filename)
        
        season_data.to_netcdf(output_path, encoding=encoding)
        print(f"     Saved {output_path}")

    print("Ensemble Processing Complete.")