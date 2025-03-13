from html2text import HTML2Text
from typing import List, Tuple, Set, Dict, Any
import json
from bs4 import BeautifulSoup # type: ignore
import numpy as np
# from SmartScraper.smart_scraper import SmartScraper
from Workflow.structured_outputs import ProductIngredientsData, ProductAllergensData, ProductNutritionData, FinalProductIngredientsData, FinalProductAllergensData, FinalProductNutritionData
from time import sleep
import random
import re
import pandas as pd # type: ignore
import json
from google.cloud import storage # type: ignore
import re
from PIL import Image
import io
import base64
# from Prompts.gemini_prompt import GeminiPrompt
from collections import Counter
import tiktoken
# from logger import Logger

def strip_tags(text):
    # Use regex to remove anything within < and >
    return re.sub(r'<[^>]*>', '', text)

def extract_html(scrape_flag: bool, url: str, proxy: str | None = None) -> Tuple[str, str]:
    """
    Uses Selenium to scrape the HTML of a webpage at any valid URL.

    Parameters:
        - url (str): The URL of the webpage to scrape.

    Returns:
        - str: The raw HTML content of the webpage.
    """
    scraper = SmartScraper(proxy)
    scraper.open_browser(url)
    #screen shots are for testing only
    #scraper.save_screenshot()
    html = scraper.get_page_source()
    if scrape_flag:
        screenshot_text = scraper.save_screenshot()
    else:
        screenshot_text = ''
    scraper.close_driver()
    return html, screenshot_text


def scrape_website(url: str, proxy: str | None = None) -> Tuple[str,str]:
    """
    Scrapes the HTML of a webpage at any valid URL, then extracts and preprocesses the content of the webpage to readable Markdown.

    Parameters:
        - url (str): The URL of the webpage to scrape.

    Returns:
        - str: The preprocessed HTML content of the webpage in Markdown.
    """
    try:
        html, screenshot_text = extract_html(False,url,proxy)
    except Exception as e:
        return f"ERROR: Scraping URL '{url}' with PROXY '{proxy}' failed - {e}\n", f"ERROR: Scraping URL '{url}' with PROXY '{proxy}' failed - {e}\n"

    soup = BeautifulSoup(html, 'html.parser')

    # Remove all HTML tags and extract plain text
    plain_text = soup.get_text()
    cleaned_text = "\n".join([line.strip() for line in plain_text.splitlines() if line.strip()])

    return f"\n```md\n{cleaned_text}\n```\n", screenshot_text

def scrape_website_handling_proxies(url: str, proxies: list) -> str:

    for proxy in proxies:
        scraped_html, screenshot_text = scrape_website(url,proxy)
        if 'ERROR: Scraping URL' not in scraped_html:
            return scraped_html
        
    return f"ERROR: Scraping URL '{url}' with all proxies failed\n"

def generate_google_url(query: str):
    """
    Generates Google Search Page URL given a search query.

    Parameters:
        - query (str): The search query.

    Returns:
        - str: The URL of the Google search page with the provided query.

    """
    url_data = query.replace(":", "%3A")
    url_data = url_data.replace(",", "%2")
    url_data = url_data.replace(" ", "+")
    url_data = url_data.replace("&", "%26")

    url = f"https://www.google.com/search?q={url_data}"

    return url

def parse_google_results(url: str, proxy:str) -> str:
    """
    Scrapes the HTML of a Google Search Results page for a query given its URL and returns a list of each URL with its title and description in a JSON object.

    Parameters:
        - url (str): The URL of the Google Search Results page.

    Returns:
        - str: A JSON string containing a list of dictionaries, each representing a search result with keys 'url', 'title', and 'description'.
    """
    try:
        html, screenshot_text = extract_html(False,url,proxy)
    except Exception as e:
        return f"Invalid Google URL - {url} - {e}"

    all_links = []
    parsed_response = BeautifulSoup(html, "html.parser").find_all(
        "div", attrs={"class": "g"}
    )
    for div in parsed_response:
        link = div.find("a", href=True)
        title = div.find("h3")
        desc = div.text
        if link and title and desc:
            all_links.append(
                {"url": link["href"], "title": title.text, "description": desc}
            )

    final_links:str = str(json.dumps(all_links, indent=4))
    return f"\n```json\n{final_links}\n```\n"


