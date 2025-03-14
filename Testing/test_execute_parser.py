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
# Test for execute_parser
#############################

def test_execute_parser(monkeypatch):

    # Create a fake GPTModel that returns dummy parsed output
    class FakeGPTModel:
        def generate_response(self, sys_inst, user_inst, Attributes):
            return {"hello": "value"}
    monkeypatch.setattr("Models.gpt_models.GPTModel", lambda: FakeGPTModel())
    
    # Prepare a fake scrape_df DataFrame with necessary columns
    data = [{
        "high_level_task": "beef",
        "description": "Test Product",
        "manufacturer": "Test Manufacturer",
        "html": "<html>Test</html>",
        "url": "http://example.com",
        "id": "123"
    }]
    scrape_df = pd.DataFrame(data)
    
    result_df = execute_parser(scrape_df, BeefAttributes)
    
    # Verify that the returned DataFrame contains the expected dummy data.
    assert isinstance(result_df, pd.DataFrame)
    assert result_df.loc[0,"url"] == "http://example.com"
    assert result_df.loc[0,"id"] == "123"
    assert result_df.loc[0,"Product Name"] == "Test Product"
