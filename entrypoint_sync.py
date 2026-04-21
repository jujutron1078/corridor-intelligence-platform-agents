"""Download pipeline data from Cloudflare R2 using boto3 (S3-compatible)."""
import os
import logging

logger = logging.getLogger("corridor.sync")


def sync():
    data_dir = os.environ.get("CORRIDOR_DATA_ROOT", "/data")
    marker = os.path.join(data_dir, "freshness.json")

    if os.path.exists(marker):
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

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    bucket = "corridor-data"
    prefix = "v1/data/"
    downloaded = 0
    errors = 0

    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # Strip prefix to get relative path
                rel_path = key[len(prefix):]
                if not rel_path or rel_path.endswith("/"):
                    continue

                local_path = os.path.join(data_dir, rel_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                try:
                    s3.download_file(bucket, key, local_path)
                    downloaded += 1
                    if downloaded % 50 == 0:
                        logger.info("  ... downloaded %d files", downloaded)
                except Exception as e:
                    logger.warning("Failed to download %s: %s", key, e)
                    errors += 1

        logger.info("R2 sync complete: %d files downloaded, %d errors", downloaded, errors)
    except Exception as e:
        logger.error("R2 sync failed: %s", e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync()
