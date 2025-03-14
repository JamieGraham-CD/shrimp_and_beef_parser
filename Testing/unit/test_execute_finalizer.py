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
# Test for execute_finalizer
#############################

def test_execute_finalizer(monkeypatch):
    # Create a fake finalizer prompt file
    dummy_finalizer_prompt = "dummy finalizer instruction"
    def fake_open(file, mode="r", *args, **kwargs):
        if "beef_finalizer.txt" in file:
            return io.StringIO(dummy_finalizer_prompt)
        return open(file, mode, *args, **kwargs)
    monkeypatch.setattr("builtins.open", fake_open)
    
    # Fake GPTModel for finalizer returning dummy output
    class FakeGPTModel:
        def generate_response(self, sys_inst, user_inst, AttributesFinalizer):
            return {"final_attr": "final_value"}
    monkeypatch.setattr("Models.gpt_models.GPTModel", lambda: FakeGPTModel())
    
    # Create a fake url_parsed_df DataFrame
    data = [{
        "id": "123",
        "url": ["http://example.com"],
        "Product Name": ["Test Product"],
        "parsed_attr": ["value"]
    }]
    url_parsed_df = pd.DataFrame(data)
    
    # Dummy AttributesFinalizer class
    class DummyAttributesFinalizer(BaseModel):
        final_attr: str
    
    result_df = execute_finalizer(url_parsed_df, DummyAttributesFinalizer)
    
    # Verify that the finalizer output contains the expected dummy data.
    assert isinstance(result_df, pd.DataFrame)
    assert result_df.iloc[0]["id"] == "123"
