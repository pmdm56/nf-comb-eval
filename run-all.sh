SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Define an array with the subfolders
EVALS=("latency" "throughput")

# Loop through each subfolder and run setup.sh
for FOLDER in "${EVALS[@]}"
do
    cd "$SCRIPT_DIR/$FOLDER" || exit 1
    ./setup.sh
    cd "$SCRIPT_DIR" || exit 1
done
