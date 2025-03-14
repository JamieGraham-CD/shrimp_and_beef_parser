import io
import logging
import pandas as pd
import pytest
from pydantic import BaseModel
from Workflow.structured_outputs import BeefAttributes, BeefAttributesFinalizer

# Import the functions from your module (assumed module name is "pipeline")
from Pipeline.master_pipeline_module import *

#############################
# Test for set_configurations
#############################

def test_set_configurations(monkeypatch):
    # Override store_secret to do nothing
    monkeypatch.setattr("utils.store_secret", lambda secret_name, project_id: None)
    
    # Fake CSV data to be returned by read_csv_from_gcs
    fake_csv_data = [
        {
            "Mfr Item Code": "item123",
            "Manufacturer Name": "Test Manufacturer",
            "Description": "Test description"
        }
    ]
    monkeypatch.setattr("Workflow.google_storage_workflow.read_csv_from_gcs", lambda path: fake_csv_data)
    
    filtered_sitemap, item_id, sitemap_df = set_configurations("item123", "beef")
    
    # Check that the filtered sitemap was correctly filtered and updated
    assert not filtered_sitemap.empty
    assert filtered_sitemap.iloc[0]["high_level_task"] == "beef"
    assert item_id == "item123"
    # sitemap_df should be a DataFrame built from fake_csv_data
    assert isinstance(sitemap_df, pd.DataFrame)
