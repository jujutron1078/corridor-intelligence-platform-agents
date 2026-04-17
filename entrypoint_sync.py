"""One-time data sync from R2 — runs before uvicorn starts."""
import os
import subprocess
import sys

def sync():
    data_dir = os.environ.get("CORRIDOR_DATA_ROOT", "/data")
    marker = os.path.join(data_dir, "freshness.json")

    if os.path.exists(marker):
        print(f"Data found at {data_dir} — skipping sync.")
        return

    access_key = os.environ.get("R2_ACCESS_KEY", "")
    secret_key = os.environ.get("R2_SECRET_KEY", "")
    endpoint = os.environ.get("R2_ENDPOINT", "")

    if not all([access_key, secret_key, endpoint]):
        print("WARNING: R2 credentials not set — starting without data.")
        os.makedirs(data_dir, exist_ok=True)
        return

    print(f"Syncing data from R2 to {data_dir}...")
    os.makedirs(data_dir, exist_ok=True)

    remote = f":s3,provider=Cloudflare,access_key_id={access_key},secret_access_key={secret_key},endpoint={endpoint}:corridor-data/v1/data"

    result = subprocess.run(
        ["rclone", "sync", remote, data_dir, "--transfers=8", "--fast-list", "--stats-one-line", "--stats=30s"],
        capture_output=False,
    )

    if result.returncode == 0:
        print(f"Data sync complete.")
    else:
        print(f"Data sync failed (exit {result.returncode}) — starting with partial/empty data.")

if __name__ == "__main__":
    sync()
