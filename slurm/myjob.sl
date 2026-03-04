#!/bin/bash
#SBATCH -A gfdl_a
#SBATCH -J spi
#SBATCH -o %x_%j.out
#SBATCH -e %x_%j.err
#SBATCH -p analysis
#SBATCH -t 48:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mail-user=soelem.bhuiyan@noaa.gov
#SBATCH --mail-type=BEGIN,END,FAIL

# --- Ensure the script runs from the submission directory ---
cd $SLURM_SUBMIT_DIR

# --- Environment Setup ---
module purge
module load conda
conda activate gfdl

# --- Execute the Python script ---
echo "Starting Python script..."
python spi_ensemble_mean.py
echo "Script finished."
