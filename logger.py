import io
import logging
from google.cloud import storage  # type: ignore
import pandas as pd # type: ignore
from io import StringIO
from datetime import datetime
import csv
import json
from typing import Any, Tuple, Union
from google.cloud import storage
import random
import time
from logging import Logger
import os


class LoggerUtil:
    """
    A custom logger utility for configuring and managing logging outputs, 
    including local files and Google Cloud Storage (GCS).

    This logger supports two main configurations:
    1. Logging to a local file.
    2. Logging to an in-memory buffer with the option to upload logs to GCS.
    """

    def __init__(self, bucket_name, name=__name__, level=logging.DEBUG):
        """
        Initialize the Logger instance with a specified name and logging level.

        Args:
            name (str): The name of the logger, typically the module's name. Defaults to `__name__`.
            level (int): The logging level (e.g., `logging.DEBUG`, `logging.INFO`).
                         Defaults to `logging.DEBUG`.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self.logger.handlers = []
        self.bucket_name = bucket_name
        self.name = name

    def configure_logger_file(
        self,
        filename: str,
        level=logging.DEBUG,
        formatter="%(asctime)s - %(levelname)s - %(message)s",
    ):
        """
        Configure the logger to write log messages to a local file.

        Args:
            filename (str): The path to the file where logs should be written.
            level (int): The logging level (e.g., `logging.DEBUG`, `logging.INFO`).
                         Defaults to `logging.DEBUG`.
            formatter (str): The format string for log messages. 
                             Defaults to "%(asctime)s - %(levelname)s - %(message)s".
        """
        self.logger.handlers = []
        self.file_handler = logging.FileHandler(filename, mode="a")
        self.file_handler.setLevel(level)
        self.file_handler.setFormatter(logging.Formatter(formatter))
        self.logger.addHandler(self.file_handler)

    def configure_logger_gcs(
        self,
        bucket_name: str,
        file_path: str,
        level=logging.DEBUG,
        formatter="%(asctime)s - %(levelname)s - %(message)s",
    ):
        """
        Configure the logger to capture log messages in memory and prepare for upload to GCS.

        Args:
            bucket_name (str): The name of the GCS bucket where logs will be uploaded.
            file_path (str): The path in the GCS bucket where logs will be stored.
            level (int): The logging level (e.g., `logging.DEBUG`, `logging.INFO`).
                         Defaults to `logging.DEBUG`.
            formatter (str): The format string for log messages. 
                             Defaults to "%(asctime)s - %(levelname)s - %(message)s".
        """
        self.logger.handlers = []
        self.memory_file = io.StringIO()
        self.memory_handler = logging.StreamHandler(self.memory_file)
        self.memory_handler.setLevel(level)
        self.memory_handler.setFormatter(logging.Formatter(formatter))
        self.logger.addHandler(self.memory_handler)

        self.bucket_name = bucket_name
        self.file_path = file_path
        self.gcp_upload_path = ''

    def set_upload_path(self, folder: str) -> str:
        """
        Define and set the upload path for logs or files in the GCS bucket.

        Args:
            folder (str): The folder within the GCS bucket where the file will be uploaded.

        Returns:
            str: The full path (folder) for the upload in the GCS bucket.
        """
        # Construct the full upload path
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # self.upload_path = f"{folder}/{timestamp}-{filename}".strip("/")
        self.gcp_upload_path = folder
        return self.gcp_upload_path


    def upload_log_to_gcs(self):
        """
        Upload the in-memory log contents to a specified GCS bucket and path.

        Raises:
            ValueError: If the logger is not configured with a GCS bucket name and file path.
        """
        if not hasattr(self, "bucket_name") or not hasattr(self, "file_path"):
            raise ValueError("Logger is not configured with GCS bucket and file path.")

        storage_client = storage.Client()
        bucket = storage_client.bucket(self.bucket_name)
        blob = bucket.blob(self.file_path)

        log_contents = self.memory_file.getvalue()
        blob.upload_from_string(log_contents)

        print(f"Uploaded log contents to {self.bucket_name}/{self.file_path}")

    def get_logger(self):
        """
        Retrieve the underlying logger instance for direct use.

        Returns:
            logging.Logger: The logger instance managed by this class.
        """
        return self.logger

    def flush_and_upload(self):
        """
        Flush in-memory logs and upload them to GCS.

        This method ensures all buffered log messages are captured and 
        sent to the configured GCS bucket and file path.
        """
        self.memory_handler.flush()
        self.upload_log_to_gcs()


    def get_gcp_bucket(
        self
    ) -> storage.Bucket:
        """
        Retrieves a Google Cloud Storage bucket object.

        Args:
            bucket_name (str): The name of the GCP bucket to retrieve.

        Returns:
            storage.Bucket: A Google Cloud Storage bucket object representing the specified bucket.
        """

        # Initialize the GCP storage client
        client = storage.Client()

        # Get the bucket
        bucket = client.bucket(self.bucket_name)

        return bucket


    def create_gcp_bucket_upload_path(
        self,
        bucket: storage.Bucket,
        bucket_folder: str,
        filename: str
    ) -> Tuple[storage.Blob, str]:
        """
        Creates a Google Cloud Storage upload path for a file in a specified bucket.

        Args:
            bucket (storage.Bucket): The Google Cloud Storage bucket object where the file will be stored.
            bucket_folder (str): The folder path within the bucket.
            filename (str): The name of the file to be uploaded.

        Returns:
            Tuple[storage.Blob, str]: 
                - `storage.Blob`: A GCP Blob object representing the file in the bucket.
                - `str`: The full path of the file within the bucket.

        Raises:
            ValueError: If any of the input arguments are invalid.
        """
        # Create the full path for the file in the bucket
        blob_path = f"{bucket_folder}/{filename}"
        blob = bucket.blob(blob_path)

        return blob, blob_path


    def upload_to_gcp(
        self,
        data: Union[pd.DataFrame, dict, str],
        filename: str,
        data_type: str = "csv",
        upload_path: str = '',
        max_retries: int = 5
    ) -> None:
        """
        Uploads a pandas DataFrame, JSON object, or plain text file to a specified Google Cloud Storage bucket.

        Args:
            data (Union[pd.DataFrame, dict, str]): The data to upload. Can be a DataFrame, JSON object, or plain text.
            filename (str): The name of the file to be uploaded (e.g., "data.csv", "data.json", "data.txt").
            data_type (str): The type of data being uploaded ("csv", "json", or "text"). Defaults to "csv".
            path (str): Path to upload on GCP. This will be the self.upload_to_gcp path by default.

        Raises:
            ValueError: If the input data is empty or invalid for the specified data_type.
            google.cloud.exceptions.GoogleCloudError: If there is an error during the upload.
        """
        for attempt in range(max_retries):
            try:
                # # Generate a random number of seconds between 1 and 5
                # sleep_time = random.randint(1, 5)

                # # Sleep for the random number of seconds
                # print(f"Sleeping for {sleep_time} seconds...")
                # time.sleep(sleep_time)
            
                # Validate input data
                if data_type == "csv" and isinstance(data, pd.DataFrame):
                    if data.empty:
                        raise ValueError("The DataFrame is empty and cannot be uploaded.")
                    # Convert DataFrame to CSV
                    buffer = io.StringIO()
                    data.to_csv(buffer, index=False)
                    buffer.seek(0)
                    content = buffer.getvalue()
                    content_type = "text/csv"

                elif data_type == "json" and isinstance(data, dict):
                    try:
                        # Convert dict to JSON string
                        content = json.dumps(data, indent=4)
                        content_type = "application/json"
                    except TypeError as e:
                        raise ValueError(f"Data is not JSON-serializable: {e}")

                elif data_type == "text" and isinstance(data, str):
                    if not data.strip():
                        raise ValueError("The text data is empty or whitespace only.")
                    # Use the plain string as content
                    content = data
                    content_type = "text/plain"

                else:
                    raise ValueError(f"Invalid data type or data does not match the expected type: {data_type}")

                # Get the bucket
                bucket = self.get_gcp_bucket()

                if upload_path == '':
                    upload_path = self.gcp_upload_path

                # Create the full path for the file in the bucket
                blob, blob_path = self.create_gcp_bucket_upload_path(bucket, upload_path, filename)

                # Upload the content to the GCP bucket
                blob.upload_from_string(content, content_type=content_type)

                # print(f"File uploaded to {self.bucket_name}/{blob_path}")

                return None

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + random.uniform(0, 3))    # Exponential backoff
                else:
                    print("Max retries reached for GCP Upload.")
                    raise


def configure_logging(id:str) -> Logger:
    """
    Configure logging for parser run.
    
    Args:
        id: Run job id for parser.
    """
    # Get current timestamp
    timestamp = datetime.now().isoformat()

    # Define log directory and file path
    log_dir = "./logging"
    os.makedirs(log_dir, exist_ok=True)  # Ensure the logging directory exists

    # Configure Logging
    LOG_FILE = f'''./logging/{id + "_" + timestamp + ".log"}''' # Change this to your preferred log file path
    logging.basicConfig(
        level=logging.INFO,  # Log all levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a'),  # Append mode
        ]
    )

    # get logger
    logger = logging.getLogger(__name__)

    return logger