def google_search(query: str, proxy: str) -> str:
    """
    Searches Google for the given query and returns a list of top search results.
    
    Parameters:
        - query (str): The search query.
        - num_results (int): Number of results to return (default is 10).
        
    Returns:
        - str: A JSON string containing a list of dictionaries, each representing a search result with keys 'url', 'title', and 'description'.
    """
    url = generate_google_url(query)
    return parse_google_results(url, proxy)


def list_nested_folder_paths(bucket_name, base_path, sku=None, manufacturer=None, product_name=None):
    # Initialize the storage client
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    # Define the complete folder prefix within the base path
    if sku and manufacturer and product_name:
        folder_prefix = f"/{sku}-{manufacturer}-{product_name}".replace(" ", "-").replace("(", "").replace(")", "").replace("/", "")
        folder_prefix = base_path +  "/" + folder_prefix 
    else:
        folder_prefix = f"{base_path}/"

    # Add a trailing slash to ensure it's recognized as a "folder" prefix
    folder_prefix += "/"
    print("Folder Prefix: ", folder_prefix)
    # List all blobs that match the folder prefix
    blobs = bucket.list_blobs(prefix=folder_prefix, delimiter="/")

    # Collect paths of the folders
    folder_paths = []   
    for page in blobs.pages:
        folder_paths.extend(page.prefixes)  # Only add prefixes, representing folder paths

    # Print the folder paths
    for path in folder_paths:
        print(f"Folder path: {path}")
    print("Folder Paths: ", folder_paths)
    return folder_paths



def read_files_from_nested_folders(bucket_name, folder_path):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    # Define paths for tier folders
    tier_one_path = f"{folder_path}/tier_one_results/"
    tier_two_path = f"{folder_path}/tier_two_results/"

    # Initialize the main data structure
    output_data = {
        "tier_one": [],
        "tier_two": []
    }

    # Function to read files into the appropriate tier list
    def read_files_in_tier(tier_path, tier_list):
        blobs = bucket.list_blobs(prefix=tier_path)
        for blob in blobs:
            blob_metadata = blob.metadata
            file_name = blob.name

            if file_name.endswith(".html"):
                # Read and store HTML file content
                html_data = blob.download_as_text()
                tier_list.append({"site": blob_metadata["url"], "sitehtml": html_data, "siteurl": blob_metadata["url"]})

            elif file_name.endswith(".png"):
                # Read and convert PNG file content to a Pillow Image object
                image_data = blob.download_as_bytes()  # Download image data as bytes
                byte_image = io.BytesIO(image_data)
                tier_list.append({"site": blob_metadata["url"], "image": byte_image, "siteurl": blob_metadata["url"]})

            elif file_name.endswith(".txt"):
                tier_list.append({"site": blob_metadata["url"], "apidata": blob.download_as_text(), "siteurl": blob_metadata["url"]})

    # Read files from both tier_one_results and tier_two_results folders
    read_files_in_tier(tier_one_path, output_data["tier_one"])
    read_files_in_tier(tier_two_path, output_data["tier_two"])

    def convert_list_of_dict_to_dict(data):
        return_dict = {}
        for i in data:
            if i['site'] not in return_dict:
                return_dict[i['site']] = {}
            if 'sitehtml' in i:
                return_dict[i['site']]["sitehtml"] = i["sitehtml"]
                return_dict[i['site']]["siteurl"] = i["siteurl"]
            elif 'image' in i:
                return_dict[i['site']]["image"] = i["image"]
                return_dict[i['site']]["siteurl"] = i["siteurl"]
            else:
                return_dict[i['site']]["apidata"] = i["apidata"]
                return_dict[i['site']]["siteurl"] = i["siteurl"]
        return return_dict

    return_data = {}

    return_data["tier_one"] = convert_list_of_dict_to_dict(output_data["tier_one"])
    return_data["tier_two"] = convert_list_of_dict_to_dict(output_data["tier_two"])

    return return_data


