from Workflow.google_storage_workflow import read_csv_from_gcs
import pandas as pd
from typing import List, Dict, Tuple
from google.cloud import storage
from google.cloud.storage.blob import Blob
from Tools.tools import clean_html, count_tokens
from Workflow.structured_outputs import BeefAttributes, BeefAttributesFinalizer, ShrimpAttributes, ShrimpAttributesFinalizer
from Models.gpt_models import GPTModel
from pydantic import BaseModel
from utils import store_secret
import pprint



def set_configurations(item_id:str, high_level_task:str) -> Tuple[pd.DataFrame, str, pd.DataFrame]:
    """ 
        Set configurations for pipeline. 

    Args:
        item_id (str): Item ID.
        high_level_task (str): High level task.
    Returns:
        Tuple[pd.DataFrame, str]: Tuple containing the sitemap dataframe and the high level task.
    """

    # 0. Extract and store secrets 
    store_secret(secret_name="des-wesel",project_id="cd-ds-384118")

    # Get Sitemap 
    sitemap_df = pd.DataFrame(read_csv_from_gcs(f"rcc-attribution/sitemap/{high_level_task}_sitemap.csv"))

    # Filter Sitemap
    filtered_sitemap = sitemap_df[sitemap_df['Mfr Item Code'] == item_id].copy().reset_index(drop=True)

    # Add high level task to sitemap
    filtered_sitemap.loc[0,'high_level_task'] = high_level_task

    return filtered_sitemap, item_id, sitemap_df


def gcp_retrieval(
        bucket_name: str,
        folder_path: str, 
        metadata_key: str, 
        metadata_value: str,
        filtered_sitemap: str
    ) -> Dict:
    """
    Fetches all blobs from a specified GCS bucket folder and filters them based on metadata.

    Parameters:
        bucket_name (str): The name of the GCS bucket.
        folder_path (str): The folder path within the bucket (e.g., "data/subfolder/").
        metadata_key (str): The metadata key to check.
        metadata_value (str): The expected value for the metadata key.

    Returns:
        List[Blob]: A list of blob objects that match the given metadata condition.
    """

    # Initialize GCS client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # List all blobs in the given folder
    blobs = bucket.list_blobs(prefix=folder_path)

    # Filter blobs based on metadata
    results_dict = {}
    for blob in blobs:
        metadata = blob.metadata or {}

        if metadata.get(metadata_key) == metadata_value:

            if blob.name.endswith(".html"):
                    # Read and store HTML file content
                    html_data = clean_html(blob.download_as_text())
                    results_dict[blob.metadata['url']] = {"file_name": blob.name, "html": html_data, "metadata": blob.metadata}

    # Construct DataFrame from results_dict with improved readability
    scrape_df = pd.DataFrame([
        {
            "url": k,
            "html": v.get("html"),
            "file_name": v.get("file_name"),
            "brand": v["metadata"]["brand"],
            "id": v["metadata"]["id"],
            "manufacturer": filtered_sitemap["Manufacturer Name"].values[0],
            "description": filtered_sitemap["Description"].values[0],
            "high_level_task": filtered_sitemap["high_level_task"].values[0]
        }
        for k, v in results_dict.items()
    ])

    return scrape_df



def execute_parser(scrape_df:pd.DataFrame, Attributes:BaseModel) -> pd.DataFrame:
    """ 
    Execute the parser on the scraped data and return structured outputs.

    Args:
        scrape_df (pd.DataFrame): The scraped data.
    Returns:
        pd.DataFrame: The structured outputs.
    """
    model = GPTModel()

    # Get high level task
    high_level_task = str(scrape_df['high_level_task'].values[0])

    # Read parser prompt
    with open(f"Prompts/{high_level_task}_parser.txt", "r") as file:
        sys_inst = file.read()

    structured_outputs = []
    for idx, row in scrape_df.iterrows():

        user_inst = f'''<HTML>
            Product: {row['description']}
            Manufacturer: {row['manufacturer']}
        </HTML>'''
        user_inst += f'''<HTML>
            {row['html']}
        </HTML>'''
        
        url = row['url']
        output = model.generate_response(sys_inst, user_inst, Attributes)
        output = {
            "url": url,
            "id": row['id'],
            "Product Name": row['description'],
            **output  # Append the remaining original dictionary contents
        }
        structured_outputs.append(output)

    url_parsed_df = pd.DataFrame(structured_outputs)

    return url_parsed_df


def execute_finalizer(url_parsed_df:pd.DataFrame, AttributesFinalizer:BaseModel) -> pd.DataFrame:
    """ 
    Execute the finalizer on the parsed data

    Args:
        url_parsed_df (pd.DataFrame): The parsed data
    Returns:
        pd.DataFrame: The finalizer output
    """
    model = GPTModel()
    
    # Read finalizer Prompt
    with open("Prompts/beef_finalizer.txt", "r") as file:
        sys_inst = file.read()

    finalizer_user_input = str(url_parsed_df.to_dict(orient='records')) 

    output = model.generate_response(sys_inst, finalizer_user_input, AttributesFinalizer)
    output = {
        "id": url_parsed_df['id'].values[0],
        **output  # Append the remaining original dictionary contents
    }

    # to csv
    output_df = pd.DataFrame([output])

    return output_df


def execute_pipeline(**kwargs) -> dict:
    """
    Execute the entire pipeline.

    Args:
        **kwargs: Arbitrary keyword arguments.
    Returns:
        pd.DataFrame: The final output.
    """

    # Unpack all expected parameters from kwargs
    item_id = kwargs.get("item_id")
    high_level_task = kwargs.get("high_level_task")
    bucket_name = kwargs.get("bucket_name")
    folder_path = kwargs.get("folder_path")
    metadata_key = kwargs.get("metadata_key")
    metadata_value = kwargs.get("metadata_value")
    structured_output_parser = kwargs.get("structured_output_parser")
    structured_output_finalizer = kwargs.get("structured_output_finalizer")

    # Set configurations
    filtered_sitemap, item_id, sitemap_df = set_configurations(item_id, high_level_task)

    # Retrieve data from GCS
    scrape_df = gcp_retrieval(bucket_name, folder_path, metadata_key, metadata_value, filtered_sitemap)

    # Execute parser
    url_parsed_df = execute_parser(scrape_df, structured_output_parser)

    # Execute finalizer
    output_df = execute_finalizer(url_parsed_df, structured_output_finalizer)

    output_dict = {
        "output_df": output_df,
        "sitemap_df": sitemap_df
    }

    return output_dict

def get_all_ids(
        bucket_name: str,
        folder_path: str
    ) -> Dict:
    """
    Fetches all blobs from a specified GCS bucket folder and filters them based on metadata.

    Parameters:
        bucket_name (str): The name of the GCS bucket.
        folder_path (str): The folder path within the bucket (e.g., "data/subfolder/").

    Returns:
        Set: A set of all ids.
    """

    # Initialize GCS client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # List all blobs in the given folder
    blobs = bucket.list_blobs(prefix=folder_path)

    # Filter blobs based on metadata
    results_dict = set()
    for blob in blobs:
        if blob.metadata is not None:
            results_dict.add(blob.metadata.get('id'))
    
    return results_dict