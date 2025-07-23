"""
Google Cloud Storage client utilities for file upload operations.
"""

from google.cloud import storage
from loguru import logger
from typing import List


def upload_file(
    bucket_name: str,
    source_file_name: str,
    destination_file_name: str,
    overwrite: bool = False,
) -> bool:
    """
    Upload a file to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket to upload to
        source_file_name: Local file path to upload
        destination_file_name: Name to give the file in GCS

    Returns:
        bool: True if upload was successful

    Raises:
        FileNotFoundError: If source file doesn't exist
        Exception: For other GCS-related errors
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_file_name)

        if not overwrite and blob.exists():
            logger.info(f"File {destination_file_name} already exists in GCS")
            return False

        logger.info(
            f"Uploading {source_file_name} to gs://{bucket_name}/{destination_file_name}"
        )
        blob.upload_from_filename(source_file_name)

        logger.info(f"Successfully uploaded {source_file_name} to GCS")
        return True

    except FileNotFoundError:
        logger.error(f"Source file not found: {source_file_name}")
        raise
    except Exception as e:
        logger.error(f"Failed to upload file to GCS: {str(e)}")
        raise


def download_file(
    bucket_name: str, source_file_name: str, destination_file_name: str
) -> bool:
    """
    Download a file from Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket to download from
        source_file_name: Name of the file in GCS to download
        destination_file_name: Local file path to save the downloaded file

    Returns:
        bool: True if download was successful

    Raises:
        Exception: For GCS-related errors
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_file_name)

        logger.info(
            f"Downloading gs://{bucket_name}/{source_file_name} to {destination_file_name}"
        )
        blob.download_to_filename(destination_file_name)

        logger.info(f"Successfully downloaded {source_file_name} from GCS")
        return True

    except Exception as e:
        logger.error(f"Failed to download file from GCS: {str(e)}")
        raise


def list_files(bucket_name: str, folder_name: str = "") -> list[str]:
    """
    List all files in a Google Cloud Storage bucket within a specific folder.

    Args:
        bucket_name: Name of the GCS bucket to list files from
        folder_name: Name of the folder within the bucket (optional)

    Returns:
        list[str]: List of file names in the bucket/folder

    Raises:
        Exception: For GCS-related errors
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Normalize folder name to ensure it ends with '/'
        if folder_name and not folder_name.endswith("/"):
            folder_name = folder_name + "/"

        logger.info(
            f"Listing files in bucket: {bucket_name}, folder: {folder_name or 'root'}"
        )

        # List blobs with prefix to filter by folder
        blobs = bucket.list_blobs(prefix=folder_name)
        file_names = [
            blob.name for blob in blobs if not blob.name.endswith("/")
        ]  # Exclude folder objects

        logger.info(
            f"Found {len(file_names)} files in bucket {bucket_name}, folder: {folder_name or 'root'}"
        )
        return file_names

    except Exception as e:
        logger.error(
            f"Failed to list files from GCS bucket {bucket_name}, folder {folder_name}: {str(e)}"
        )
        raise


def generate_signed_urls(
    bucket_name: str, file_names: List[str], expiration_minutes: int = 60
) -> List[str]:
    """
    Generate signed URLs for GCS blobs so they can be accessed by external services.

    Args:
        bucket_name: Name of the GCS bucket
        file_names: List of file names in the bucket
        expiration_minutes: How long the signed URLs should be valid (default: 60 minutes)

    Returns:
        List of signed URLs for the files

    Raises:
        Exception: For GCS-related errors
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        signed_urls = []

        for file_name in file_names:
            blob = bucket.blob(file_name)
            signed_url = blob.generate_signed_url(
                expiration=expiration_minutes * 60,  # Convert minutes to seconds
                method="GET",
            )
            signed_urls.append(signed_url)
            logger.info(f"Generated signed URL for {file_name}")

        logger.info(
            f"Generated {len(signed_urls)} signed URLs for bucket {bucket_name}"
        )
        return signed_urls

    except Exception as e:
        logger.error(
            f"Failed to generate signed URLs for bucket {bucket_name}: {str(e)}"
        )
        raise
