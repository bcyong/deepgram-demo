"""
Google Cloud Storage client utilities for file upload operations.
"""

from google.cloud import storage
from loguru import logger


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


def list_files(bucket_name: str) -> list[str]:
    """
    List all files in a Google Cloud Storage bucket.

    Args:
        bucket_name: Name of the GCS bucket to list files from

    Returns:
        list[str]: List of file names in the bucket

    Raises:
        Exception: For GCS-related errors
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        logger.info(f"Listing files in bucket: {bucket_name}")
        blobs = bucket.list_blobs()
        file_names = [blob.name for blob in blobs]

        logger.info(f"Found {len(file_names)} files in bucket {bucket_name}")
        return file_names

    except Exception as e:
        logger.error(f"Failed to list files from GCS bucket {bucket_name}: {str(e)}")
        raise