def clean_html(html):
    
    # Remove all HTML tags and extract plain text
    try:
        soup = BeautifulSoup(html, 'html.parser')
        plain_text = soup.get_text()
        plain_text = strip_tags(plain_text)
        cleaned_text = "\n".join([line.strip() for line in plain_text.splitlines() if line.strip()])
        cleaned_text = cleaned_text.replace('   ','')
    except:
        cleaned_text = ''
        return str(cleaned_text)
    return str({cleaned_text})



def convert_tiered_json_to_url_df(tiered_json_data,product):

    tier_1_urls = set(tiered_json_data['tier_one'].keys())
    tier_2_urls = set(tiered_json_data['tier_two'].keys())

    # Create dictionary with URLs as keys and tiers as values
    url_tier_dict = {url: "tier_one" for url in tier_1_urls}
    url_tier_dict.update({url: "tier_two" for url in tier_2_urls})

    url_df_list = []
    for url in url_tier_dict:
        tmp_url_dict = {}
        url_tier = url_tier_dict[url]

        tmp_url_dict["url"] = url

        try:
            tmp_url_dict["scraped_html"] = clean_html(str(tiered_json_data[url_tier][url]["sitehtml"]))
        except:
            tmp_url_dict["scraped_html"] = 'error - convert_tiered_json_to_url_df'
        
        try:
            tmp_url_dict["scraped_png"] = tiered_json_data[url_tier][url]["image"]
        except:
            tmp_url_dict["scraped_png"] = 'error - convert_tiered_json_to_url_df'
                
        if url_tier == "tier_one":
            try:
                tmp_url_dict["scraped_api"] = clean_html(str(tiered_json_data[url_tier][url]["apidata"]))
            except:
                tmp_url_dict["scraped_api"] = 'error - convert_tiered_json_to_url_df'
            tmp_url_dict["tier"] = "Tier_1"
        else:
            tmp_url_dict["tier"] = "Tier_2"

        
        url_df_list.append(tmp_url_dict)

    df_output = pd.DataFrame(url_df_list)
    total_records = len(df_output)
    df_output['product_name'] = [product['Product Name']]*total_records
    df_output['product_manufacturer'] = [product['Manufacturer']]*total_records
    df_output['size_uom'] = [product['Size UOM']]*total_records     

    return df_output

    
def extract_data_from_bucket(product,bucket_name,base_path,local_output_path,logger, gcp_upload_path):
    
    logger_handler = Logger(bucket_name,name="wesel")
    output_paths = list_nested_folder_paths(bucket_name, base_path, sku=product["SKU"], manufacturer = product["Manufacturer"], product_name=product["Product Name"])
    testing_output_path = output_paths[0].strip("/tier_one_results/")

    tiered_json_data = read_files_from_nested_folders(bucket_name, testing_output_path)

    try:
        url_df = convert_tiered_json_to_url_df(tiered_json_data,product)
    except Exception as e:
        print(e)
    
    url_df.to_json(local_output_path.replace('int_output.json','scraped_url_df.json'),orient="records")
    url_df.to_csv(local_output_path.replace('int_output.json','scraped_url_df.csv'))

    # logger_handler.upload_to_gcp(url_df,gcp_upload_path,"scraped_url_df.csv","csv")
    # logger_handler.upload_to_gcp(dict(url_df.to_dict(orient="index")),gcp_upload_path,"scraped_url_df.json","json") 

    if len(url_df) == 0:
        # Define the string you want to save
        text_to_save = "No data was found in the google bucket for this product."
        # Specify the file name
        file_name = local_output_path.replace('int_output.json','error_message.txt')
        # Open the file in write mode and save the string
        with open(file_name, "w") as file:
            file.write(text_to_save)
        

    return url_df 

def clean_scraped_text_df(scrape_df,field):
    try:
        scrape_df[field] = scrape_df[field].apply(lambda x: clean_html(str(x)))
    except:
        scrape_df[field] = ['']*len(scrape_df)
    return scrape_df


