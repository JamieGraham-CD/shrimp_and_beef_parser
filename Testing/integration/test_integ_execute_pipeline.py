import io
import logging
import pandas as pd
import pytest
from pydantic import BaseModel
from Workflow.structured_outputs import BeefAttributes, BeefAttributesFinalizer

# Import the functions from your module (assumed module name is "pipeline")
from Pipeline.master_pipeline_module import *
from utils import store_secret 
from main import main
import os

# 0. Extract and store secrets 
store_secret(secret_name="des-wesel",project_id="cd-ds-384118")
#############################
# Test for execute_pipeline
#############################

def test_execute_pipeline():
    
    # Define input parameters
    high_level_task = 'beef'
    bucket_name = "data-extraction-services"
    folder_path = f"rcc-attribution/{high_level_task}v2/"  # Ensure this ends with '/'
    metadata_key = "id"

    # Set structured output parser and finalizer based on high level task
    if high_level_task == 'shrimp':
        structured_output_parser = ShrimpAttributes
        structured_output_finalizer = ShrimpAttributesFinalizer
    elif high_level_task == 'beef':
        structured_output_parser = BeefAttributes
        structured_output_finalizer = BeefAttributesFinalizer  
    
    # Get all item ids
    item_id_list = list(get_all_ids(bucket_name, folder_path))

    logger = logging.getLogger(__name__)
    # Execute pipeline iteratively over items
    df_list = []
    idx = 1
    item_id = item_id_list[idx]

    try:
        logger.info(f"Processing item {item_id}, index {idx}...")
        
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

    except Exception as e:
        print('exception at idx: ', str(idx))
        

    # Create master dataframe
    output_df = pd.DataFrame(df_list)

    # Save output to CSV
    output_df.to_csv(f"Testing/integration/test_output/{high_level_task}_example.csv")
    
    # Verify that the CSV file exists and that the output DataFrame has exactly one record
    assert os.path.exists(f"Testing/integration/test_output/{high_level_task}_example.csv")
    assert len(output_df) == 1
