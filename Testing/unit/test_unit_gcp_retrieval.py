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
# Test for gcp_retrieval
#############################

def test_gcp_retrieval(monkeypatch):
    # Override clean_html to simply strip the text
    monkeypatch.setattr("Tools.tools.clean_html", lambda html: html.strip())
    
    # Create a fake Blob class
    class FakeBlob:
        def __init__(self, name, metadata, text):
            self.name = name
            self.metadata = metadata
            self._text = text
        def download_as_text(self):
            return self._text

    # Fake blobs: one qualifies (html file with matching metadata) and one does not.
    fake_blob1 = FakeBlob(
        name="file1.html",
        metadata={"url": "http://example.com/1", "id": "1", "brand": "TestBrand"},
        text=" <html>Content 1</html> "
    )
    fake_blob2 = FakeBlob(
        name="file2.txt",
        metadata={"url": "http://example.com/2", "id": "2", "brand": "TestBrand"},
        text=" <html>Content 2</html> "
    )
    fake_blobs = [fake_blob1, fake_blob2]

    # Create fake bucket and client classes
    class FakeBucket:
        def list_blobs(self, prefix):
            return fake_blobs
    class FakeClient:
        def bucket(self, bucket_name):
            return FakeBucket()
    monkeypatch.setattr("google.cloud.storage.Client", lambda: FakeClient())
    
    # Create a fake filtered_sitemap DataFrame
    filtered_sitemap = pd.DataFrame({
        "Manufacturer Name": ["Test Manufacturer"],
        "Description": ["Test description"],
        "high_level_task": ["beef"]
    })
    
    df = gcp_retrieval("fake_bucket", "fake_folder", "id", "1", filtered_sitemap)
    
    # Only fake_blob1 qualifies; verify its values are in the DataFrame.
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["url"] == "http://example.com/1"
    # clean_html should have stripped the text
    # assert row["html"] == "<html>Content 1</html>"
    assert row["file_name"] == "file1.html"
    assert row["brand"] == "TestBrand"
    assert row["manufacturer"] == "Test Manufacturer"
    assert row["description"] == "Test description"
    assert row["high_level_task"] == "beef"
