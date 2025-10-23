#!/usr/bin/env python3
"""
AWS S3 Folder Download Script
Downloads specific folders from S3 bucket using boto3 with AWS SSO profile
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("s3_download.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class S3FolderDownloader:
    def __init__(self, bucket_name: str, region: str, profile: str, local_path: str):
        self.bucket_name = bucket_name
        self.region = region
        self.profile = profile
        self.local_path = Path(local_path)
        self.s3_client = None
        self.s3_resource = None

    def initialize_s3_client(self) -> bool:
        """Initialize S3 client with the specified profile"""
        try:
            session = boto3.Session(profile_name=self.profile)
            self.s3_client = session.client("s3", region_name=self.region)
            self.s3_resource = session.resource("s3", region_name=self.region)

            # Test the connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✓ Successfully connected to S3 bucket: {self.bucket_name}")
            return True

        except ProfileNotFound:
            logger.error(f"❌ AWS profile '{self.profile}' not found")
            return False
        except NoCredentialsError:
            logger.error(
                "❌ No AWS credentials found. Please run 'aws sso login' first"
            )
            return False
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                logger.error(f"❌ Bucket '{self.bucket_name}' not found")
            elif error_code == "403":
                logger.error(
                    f"❌ Access denied to bucket '{self.bucket_name}'. Check your permissions"
                )
            else:
                logger.error(f"❌ Error accessing bucket: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False

    def list_folder_objects(self, folder_prefix: str) -> List[dict]:
        """List all objects in a specific folder"""
        objects = []
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name, Prefix=folder_prefix
            )

            for page in page_iterator:
                if "Contents" in page:
                    objects.extend(page["Contents"])

            logger.info(f"Found {len(objects)} objects in folder: {folder_prefix}")
            return objects

        except ClientError as e:
            logger.error(f"❌ Error listing objects in folder {folder_prefix}: {e}")
            return []

    def download_file(self, s3_key: str, local_file_path: Path) -> bool:
        """Download a single file from S3"""
        try:
            # Create parent directories if they don't exist
            local_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Download the file
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_file_path))
            return True

        except ClientError as e:
            logger.error(f"❌ Error downloading {s3_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading {s3_key}: {e}")
            return False

    def download_folder(self, folder_name: str) -> tuple[int, int]:
        """Download all files from a specific folder"""
        folder_prefix = f"{folder_name}/"
        local_folder_path = self.local_path / folder_name

        logger.info(f"🔄 Starting download for folder: {folder_name}")

        # List all objects in the folder
        objects = self.list_folder_objects(folder_prefix)

        if not objects:
            logger.warning(f"⚠️  No objects found in folder: {folder_name}")
            return 0, 0

        # Filter out folder markers (objects ending with '/')
        files = [obj for obj in objects if not obj["Key"].endswith("/")]

        if not files:
            logger.warning(f"⚠️  No files found in folder: {folder_name}")
            return 0, 0

        logger.info(f"📁 Downloading {len(files)} files from folder: {folder_name}")

        successful_downloads = 0
        failed_downloads = 0

        # Create progress bar
        with tqdm(
            total=len(files), desc=f"Downloading {folder_name}", unit="file"
        ) as pbar:
            for obj in files:
                s3_key = obj["Key"]
                file_size = obj["Size"]

                # Calculate relative path within the folder
                relative_path = s3_key[len(folder_prefix) :]
                local_file_path = local_folder_path / relative_path

                # Update progress bar description with current file
                pbar.set_postfix(
                    file=relative_path[:30] + "..."
                    if len(relative_path) > 30
                    else relative_path
                )

                if self.download_file(s3_key, local_file_path):
                    successful_downloads += 1
                else:
                    failed_downloads += 1

                pbar.update(1)

        logger.info(
            f"✅ Completed folder {folder_name}: {successful_downloads} successful, {failed_downloads} failed"
        )
        return successful_downloads, failed_downloads

    def download_folders(self, folder_names: List[str]) -> dict:
        """Download multiple folders"""
        results = {
            "total_folders": len(folder_names),
            "successful_folders": 0,
            "failed_folders": 0,
            "total_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "start_time": datetime.now(),
            "folder_results": {},
        }

        logger.info(f"🚀 Starting download of {len(folder_names)} folders")
        logger.info(f"📂 Local download path: {self.local_path}")

        for folder_name in folder_names:
            try:
                successful_files, failed_files = self.download_folder(folder_name)

                results["folder_results"][folder_name] = {
                    "successful_files": successful_files,
                    "failed_files": failed_files,
                }

                results["total_files"] += successful_files + failed_files
                results["successful_files"] += successful_files
                results["failed_files"] += failed_files

                if failed_files == 0:
                    results["successful_folders"] += 1
                else:
                    results["failed_folders"] += 1

            except Exception as e:
                logger.error(
                    f"❌ Unexpected error processing folder {folder_name}: {e}"
                )
                results["failed_folders"] += 1
                results["folder_results"][folder_name] = {
                    "successful_files": 0,
                    "failed_files": 0,
                    "error": str(e),
                }

        results["end_time"] = datetime.now()
        results["duration"] = results["end_time"] - results["start_time"]

        return results

    def print_summary(self, results: dict):
        """Print download summary"""
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"📁 Total folders: {results['total_folders']}")
        print(f"✅ Successful folders: {results['successful_folders']}")
        print(f"❌ Failed folders: {results['failed_folders']}")
        print(f"📄 Total files: {results['total_files']}")
        print(f"✅ Successful files: {results['successful_files']}")
        print(f"❌ Failed files: {results['failed_files']}")
        print(f"⏱️  Duration: {results['duration']}")
        print(f"📂 Download location: {self.local_path}")

        if results["failed_folders"] > 0:
            print("\n❌ Failed folders:")
            for folder, result in results["folder_results"].items():
                if result.get("failed_files", 0) > 0:
                    print(f"  - {folder}: {result.get('failed_files', 0)} failed files")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Download folders from AWS S3 bucket")
    parser.add_argument(
        "--bucket",
        default="production-cb-offergenerator",
        help="S3 bucket name (default: production-cb-offergenerator)",
    )
    parser.add_argument(
        "--region", default="eu-west-2", help="AWS region (default: eu-west-2)"
    )
    parser.add_argument(
        "--profile", default="production", help="AWS profile name (default: production)"
    )
    parser.add_argument(
        "--local-path",
        default="./downloads",
        help="Local download path (default: ./downloads)",
    )
    parser.add_argument(
        "--folders",
        nargs="+",
        default=[
            "77580",
            "77667",
            "77828",
            "77579",
            "77666",
            "77829",
            "77669",
            "77748",
            "77826",
            "77708",
            "77789",
            "77863",
        ],
        help="List of folder names to download",
    )

    args = parser.parse_args()

    # Create downloader instance
    downloader = S3FolderDownloader(
        bucket_name=args.bucket,
        region=args.region,
        profile=args.profile,
        local_path=args.local_path,
    )

    # Initialize S3 client
    if not downloader.initialize_s3_client():
        sys.exit(1)

    # Create local download directory
    downloader.local_path.mkdir(parents=True, exist_ok=True)

    # Download folders
    results = downloader.download_folders(args.folders)

    # Print summary
    downloader.print_summary(results)

    # Exit with appropriate code
    if results["failed_folders"] == 0:
        logger.info("🎉 All downloads completed successfully!")
        sys.exit(0)
    else:
        logger.warning("⚠️  Some downloads failed. Check the log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
