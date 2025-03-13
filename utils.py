import json
import re
import pandas as pd # type: ignore
# from unit_convert import UnitConvert # type: ignore
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
from google.cloud import storage # type: ignore
from Workflow.google_storage_workflow import read_csv_from_gcs
from google.cloud import secretmanager # type: ignore
import os

def extract_json_from_string(text: str):
    """Extracts first JSON object present from a string of text if present, else returns None"""
    # Look for the largest { ... } in text
    match = re.search(r"\{(.*)\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed_response = json.loads(match.group())
        return parsed_response
    except Exception as e:
        return None
    
    
def sanitize_filename(filename: str):
    """Removes any special characters that won't work in filenames and replaces them with underscores"""
    return "".join(
        c if c.isalnum() or c in {" ", ".", "-", "_"} else "_" for c in filename
    )

def convert_volume_to_oz(volume_quantity, volume_unit):
    """
    Convert volume to ounces directly based on the volume unit.

    Args:
    - volume_quantity (float): The volume value to convert.
    - volume_unit (str): The unit of the volume (e.g., "ml", "l", "fl oz").

    Returns:
    - float: The equivalent volume in ounces.
    """
    # Conversion factors for volume to ounces (direct conversion)
    volume_to_oz = {
        'ml': 0.033814,   
        'l': 33.814,     
        'gal': 128.0  
    }

    # Check if the provided volume unit exists in our dictionary
    if volume_unit.lower() in volume_to_oz:
        return volume_quantity * volume_to_oz[volume_unit.lower()]
    else:
        raise ValueError(f"Unsupported volume unit: {volume_unit}")

# Updated extract_quantity_and_unit function
def extract_quantity_and_unit(size_str):
    """
    Extract quantity and unit from a given string.
    
    Args:
    - size_str (str): The input string containing size information.
    
    Returns:
    - tuple: (quantity, unit) or (None, None) if no match is found.
    """
    # Updated regex pattern
    pattern = r'(\d*?\.?\d+)\s*(oz|lb|l|ml|mg|gal|g|fl.*oz|ounce|millilitre|gram|fluidOunceUS|pound)'
    
    # Perform the regex search on the input string
    match = re.search(pattern, size_str, re.IGNORECASE)
    
    if match:
        quantity = float(match.group(1))  # Extract the quantity
        unit = match.group(2).lower()  # Extract the unit and convert to lowercase
        unit = unit.replace('lb', 'lbs')
        unit = unit.replace('ounce', 'oz')
        unit = unit.replace('millilitre', 'ml')
        unit = unit.replace('gram', 'g')
        unit = unit.replace('fluidOunceUS', 'oz')
        unit = unit.replace('pound', 'lbs')
        if 'oz' in unit:
            unit = 'oz' 
        return quantity, unit
    return None, None

def is_serving_size_match(product_name, serving_size, margin_of_error=0.2):
    """
    Check if the serving size matches the product quantity and unit in the product name.
    
    Args:
    - product_name (str): The product name containing the size information.
    - serving_size (str): The serving size string to match against.
    - margin_of_error (float): The acceptable margin of error in the comparison (in oz).
    
    Returns:
    - bool: True if the serving size matches the product size, False otherwise.
    """
    # Check if serving size is NaN
    if pd.isna(serving_size):
        return False

    # Extract quantity and unit from serving size
    serving_quantity, serving_unit = extract_quantity_and_unit(serving_size)

    # If no unit is found in the product name, return True
    if not serving_unit:
        return False

    # Extract quantity and unit from product name
    product_quantity, product_unit = extract_quantity_and_unit(product_name)

    # If any of the quantities or units are missing, return False
    if not product_quantity or not serving_quantity or not product_unit or not serving_unit:
        return True

    # If the unit is a volume (e.g., ml, l, fl oz), convert it to ounces
    if product_unit in ['ml', 'l', 'gal']:
        try:
            product_quantity_in_oz = convert_volume_to_oz(product_quantity, product_unit)
        except ValueError:
            return False
    else:
        try:
            product_quantity_in_oz = UnitConvert(**{product_unit: product_quantity})['oz']
        except KeyError:
            return False

    # Convert serving size to ounces
    if serving_unit in ['ml', 'l', 'gal']:
        try:
            serving_quantity_in_oz = convert_volume_to_oz(serving_quantity, serving_unit)
        except ValueError:
            return False
    else:
        try:
            serving_quantity_in_oz = UnitConvert(**{serving_unit: serving_quantity})['oz']
        except KeyError:
            return False

    # Compare the quantities within the margin of error
    if abs(product_quantity_in_oz - serving_quantity_in_oz) <= margin_of_error:
        return True
    else:
        return False



def invert_dictionary(my_dict):

    # Inverted dictionary using defaultdict
    inverted_dict = defaultdict(list)
    for key, values in my_dict.items():
        for value in values:
            inverted_dict[value].append(key)

    # Post-process to make single-value lists into single values
    for key, value in inverted_dict.items():
        if len(value) == 1:  # If there's only one key for this value
            inverted_dict[key] = value[0]  # Replace list with the single value

    # Convert defaultdict to a regular dictionary and print
    return dict(inverted_dict)


def generate_sitemap(site_path:str) -> list:
    """
    Generates a sitemap by reading a CSV file from Google Cloud Storage (GCS).

    This function retrieves a CSV file from GCS, processes its content, and returns
    a list of site entries.

    Args:
        site_path (str): The GCS file path (e.g., "gs://bucket-name/path/to/file.csv").

    Returns:
        list: A list containing the site entries extracted from the CSV file.
    """
    # Initialize empty sitemap list
    sitemap = []

    # Call read csv from gcs 
    site_csv = read_csv_from_gcs(site_path)

    # Append to sitemap list
    for site in site_csv:    
        sitemap.append(site)

    return sitemap

def list_folders_in_bucket(bucket_name:str, folder_path:str) -> list:
    """
    Lists all folder names within a specified path in a Google Cloud Storage (GCS) bucket.

    This function retrieves the names of all "folders" (i.e., common prefixes) within 
    a given folder path inside a GCS bucket. It uses the `delimiter='/'` parameter 
    to treat objects as directory-like structures.

    Args:
        bucket_name (str): The name of the GCS bucket.
        folder_path (str): The path within the bucket where folders should be listed. 
                        This should end with a `/` to properly target a directory.

    Returns:
        list[str]: A list of folder names (subdirectories) within the specified path.
    """
    # Initialize the Google Cloud Storage client
    client = storage.Client()

    # Access the specified bucket
    bucket = client.bucket(bucket_name)

    # List blobs in the specified folder
    blobs = client.list_blobs(bucket_name, prefix=folder_path, delimiter='/')

    # Extract folder names
    folders = []
    for page in blobs.pages:
        folders.extend(page.prefixes)  # `prefixes` contains only folder names

    # Print or return folder names
    folder_names = [folder[len(folder_path):].rstrip('/') for folder in folders]
    
    return folder_names

def generate_intersecting_sitemap_df(bucket_name:str,base_path:str,sitemap:list):
    """
    Generates a DataFrame containing only the SKUs that exist in both a given sitemap 
    and the scraped products from a Google Cloud Storage (GCS) bucket.

    This function retrieves product folder names from the specified GCS bucket path, 
    extracts their SKUs, and compares them against the SKUs present in the provided sitemap. 
    It then filters the sitemap to only include SKUs that are present in both sources.

    Args:
        bucket_name (str): The name of the GCS bucket.
        base_path (str): The base folder path in the bucket where product folders are stored.
        sitemap (list[dict]): A list of dictionaries representing the sitemap, where each 
                              dictionary contains at least a 'SKU' key.

    Returns:
        pd.DataFrame: A DataFrame containing only the entries from the sitemap where the SKU 
                      exists in the scraped product folders.
    """
    
    # List folder in buckets
    scraped_products = (list_folders_in_bucket(bucket_name, base_path + '/'))
    
    # Get scraped SKUs
    scraped_skus = set([text.split('-', 1)[0] for text in scraped_products])
    
    # Get sitemap SKUs
    sitemap_skus = set([site['SKU'] for site in sitemap])
    
    # Get intersecting SKUS
    intersecting_skus = list(sitemap_skus.intersection(scraped_skus))
    
    # Define DataFrame
    sitemap_df = pd.DataFrame(sitemap)
    
    # Define intersecting sitemap dataframe
    intersecting_sitemap_df = sitemap_df[sitemap_df['SKU'].isin(intersecting_skus)]
    
    return intersecting_sitemap_df

def get_secret(secret_name: str, project_id: str) -> dict:
    """
    Retrieve a secret from GCP Secret Manager and parse it as a dictionary.

    Args:
        secret_name (str): The name of the secret.
        project_id (str): The GCP project ID.

    Returns:
        dict: A dictionary containing the secret's key-value pairs.
    """
    try:
        # Create a Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

        # Fetch the secret
        response = client.access_secret_version(request={"name": secret_path})
        secret_json = response.payload.data.decode("UTF-8")  # Decode secret value

        # Parse the JSON secret
        secret_dict = json.loads(secret_json)

        return secret_dict

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve secret: {e}")

def store_secret(secret_name:str,project_id:str):
    """
    Store a secret from GCP Secret Manager into env variables

    Args:
        secret_name (str): The name of the secret.
        project_id (str): The GCP project ID.

    Returns:
        dict: A dictionary containing the secret's key-value pairs.
    """
    # Fetch the secret
    secrets = get_secret(secret_name, project_id)

    # Set each secret as an environment variable
    for key, value in secrets.items():
        os.environ[key] = value  # Store in environment

    pass

