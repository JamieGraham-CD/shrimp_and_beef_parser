from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict, Set
from google.cloud import storage # type: ignore
import logging
import pandas as pd # type: ignore
from logger import Logger 

class Pipeline(ABC):
    """
    The parent class for all pipeline classes in the Canteen Parser codebase.

    Attributes:
        shared_object (dict): The shared object from the previous pipeline subclass.
        scrape_df (pd.DataFrame): A DataFrame to store scraped data.
        scrape_df_post_processing (pd.DataFrame): A DataFrame to store post-processed scraped data.
        exit_flag (bool): A flag indicating whether the pipeline should terminate early.
        bucket_name (str): Name of the GCP bucket.
        client (storage.Client): GCP storage client.
        bucket (storage.Bucket): GCP bucket object.
        product (str): Product identifier.
        sku (str): SKU identifier.
        product_name (str): Name of the product.
        manufacturer (str): Manufacturer of the product.
        size_uom (str): Unit of measurement for size.
        base_path (str): Base directory path.
        prompt_path (str): Path to the prompt file.
        logger (logging.Logger): Logger instance for logging events.
        logger_handler (Optional[logging.Handler]): Optional logger handler.
        local_output_path (str): Path to local output file.
        image_to_text_model (Optional[str]): Model used for image-to-text conversion.
        gpt_model (Optional[str]): GPT model used for text processing.
        tasks (List[str]): List of tasks in the pipeline.
        fail_if_over_75_percent_undetermined (bool): Whether to fail if >75% is undetermined.
        fail_if_single_task_empty (bool): Whether to fail if a single task has no results.
        fail_if_100_percent_undetermined (bool): Whether to fail if 100% of results are undetermined.
        exit_at_semantic_check_mode (bool): Whether to exit the pipeline after semantic check.
    """
    def __init__(self, shared_object: dict):
        if not isinstance(shared_object, dict):
            raise ValueError("shared_object must be a dictionary.")
        self.shared_object = shared_object
        self.scrape_df: pd.DataFrame = pd.DataFrame()
        self.scrape_df_post_processing: pd.DataFrame = pd.DataFrame()
        self.exit_flag: bool = False

         # GCP-related attributes
        self.bucket_name: str = "data-extraction-services"
        self.client: storage.Client = storage.Client()  # GCP Storage Client
        self.bucket: storage.Bucket = self.client.get_bucket(self.bucket_name)  # GCP Storage Bucket

        # Product-related attributes
        self.product: dict = {}
        self.sku: str = ""
        self.product_name: str = ""
        self.manufacturer: str = ""
        self.size_uom: str = ""
        self.sku_product_manufacturer: str = ""
        self.sku_folder_prefix = str = ""
        
        # File and path attributes
        self.base_path: str = ""
        self.prompt_path: str = ""
        self.local_output_path: str = ""

        # Logging attributes
        self.logger: Any = None
        self.logger_handler: Any = None

        # AI Model attributes
        self.image_to_text_model: Any = None
        self.gpt_model: Any = None

        # Task-related attributes
        self.tasks: List[str] = []

        # Intermediate data structures
        self.graded_results_list: List[Any]
        self.task_dict: Dict[str,Any]
        self.populated_tasks: Set[str]
        self.structured_response_list: List[Any]
        self.structured_response: dict
        self.agent_formatter_contents: str

        # Error handling flags
        self.fail_if_over_75_percent_undetermined: bool = False
        self.fail_if_single_task_empty: bool = False
        self.fail_if_100_percent_undetermined: bool = False
        self.exit_at_semantic_check_mode: bool = False

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
    def set_global_attributes(self):
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
