#!/bin/bash

# --- LSF Directives ---

# -- Set the job name and define it as a Job Array --
# This creates an array of 18 jobs, indexed from 1 to 18.
# %I will be replaced by the job array index (1-18) for each task.
# %J will be replaced by the overall job ID for the array.
#BSUB -J RecipeBatchArray[1-18]

# -- Choose the queue --
#BSUB -q gpua100

# -- Request GPU resources --
# Request 1 GPU in exclusive process mode *per array task*.
#BSUB -gpu "num=1:mode=exclusive_process"

# -- Specify memory per job --
# Requesting 24GB *per array task*.
#BSUB -R "rusage[mem=24GB]"

# -- Notify by email --
# Send email when the job begins and ends *for the entire array*.
#BSUB -B -N

# -- Specify your email address --
# Replace with your actual DTU email
#BSUB -u s233185@dtu.dk

# -- Output and Error files --
# %J is replaced by the job ID (for the array)
# %I is replaced by the job array index (1-18) for each task
# This creates separate output and error files for *each* task in the array,
#BSUB -o logs/batch_array_%J_%I.out
#BSUB -e logs/batch_array_%J_%I.err

# -- Estimated wall clock time (maximum execution time): HH:MM --
# Request 1 hour *per array task*
#BSUB -W 01:00 

# -- Number of tasks/cores requested --
# Request 4 CPU cores *per array task*.
#BSUB -n 4

# -- Specify the distribution of tasks: on a single node --
# Ensure *each task* runs on one node.
#BSUB -R "span[hosts=1]"

# -- End of LSF directives --

# --- Script Logic ---

echo "Starting LSF Job Array task: $LSB_JOBID (Array ID: $LSB_JOBID, Task Index: $LSB_JOBINDEX)"
echo "Running on host: $(hostname)"
echo "Current directory: $(pwd)"

# --- Determine Input and Output Files based on Array Index ---
# We have 18 files, recipes_batch_0001.csv to recipes_batch_0018.csv
# The array index $LSB_JOBINDEX goes from 1 to 18.
# We need to format the index with leading zeros (e.g., 1 -> 0001)

# Use printf to format the index with leading zeros to match your file naming
BATCH_NUM=$(printf "%04d" $LSB_JOBINDEX)

# Define paths for input and output files for *this specific task*
INPUT_CSV="recipes/batched_recipes/recipes_batch_${BATCH_NUM}.csv"
# Output to a dedicated directory for results, using the batch number in the filename
OUTPUT_CSV="LLM/batch_results/recipes_batch_${BATCH_NUM}.csv"

echo "Processing input file: $INPUT_CSV"
echo "Saving results to: $OUTPUT_CSV"

# Define the directory where the output CSV will be saved
OUTPUT_DIR=$(dirname "$OUTPUT_CSV")

# Create the output directory if it doesn't exist
echo "Ensuring output directory exists: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
MKDIR_STATUS=$?
if [ $MKDIR_STATUS -ne 0 ]; then
    echo "Error: Failed to create output directory '$OUTPUT_DIR'. Exit status: $MKDIR_STATUS"
    # Exit this specific array task with an error
    exit 1
fi
echo "Output directory ready."


# Load necessary modules
echo "Loading modules..."
# Load the exact available Python and CUDA module versions you need
module load python3/3.11.9
module load cuda/12.8.0
echo "Modules loaded."

# --- Python Environment Setup ---
# Add user-installed packages to PATH and PYTHONPATH
echo "Updating PATH and PYTHONPATH for user installs..."
# Get the Python version dynamically to correctly set the site-packages path
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="$HOME/.local/lib/python${PYTHON_VERSION}/site-packages:$PYTHONPATH"
echo "PATH and PYTHONPATH updated."

# Check GPU availability for diagnostics
echo "Checking for GPU availability for task $LSB_JOBINDEX:"
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Number of GPUs:', torch.cuda.device_count()); print('GPU device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"

# --- Run Your Python Script ---
# Execute the process_batch.py script, passing the specific input and output file paths
echo "Running Python script: process_batch.py"

# Make sure the path to your process_batch.py script is correct relative to your submission directory
PYTHON_SCRIPT="process_batch.py"

# Use the python3 command loaded by the module
python3 "$PYTHON_SCRIPT" "$INPUT_CSV" "$OUTPUT_CSV"
PYTHON_EXIT_STATUS=$?

# --- Check Python Script Exit Status ---
# If the Python script exits with a non-zero status, something went wrong.
if [ $PYTHON_EXIT_STATUS -ne 0 ]; then
    echo "Error: Python script failed for task $LSB_JOBINDEX with exit status: $PYTHON_EXIT_STATUS"
    echo "Check the error log (batch_array_%J_%I.err) for details."
    exit $PYTHON_EXIT_STATUS
fi

# --- Cleanup ---
echo "Task $LSB_JOBINDEX finished successfully."

# Exit the job script successfully for this task
exit 0
