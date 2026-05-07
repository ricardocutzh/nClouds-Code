#!/bin/sh

# Ensure variables are set
if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3_BUCKET is not set."
    exit 1
fi

# Directory to store checksums of previously synced files
HASH_DIR="/tmp/sync-hashes"
mkdir -p "$HASH_DIR"

# Upload a file only if its content has changed since last upload
sync_if_changed() {
    local file="$1"
    local key="$2"
    local cache_control="$3"

    # Compute current checksum
    local current_hash
    current_hash=$(md5sum "$file" | awk '{print $1}')

    # Build a safe path for storing the previous hash
    local hash_file="$HASH_DIR/$(echo "$key" | tr '/' '_')"

    # Compare with previously uploaded hash
    if [ -f "$hash_file" ] && [ "$(cat "$hash_file")" = "$current_hash" ]; then
        return 0  # unchanged, skip upload
    fi

    # Upload and store new hash on success
    if aws s3 cp "$file" "s3://$S3_BUCKET/$key" \
        --cache-control "$cache_control" \
        --no-progress; then
        echo "$current_hash" > "$hash_file"
    fi
}

echo "Starting S3 Sync to s3://$S3_BUCKET every 2 seconds..."

while true; do
    # 1. Sync .ts segment files — only upload new or changed segments
    find /src -name "*.ts" ! -name "*.tmp" | while read -r file; do
        key="${file#/src/}"
        sync_if_changed "$file" "$key" "max-age=31536000" &
    done

    # 2. Sync .m3u8 playlists — only upload if content changed
    find /src -name "*.m3u8" | while read -r file; do
        key="${file#/src/}"
        sync_if_changed "$file" "$key" "no-cache, no-store, must-revalidate" &
    done

    # Wait for all uploads to finish
    wait

    sleep 2
done