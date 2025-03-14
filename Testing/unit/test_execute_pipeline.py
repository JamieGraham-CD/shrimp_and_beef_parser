import io
import logging
import pandas as pd
import pytest
from pydantic import BaseModel
from Workflow.structured_outputs import BeefAttributes, BeefAttributesFinalizer

# Import the functions from your module (assumed module name is "pipeline")
from Pipeline.master_pipeline_module import *
from utils import store_secret 

# 0. Extract and store secrets 
store_secret(secret_name="des-wesel",project_id="cd-ds-384118")
#############################
# Test for execute_pipeline
#############################

def test_execute_pipeline(monkeypatch):
    # Override set_configurations to return dummy values.
    def fake_set_configurations(item_id, high_level_task, logger=None):
        filtered_sitemap = pd.DataFrame({
            "Manufacturer Name": ["Dummy Manufacturer"],
            "Description": ["Dummy Description"],
            "high_level_task": [high_level_task]
        })
        sitemap_df = filtered_sitemap.copy()
        return filtered_sitemap, item_id, sitemap_df
    monkeypatch.setattr("Pipeline.master_pipeline_module.set_configurations", fake_set_configurations)
    
    # Override gcp_retrieval to return a dummy scrape DataFrame.
    def fake_gcp_retrieval(bucket_name, folder_path, metadata_key, metadata_value, filtered_sitemap, logger=None):
        data = {
            "high_level_task": [ "beef" ],
            "description": [ "Dummy Product" ],
            "manufacturer": [ "Dummy Manufacturer" ],
            "html": [ "<html>Dummy</html>" ],
            "url": [ "http://dummy.com" ],
            "id": [ "dummy123" ]
        }
        return pd.DataFrame(data)
    monkeypatch.setattr("Pipeline.master_pipeline_module.gcp_retrieval", fake_gcp_retrieval)
    
    # Override execute_parser to return a dummy parsed DataFrame.
    def fake_execute_parser(scrape_df, Attributes, logger=None):
        data = {
            "url": [ "http://dummy.com" ],
            "id": [ "dummy123" ],
            "Product Name": [ "Dummy Product" ],
            "parsed_attr": [ "dummy_parsed" ]
        }
        return pd.DataFrame(data)
    monkeypatch.setattr("Pipeline.master_pipeline_module.execute_parser", fake_execute_parser)
    
    # Override execute_finalizer to return a dummy finalizer DataFrame.
    def fake_execute_finalizer(url_parsed_df, AttributesFinalizer, logger=None):
        data = {
            "id": [ "dummy123" ],
            "final_attr": [ "dummy_final" ]
        }
        return pd.DataFrame(data)
    monkeypatch.setattr("Pipeline.master_pipeline_module.execute_finalizer", fake_execute_finalizer)
    
    # Prepare dummy kwargs for execute_pipeline
    kwargs = {
        "item_id": "dummy123",
        "high_level_task": "beef",
        "bucket_name": "dummy_bucket",
        "folder_path": "dummy_folder",
        "metadata_key": "dummy_key",
        "metadata_value": "dummy_value",
        "structured_output_parser": BaseModel,
        "structured_output_finalizer": BaseModel
    }
    
    result = execute_pipeline(**kwargs)
    
    # Verify that execute_pipeline returns the expected dictionary structure.
    assert "output_df" in result
    assert "sitemap_df" in result
    assert isinstance(result["output_df"], pd.DataFrame)
    assert isinstance(result["sitemap_df"], pd.DataFrame)
