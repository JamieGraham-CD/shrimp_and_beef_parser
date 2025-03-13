from google.cloud import storage # type: ignore
from typing import Optional, List, Dict, Set, Iterator
import io
from google.cloud.storage.blob import Blob # type: ignore
from io import StringIO
import csv
from abc import ABC, abstractmethod
from Pipeline.pipeline import Pipeline

class GCPRetrieval(Pipeline):
    """
    A universal class to support retrieval for LLM parsing workflows. Supports data extraction from Google Cloud Storage.
    """
    
    def __init__(self, input_object: dict):
        """
        Initializes the Retrieval class with project credentials.

        Args:
            input_object (dict): The input object to the class. 
            output_object (dict): The output object for the class.
            bucket_name (str): The GCP bucket name for retrieval. 
        """
        self.bucket_name = input_object['bucket_name']

        # Initialize clients for GCP services
        self.client = storage.Client()
        self.bucket = self.client.get_bucket(self.bucket_name)

        if not isinstance(input_object, dict):
            raise ValueError("input_object must be a dictionary.")
        self.input_object = input_object
        self.output_object = None

    def get_blobs_from_folder(self, folder_path: str) -> Iterator[Blob]:
        """
        Retrieves the collection of blobs from a specific folder in the GCP bucket.

        Args:
            folder_path (str): The path to the folder in the bucket.

        Returns:
            Set[Blob]: A set of Blob objects within the specified folder.
        """
        if not folder_path.endswith("/"):
            folder_path += "/"

        blobs = self.bucket.list_blobs(prefix=folder_path, delimiter="/")
        return blobs  # Convert the iterator to a collection of Blob objects
    
    def get_subfolder_paths(
            self,
            input_path: str
        ) -> List[str]:
            """
            Lists nested folder paths within a specified input path in a GCP bucket.

            Constructs a folder prefix based on the provided SKU, manufacturer, and product name,
            and lists all folder paths matching the prefix within the specified base path.

            Args:
                input_path (str): The base path to search for nested folders.

            Returns:
                List[str]: A list of subfolder paths that match the specified prefix.

            Example:
                If called as:
                    list_nested_folder_paths(input_path)

                This will return:
                    ["<input_path>/subfolder1","<input_path>/subfolder2", ...]
            """

            # Add a trailing slash to ensure it's recognized as a "folder" prefix
            input_path += "/"

            # List all blobs that match the folder prefix
            blobs = self.bucket.list_blobs(prefix=input_path, delimiter="/")
            # Collect paths of the folders
            folder_paths = []
            for page in blobs.pages:
                folder_paths.extend(page.prefixes)  # Only add prefixes, representing folder paths

            return folder_paths
    
    def get_blob_data(
            self,
            folder_path: str
        ) -> dict:
            """
            Accepts a folder path as input, and returns the data within files in the folder (html, png, txt) in a dictionary of dictionaries.

            Args:
                folder_path (str): The folder path to search for data.

            Returns:
                output_dict (dict): A dictionary of dictionaries with keys as file names and values as a dictionary of extracted data. 

            """
            output_dict: dict = {}
            blobs = self.get_blobs_from_folder(folder_path)
            for blob in blobs:
                
                file_name = blob.name
                if file_name == folder_path:
                    continue
                
                if blob.metadata is None:
                     continue
                else:
                    blob_metadata = blob.metadata
                    blob_url = blob_metadata['url']

                if blob_url not in output_dict.keys():
                     output_dict[blob_url] = {}

                if file_name.endswith(".html"):
                    # Read and store HTML file content
                    html_data = blob.download_as_text()
                    output_dict[blob_url].update({"file_name": file_name, "html": html_data, "metadata": blob_metadata})

                elif file_name.endswith("product_image.png"):
                    # Read and convert PNG file content to a Pillow Image object                    
                    image_data = blob.download_as_bytes()  # Download image data as bytes
                    byte_image = io.BytesIO(image_data)
                    output_dict[blob_url].update({"file_name": file_name, "product_image": byte_image, "metadata": blob_metadata})

                elif file_name.endswith(".png") and "product_image" not in file_name:
                    # Read and convert PNG file content to a Pillow Image object
                    image_data = blob.download_as_bytes()  # Download image data as bytes
                    byte_image = io.BytesIO(image_data)
                    output_dict[blob_url].update({"file_name": file_name, "image": byte_image, "metadata": blob_metadata})

                elif file_name.endswith(".txt"):
                    txt_data = blob.download_as_text()
                    output_dict[blob_url].update({"file_name": file_name, "txt": txt_data, "metadata": blob_metadata})

            return output_dict
    

    def read_csv_from_gcs(self, folder: str) -> List:
        """
            Downloads csv from folder in GCS

            Args:
                folder (str): The base path to search for csv, from bucket as root.

            Returns:
                List[str]: A csv in a list.
        """
        
        bucket_name = self.bucket_name
        destination_blob_path = folder
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_path)

        # Download the file as bytes and decode it into a string
        content = blob.download_as_text()

        # Use io.StringIO to read the CSV data
        csv_reader = csv.DictReader(StringIO(content))
        data = [row for row in csv_reader]
        return data
    
    @abstractmethod
    def process(self) -> None:
        """
        Processes the data in a way specific to the subclass's use case.
        """
        pass

    @abstractmethod
    def save_results(self) -> None:
        """
        Saves the processed data based on the provided options.
        """
        pass

    @abstractmethod
    def set_global_attributes(self) -> dict:
        """
        Sets the output object for the next pipeline subclass.

        Returns:
            dict: The output object.
        """
        pass

    def run(self) -> None:
        """
        Runs the pipeline by processing the input, saving results, and setting the output object.
        """
        self.process()
        self.save_results()
        self.set_global_attributes()
