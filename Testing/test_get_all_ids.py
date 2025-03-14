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
# Test for get_all_ids
#############################

def test_get_all_ids(monkeypatch):
    # Create a fake Blob class for testing get_all_ids
    class FakeBlob:
        def __init__(self, metadata):
            self.metadata = metadata
    
    fake_blob1 = FakeBlob(metadata={"id": "1"})
    fake_blob2 = FakeBlob(metadata={"id": "2"})
    fake_blob3 = FakeBlob(metadata={"id": "3"})
    fake_blob4 = FakeBlob(metadata=None)  # Should be ignored
    fake_blobs = [fake_blob1, fake_blob2, fake_blob3, fake_blob4]
    
    # Create fake bucket and client classes
    class FakeBucket:
        def list_blobs(self, prefix):
            return fake_blobs
    class FakeClient:
        def bucket(self, bucket_name):
            return FakeBucket()
    monkeypatch.setattr("google.cloud.storage.Client", lambda: FakeClient())
    
    result = get_all_ids("dummy_bucket", "dummy_folder")
    
    # Expected set should only contain the ids from blobs with metadata.
    assert isinstance(result, set)
    assert result == {"1", "2", "3"}
