from Workflow.google_storage_workflow import read_csv_from_gcs
import pandas as pd
from typing import List, Dict
from google.cloud import storage
from google.cloud.storage.blob import Blob
from Tools.tools import clean_html
from Workflow.structured_outputs import BeefAttributes, BeefAttributesFinalizer, ShrimpAttributes, ShrimpAttributesFinalizer
from Models.gpt_models import GPTModel
from pydantic import BaseModel
from utils import store_secret
from Pipeline.master_pipeline_module import get_all_ids, execute_pipeline


def main(
        high_level_task: str,
        bucket_name: str,
        folder_path: str,
        metadata_key: str,
        structured_output_parser: BaseModel,
        structured_output_finalizer: BaseModel
    ) -> None:
    """ 
        Main function to execute the pipeline.
    
    Args:
        high_level_task (str): High level task.
        bucket_name (str): Name of the GCP bucket.
        folder_path (str): Folder path within the bucket.
        metadata_key (str): Metadata key to filter on.
        structured_output_parser (BaseModel): Structured output parser.
        structured_output_finalizer (BaseModel): Structured output finalizer.
    Returns:
        None
    """

    # Get all item ids
    item_id_list = list(get_all_ids(bucket_name, folder_path))

    # Execute pipeline iteratively over items
    df_list = []
    for idx, item_id in enumerate(item_id_list):
        try:
            if (idx > 1000):
                continue 
            
            print(idx)
            
            input_dict = {
                "item_id": item_id,
                "high_level_task": high_level_task,
                "bucket_name": bucket_name,
                "folder_path": folder_path,
                "metadata_key": metadata_key,
                "metadata_value": item_id,
                "structured_output_parser": structured_output_parser,
                "structured_output_finalizer": structured_output_finalizer
            }

            output_dict = execute_pipeline(**input_dict)

            tmp_output_df = output_dict.get("output_df")
            df_list.append(tmp_output_df.to_dict(orient='records')[0])

            # Save output to CSV
            tmp_df = pd.DataFrame(df_list)
            tmp_df.to_csv(f"{high_level_task}_example.csv")
        except Exception as e:
            print('exception at idx: ', str(idx))
            continue

    # Create master dataframe
    output_df = pd.DataFrame(df_list)

    # Save output to CSV
    output_df.to_csv(f"{high_level_task}_example.csv")


if __name__ == "__main__":

    high_level_task = 'beef'
    bucket_name = "data-extraction-services"
    folder_path = f"rcc-attribution/{high_level_task}v2/"  # Ensure this ends with '/'
    metadata_key = "id"

    if high_level_task == 'shrimp':
        structured_output_parser = ShrimpAttributes
        structured_output_finalizer = ShrimpAttributesFinalizer
    elif high_level_task == 'beef':
        structured_output_parser = BeefAttributes
        structured_output_finalizer = BeefAttributesFinalizer  
    
    main(
        high_level_task=high_level_task,
        bucket_name=bucket_name,
        folder_path=folder_path,
        metadata_key=metadata_key,
        structured_output_parser=structured_output_parser,
        structured_output_finalizer=structured_output_finalizer
    )