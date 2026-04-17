#!/bin/bash
set -e

DATA_DIR="${CORRIDOR_DATA_ROOT:-/data}"

# Sync data from R2 if the directory is empty or missing
if [ ! -f "$DATA_DIR/freshness.json" ]; then
    echo "Data not found at $DATA_DIR — syncing from R2..."
    if [ -n "$R2_ACCESS_KEY" ] && [ -n "$R2_SECRET_KEY" ] && [ -n "$R2_ENDPOINT" ]; then
        mkdir -p "$DATA_DIR"
        rclone sync \
            ":s3,provider=Cloudflare,access_key_id=$R2_ACCESS_KEY,secret_access_key=$R2_SECRET_KEY,endpoint=$R2_ENDPOINT:corridor-data/v1/data" \
            "$DATA_DIR" \
            --transfers=8 --checkers=4 --fast-list \
            --stats-one-line --stats=30s
        echo "Data sync complete: $(du -sh "$DATA_DIR" | cut -f1)"
    else
        echo "WARNING: R2 credentials not set — starting without data. Set R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT."
        mkdir -p "$DATA_DIR"
    fi
else
    echo "Data found at $DATA_DIR — skipping sync."
fi

# Hand off to the base image's default command
exec "$@"
