"""Download pipeline data from Cloudflare R2 using boto3 (S3-compatible)."""
import os
import logging

logger = logging.getLogger("corridor.sync")


def sync(force=False):
    data_dir = os.environ.get("CORRIDOR_DATA_ROOT", "/data")
    marker = os.path.join(data_dir, "freshness.json")

    if os.path.exists(marker) and not force:
        logger.info("Data found at %s — skipping sync.", data_dir)
        return

    access_key = os.environ.get("R2_ACCESS_KEY", "")
    secret_key = os.environ.get("R2_SECRET_KEY", "")
    endpoint = os.environ.get("R2_ENDPOINT", "")

    if not all([access_key, secret_key, endpoint]):
        logger.warning("R2 credentials not set — starting without data.")
        os.makedirs(data_dir, exist_ok=True)
        return

    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        logger.error("boto3 not installed — cannot sync from R2")
        return

    logger.info("Syncing data from R2 to %s ...", data_dir)
    os.makedirs(data_dir, exist_ok=True)

    from boto3.s3.transfer import TransferConfig

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
        ),
        region_name="auto",
    )

    # Multipart download for large files — 8 MB chunks, 4 threads
    transfer_config = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,
        max_concurrency=4,
        multipart_chunksize=8 * 1024 * 1024,
    )

    bucket = "corridor-data"
    prefix = "v1/data/"
    downloaded = 0
    errors = 0

    # Skip large raster dirs that exceed Railway's 500 MB volume limit.
    # These are non-essential for the main map/dashboards.
    SKIP_PREFIXES = {"v1/data/connectivity/", "v1/data/livestock/"}

    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # Strip prefix to get relative path
                rel_path = key[len(prefix):]
                if not rel_path or rel_path.endswith("/"):
                    continue

                # Skip large non-essential dirs
                if any(key.startswith(sp) for sp in SKIP_PREFIXES):
                    continue

                local_path = os.path.join(data_dir, rel_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                # Skip if file already exists and has same size
                if not force and os.path.exists(local_path):
                    local_size = os.path.getsize(local_path)
                    if local_size == obj.get("Size", -1):
                        downloaded += 1
                        continue

                try:
                    size_mb = obj.get("Size", 0) / 1e6
                    if size_mb > 10:
                        logger.info("  downloading %s (%.0f MB)...", rel_path, size_mb)
                    s3.download_file(bucket, key, local_path, Config=transfer_config)
                    downloaded += 1
                    if downloaded % 50 == 0:
                        logger.info("  ... downloaded %d files", downloaded)
                except Exception as e:
                    logger.warning("Failed to download %s (%.0f MB): %s", key, obj.get("Size", 0) / 1e6, e)
                    errors += 1

        logger.info("R2 sync complete: %d files downloaded, %d errors", downloaded, errors)
    except Exception as e:
        logger.error("R2 sync failed: %s", e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync()
