#!/bin/bash

# Usage: ./s3_sync_touch.sh <bucket-name> [--dry-run]

BUCKET=$1
DRY_RUN=false
JSON_LIST="csv_keys.json"

# Check for dry-run flag
if [[ "$2" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "\033[33m--- DRY RUN MODE: No actual S3 changes will be made ---\033[0m"
fi

# Validation
if [[ -z "$BUCKET" ]]; then
    echo "Error: Bucket name is required."
    echo "Usage: $0 <bucket-name> [--dry-run]"
    exit 1
fi

echo "Listing CSV keys from s3://$BUCKET..."

# 1. List keys for CSV files and save to a JSON list
aws s3api list-objects-v2 \
    --bucket "$BUCKET" \
    --query "Contents[?ends_with(Key, '.csv')].Key" \
    --output json > "$JSON_LIST"

KEY_COUNT=$(jq 'length' "$JSON_LIST")

if [[ "$KEY_COUNT" -eq 0 ]]; then
    echo "No CSV files found."
    exit 0
fi

echo "Found $KEY_COUNT files. Starting sequence..."
echo "-------------------------------------------"

# 2. Iterate through the JSON list
jq -r '.[]' "$JSON_LIST" | while read -r KEY; do
    # Extract the actual filename from the key (e.g., 'path/to/file.csv' -> 'file.csv')
    FILENAME=$(basename "$KEY")
    
    echo "Current Key: $KEY"
    echo "Local Filename: $FILENAME"

    if [ "$DRY_RUN" = true ]; then
        # Mock execution
        echo "[DRY-RUN] aws s3 cp s3://$BUCKET/$KEY ./${FILENAME}"
        echo "[DRY-RUN] sleep 3"
        echo "[DRY-RUN] aws s3 cp ./${FILENAME} s3://$BUCKET/$KEY"
    else
        # Actual execution
        echo "📥 Downloading..."
        aws s3 cp "s3://$BUCKET/$KEY" "./$FILENAME" > /dev/null
        
        echo "⏳ Waiting 3 seconds..."
        sleep 3
        
        echo "📤 Uploading..."
        aws s3 cp "./$FILENAME" "s3://$BUCKET/$KEY" > /dev/null
        
        # Cleanup
        rm "./$FILENAME"
        echo "✅ Done"
    fi
    echo "-------------------------------------------"
done

echo "Script complete. All entries processed."