def check_over_threshold_undetermined(task,structured_response_dict,threshold):

    task_fields = get_task_fields(task)

    task_results = [ str(structured_response_dict[key]) for key in task_fields if key in structured_response_dict]
    
    # Count occurrences
    counts = Counter(task_results)
    total_fields = len(task_results)
    total_undetermined = counts['undetermined']+counts[''] + counts['[]']

    percent_undetermined = total_undetermined/total_fields 

    if percent_undetermined >= threshold:
        return True
    else:
        return False


def check_for_empty_list(graded_results_validated,task,product,local_output_path):
    
    is_empty_list = graded_results_validated[task] == []
    if is_empty_list:
        
        text_to_save = f'''No data made it through past final validation for task: {task}'''
        # Specify the file name
        file_name = local_output_path.replace('int_output.json','error_message.txt')
        # Open the file in write mode and save the string
        with open(file_name, "w") as file:
            file.write(text_to_save)
            
        return is_empty_list
    else:
        return False


def image_to_text_gemini(image):

    # image: a binary image object
    prompt = '''
    Extract the following information from the image, in the json schema:
    "Product Name Scraped": string,
    "Servings Per Container": "amount",
    "Serving Size": "amount",
    "Calories": "amount",
    "Total Fat": "amount",
    "Saturated Fat": "amount",
    "Trans Fat": "amount",
    "Cholesterol": "amount",
    "Sodium": "amount",
    "Total Carbohydrate": "amount",
    "Dietary Fiber": "amount",
    "Total Sugars": "amount",
    "Total Added Sugars": "amount"
    "Protein": "amount"
    '''

    prompt = '''
    Extract all visible text from the image and output a string
    '''

    model = GeminiPrompt(json_mode = True)
    try:
        result = model.extract_text_from_img(image, prompt)
    except:
        result = ''
        return result
    return result


def get_task_fields(task):

    task_class = get_task_class(task)

    task_fields = list(task_class.__fields__.keys())
    task_fields = [task_item for task_item in task_fields if task_item not in ['Product_Name_Scraped','Serving_Size','log']]

    return task_fields

def get_task_class(task: str):
    """
    Retrieves the structured output class associated with a given task.

    Args:
        task (str): The name of the task to look up (e.g., 'nutrition', 'ingredients', 'allergens').

    Returns:
        Optional[type]: The class associated with the task, or None if the task is not found.
    """
    task_class_mapping = {
        "nutrition": ProductNutritionData,
        "ingredients": ProductIngredientsData,
        "allergens": ProductAllergensData,
    }

    return task_class_mapping.get(task)


def get_final_task_class(task: str):
    """
    Retrieves the final structured output class associated with a given task.

    Args:
        task (str): The name of the task to look up (e.g., 'nutrition', 'ingredients', 'allergens').

    Returns:
        Optional[type]: The class associated with the task, or None if the task is not found.
    """
    task_class_mapping = {
        "nutrition": FinalProductNutritionData,
        "ingredients": FinalProductIngredientsData,
        "allergens": FinalProductAllergensData,
    }

    return task_class_mapping.get(task)

def upsert_into_nested_dictionary(data, outer_key, inner_key, value):
    """
    Updates or inserts into a dictionary of dictionaries.

    Args:
        data (dict): The dictionary of dictionaries.
        outer_key: The key for the outer dictionary.
        inner_key: The key for the inner dictionary.
        value: The value to upsert.

    Example:
        upsert(data, "user1", "age", 26)
    """
    # Ensure the outer key exists
    if outer_key not in data:
        data[outer_key] = {}
    
    # Update or insert the inner key-value pair
    data[outer_key][inner_key] = value

    return data



def count_tokens(text: str, model: str = "gpt-4"):
    """
    Counts the number of tokens in a given text for a specified model.
    
    Parameters:
    - text (str): The input string.
    - model (str): The model to use for tokenization (default: "gpt-4").
    
    Returns:
    - int: The number of tokens.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))