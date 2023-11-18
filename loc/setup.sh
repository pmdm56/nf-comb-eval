CURRENT_EXPERIMENT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
TOOL_NFS_DIR=$CURRENT_EXPERIMENT_DIR/../../maestro-dev-env/shared/maestro/dpdk-nfs/nf-comb/examples-comb
HANDMADE_NFS_DIR=$CURRENT_EXPERIMENT_DIR/../../maestro-dev-env/shared/maestro/dpdk-nfs/nf-comb/examples-handmade

find "$TOOL_NFS_DIR" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | while read -r folder; do
    echo "Processing folder: $folder"
    (cd $TOOL_NFS_DIR && cloc $folder --csv --out="$CURRENT_EXPERIMENT_DIR/${folder}_cloc_tool.csv")
done

find "$HANDMADE_NFS_DIR" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | while read -r folder; do
    echo "Processing folder: $folder"
    (cd $HANDMADE_NFS_DIR && cloc $folder --csv --out="$CURRENT_EXPERIMENT_DIR/${folder}_cloc_hm.csv")
done

# cloc $nfs_hm --csv --out=loc_nfs_hm.csv

