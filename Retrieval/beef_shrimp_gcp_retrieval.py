from google.cloud import storage # type: ignore
from typing import Optional, List, Dict, Union
import io
from Retrieval.gcp_retrieval import GCPRetrieval
import pandas as pd # type: ignore
from Tools.tools import clean_html
from abc import ABC, abstractmethod
import time
from Pipeline.pipeline import Pipeline

class BeefShrimpGCPRetrieval(GCPRetrieval):
    """
    A class for the Canteen Scanner Project to support retrieval and extract data from Google Cloud Platform (GCP).

    Args:
        bucket_name (str): The name of the GCP bucket to pull from.
    """
    
    def __init__(self, input_object:dict):
        """
        Initializes the Retriever with project credentials.

        Args:
            input_object (dict): dictionary of inputs for SKU retrieval.
            output_object (dict): output dictionary. 
        """

        if not isinstance(input_object, dict):
            raise ValueError("input_object must be a dictionary.")
        self.input_object = input_object
        # self.output_object = None
        
        # # Initialize global parent attributes
        # Pipeline.bucket_name = input_object["bucket_name"]
        # Pipeline.client = storage.Client()
        # Pipeline.bucket = Pipeline.client.get_bucket(input_object["bucket_name"])
        # Pipeline.product = input_object["product"]
        # Pipeline.sku = input_object["product"]['SKU']
        # Pipeline.product_name = input_object["product"]['Product Name']
        # Pipeline.manufacturer = input_object["product"]['Manufacturer']
        # Pipeline.size_uom = input_object["product"]['Size UOM']
        # Pipeline.base_path = input_object["base_path"]
        # Pipeline.prompt_path = input_object["prompt_path"]
        # Pipeline.logger = input_object["logger"]
        # Pipeline.logger_handler = input_object["logger_handler"]
        # Pipeline.local_output_path = input_object["local_output_path"]
        # Pipeline.exit_flag = False
        # Pipeline.image_to_text_model = input_object["image_to_text_model"]
        # Pipeline.gpt_model = input_object["gpt_model"]
        # Pipeline.tasks = input_object["tasks"]
        # Pipeline.fail_if_over_75_percent_undetermined = False
        # Pipeline.fail_if_single_task_empty = False
        # Pipeline.fail_if_100_percent_undetermined = True
        # Pipeline.exit_at_semantic_check_mode = False
        # Pipeline.sku_product_manufacturer = input_object['sku_product_manufacturer']
        # Pipeline.sku_folder_prefix = ''


    def get_sku_folder(self) -> str:
        """
        Constructs a folder path based on the provided SKU, self.manufacturer, and product name,
        and lists all folder paths matching the prefix within the specified base path.

        Args:
            base_path (str): The base path to search for nested folders.

        Returns:
            folder_prefix (str): A string folder path that matches the specified prefix.

        Example:
            Given the following folder structure:
            - /bucket/data/123-ABC-ProductA/
            - /bucket/data/456-DEF-ProductB/

            If called as:
                list_nested_folder_paths("/bucket/data")

            This will return:
                "/bucket/data/123-ABC-ProductA"
        """
        # Define the complete folder prefix within the base path
        if self.sku and self.manufacturer and self.product_name:
            folder_prefix = f"/{self.sku}-{self.manufacturer}-{self.product_name}".replace(" ", "-").replace("(", "").replace(")", "").replace("/", "")
            folder_prefix = self.base_path + "/" + folder_prefix
            Pipeline.sku_folder_prefix = folder_prefix
        else:
            folder_prefix = f"{self.base_path}"

        return folder_prefix

    def get_nested_sku_dictionary(self) -> Dict:
        """
        Builds a nested dictionary containing Canteen Scanner SKU data organized into tiers.

        This method retrieves tiered SKU data from a structured folder system and organizes
        the extracted data into a dictionary with two main keys: "tier_one" and "tier_two".

        Returns:
            dict: A nested dictionary with the following structure:
                - "tier_one" (dict): Contains a dictionary of extracted data for the first tier.
                - "tier_two" (dict): Contains a dictionary of extracted data for the second tier.
                
                Each tier contains nested dictionaries of data with the following key-value pairs:

                - Key: file_name from GCP 
                - Value: Dictionary with the following fields:
                    - "url" (str): The website url
                    - "tier" (str): The tier of the data ("tier_one" or "tier_two").
                    - "metadata" (dict): Metadata associated with the file.
                    - "sitehtml" (any): The extracted html data.
                    - "apidata" (str): The extracted api data
                    - "image" (any): The extracted iamge data
                    - "file_name" (str): File name on GCP
        """
        # Define paths for tier folders
        sku_folder = self.get_sku_folder()

        # Get Tier 1 and 2 folders
        tier_paths = self.get_subfolder_paths(sku_folder)


        # Initialize the main data structure
        output_data: dict = {
            "tier_one": {},
            "tier_two": {}
        }

        for path in tier_paths:
            extracted_data = self.get_blob_data(path)

            if extracted_data == {}:
                continue

            if "tier_one" in path:
                tier = "tier_one"
            elif "tier_two" in path:
                tier = "tier_two"
            else:
                continue  # Skip if the path is not part of tier_one or tier_two

            for url in extracted_data:
                extracted_data[url]["tier"] = tier
                extracted_data[url]["sitehtml"] = extracted_data[url].get("html","") 
                extracted_data[url]["apidata"] = extracted_data[url].get("txt","") 
                extracted_data[url]["image"] = extracted_data[url].get("image","") 
                extracted_data[url].pop("html") if "html" in extracted_data[url] else None
                extracted_data[url].pop("txt") if "txt" in extracted_data[url] else None

            output_data[tier] = extracted_data

        return output_data


    def get_flattened_url_df(self) -> pd.DataFrame:
        """
        Builds a DataFrame containing URLs and their associated data by flattening the tiered SKU data from the GCP nested SKU dictionary.

        This method retrieves tiered SKU data, processes URLs into tiers, and extracts
        relevant data (HTML, PNG, API data) for each URL, organizing it into a DataFrame.

        Returns:
            pd.DataFrame: A DataFrame with the following columns:
                - "url" (str): The URL associated with the SKU.
                - "scraped_html" (str): Cleaned HTML content or an error message.
                - "scraped_png" (any): PNG image data or an error message.
                - "scraped_api" (str, optional): Cleaned API data or an error message (only for Tier 1).
                - "tier" (str): The tier of the data ("Tier_1" or "Tier_2").
                - "product_name" (str): The product name associated with the SKU.
                - "product_manufacturer" (str): The manufacturer of the product.
                - "size_uom" (str): The size and unit of measure for the product.

        Raises:
            KeyError: If a URL key is missing in the nested SKU dictionary.
            Exception: For unexpected errors during data processing.
        """
        nested_sku_dictionary = self.get_nested_sku_dictionary()

        # Extract URLs from tiered data
        tier_1_urls = set(nested_sku_dictionary['tier_one'].keys())
        tier_2_urls = set(nested_sku_dictionary['tier_two'].keys())

        # Create dictionary with URLs as keys and tiers as values
        url_tier_dict = {url: "tier_one" for url in tier_1_urls}
        url_tier_dict.update({url: "tier_two" for url in tier_2_urls})


        # List to hold processed URL data
        url_df_list = []
        for url in url_tier_dict:
            tmp_url_dict = {}
            url_tier = url_tier_dict[url]

            tmp_url_dict["url"] = url
            
            # Process HTML data
            tmp_url_dict["scraped_html"] = clean_html(str(nested_sku_dictionary[url_tier][url]["sitehtml"])) if "sitehtml" in nested_sku_dictionary[url_tier][url] else 'No HTML'

            # Process PNG data
            tmp_url_dict["scraped_png"] = nested_sku_dictionary[url_tier][url]["image"] if "image" in nested_sku_dictionary[url_tier][url] else 'No Image'

            # Process API data for Tier 1
            if url_tier == "tier_one":
                tmp_url_dict["scraped_api"] = clean_html(str(nested_sku_dictionary[url_tier][url]["apidata"])) if "apidata" in nested_sku_dictionary[url_tier][url] else 'No API'
                tmp_url_dict["tier"] = "Tier_1"
            else: 
                tmp_url_dict["tier"] = "Tier_2"

            url_df_list.append(tmp_url_dict)

        # Create a DataFrame from the list of dictionaries
        df_output = pd.DataFrame(url_df_list)

        # Add product-specific columns
        total_records = len(df_output)
        df_output['product_name'] = [self.product_name] * total_records
        df_output['product_manufacturer'] = [self.manufacturer] * total_records
        df_output['size_uom'] = [self.size_uom] * total_records

        self.scrape_df = df_output

        return df_output

    def process(self) -> None:
        """
        Orchestrates the internal flow of the canteen GCP retrieval class, which outputs a flattened dataframe retrieving URL specific information for a product.
        """
        self.get_flattened_url_df()
        pass


    def save_results(self) -> None:
        """
        Saves the processed data based on the provided options.
        """
        if self.scrape_df.empty:
            self.logger.error("scrape_df empty after canteen gcp retrieval")
            self.exit_flag = True
        else:
            self.logger_handler.upload_to_gcp(self.scrape_df,f'''{self.sku}_retrieval_pre_parsing.csv''',"csv")
            self.scrape_df.to_csv(self.local_output_path.replace('.json','_retrieval_pre_parsing.csv'))
        pass

    def set_global_attributes(self):
        """
        Sets the global Pipeline attributes to be inherited by next pipeline subclass.

        Returns:
            None
        """
        Pipeline.scrape_df = self.scrape_df
        Pipeline.exit_flag = self.exit_flag

        pass

    def run(self) -> None:
        """
        Runs the pipeline by processing the input, saving results, and setting the output object.
        """
        # Start clock for profiling
        start_time = time.time()

        # Run process method
        self.process()
        
        # Run save results method
        self.save_results()
        
        # Run set shared state attributes method
        self.set_global_attributes()
        
        # End clock for profiling
        end_time = time.time()
        
        # Calculate elapsed time and log
        execution_time = end_time - start_time
        self.logger.info(f"Retrieval execution time: {execution_time:.2f} seconds")