#!/bin/bash

# Default values
DRY_RUN=false
REGION=""
FILE=""

# Usage information
usage() {
    echo "Usage: $0 -f <snapshot_ids_file> -r <region> [-d]"
    echo "  -f: Path to the .txt file containing snapshot IDs"
    echo "  -r: AWS region (e.g., us-east-1)"
    echo "  -d: Dry run (prints the actions without deleting)"
    exit 1
}

# Parse flags
while getopts "f:r:d" opt; do
    case $opt in
        f) FILE="$OPTARG" ;;
        r) REGION="$OPTARG" ;;
        d) DRY_RUN=true ;;
        *) usage ;;
    esac
done

# Basic validation
if [[ -z "$FILE" || -z "$REGION" ]]; then
    echo "❌ Error: Missing required arguments."
    usage
fi

if [[ ! -f "$FILE" ]]; then
    echo "❌ Error: File '$FILE' not found."
    exit 1
fi

echo "🚀 Starting operation in region: $REGION"
if [ "$DRY_RUN" = true ]; then
    echo "⚠️  DRY RUN ENABLED: No snapshots will actually be deleted."
fi
echo "--------------------------------------------------"

# Loop through the file
while IFS= read -r snapshot_id || [[ -n "$snapshot_id" ]]; do
    # Trim whitespace or hidden carriage returns (useful if file was edited on Windows)
    id=$(echo "$snapshot_id" | tr -d '\r' | xargs)

    # Skip empty lines
    if [[ -z "$id" ]]; then
        continue
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would delete snapshot: $id"
        # Optional: Use AWS CLI's built-in dry-run to verify permissions/existence
        # aws ec2 delete-snapshot --snapshot-id "$id" --region "$REGION" --dry-run 2>&1 | grep -q 'DryRunOperation'
    else
        echo "🗑️  Deleting snapshot: $id..."
        aws ec2 delete-snapshot --snapshot-id "$id" --region "$REGION"
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully requested deletion for $id"
        else
            echo "❌ Failed to delete $id"
        fi
    fi
done < "$FILE"

echo "--------------------------------------------------"
echo "🏁 Operation complete."