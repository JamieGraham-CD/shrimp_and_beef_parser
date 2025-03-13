from datetime import datetime
import json
from typing import Callable, List, Tuple, Dict
import pandas as pd # type: ignore
from Prompts.wesel_prompts import *
import os
from Tools.tools import *
from openai import AzureOpenAI
from Agents.agents import Agent
from logger import Logger
from utils import sanitize_filename
from Workflow.google_storage_workflow import create_folder_if_not_exists, upload_csv_to_bucket
from Workflow.structured_outputs import *
from SmartScraper.programmatic_scraper import *
from Retrieval.canteen_gcp_retrieval import CanteenGCPRetrieval
from PreProcessor.canteen_pre_processor import CanteenPreProcessor
from Validator.canteen_validator import CanteenValidator
from Finalizer.canteen_finalizer import CanteenFinalizer
from Parser.canteen_parser import CanteenParser
import logging 
from Models.gpt_models import GPTModel
from Models.gemini_models import GeminiModel
from Pipeline.pipeline import Pipeline
import time
import random
from dotenv import load_dotenv

def create_products_output_dir(agent_name: str) -> str:
    """Creates output directory for logs and data and returns its relative path"""
    cwd = os.path.dirname(__file__)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    # Create relative path for directory
    output_dir = f"{cwd}/output/{timestamp}_{agent_name}"
    # Create the directory if not already exists
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def fetch_product_data(
    generate_agent: Callable,
    products: List[dict],
    local_output: bool = True,
    folder_name: str = "",
    upload_to_gcp: bool = False,
    bucket_name: str = "",
    base_path: str = "",
    intermediate_results_path: str = "",
    tasks: list = ["nutrition","ingredients","allergens"]
):
    """
    Fetches product data using an agent and saves results to a CSV file.

    Args:
        generate_agent (Callable): A function that generates an agent to process product data.
        products (List[Tuple[str, str]]): A list of tuples containing product identifiers (e.g., SKU, product name).
        local_output (bool, optional): Whether to save the results locally. Defaults to True.
        folder_name (str, optional): Name of the folder to store product data. Defaults to an empty string.
        upload_to_gcp (bool, optional): Whether to upload the results to Google Cloud Storage (GCP). Defaults to False.
        bucket_name (str, optional): The name of the GCP storage bucket. Required if `upload_to_gcp` is True. Defaults to an empty string.
        base_path (str, optional): The base directory for storing the processed files. Defaults to an empty string.
        intermediate_results_path (str, optional): Path to store intermediate processing results. Defaults to an empty string.
        tasks (list, optional): A list of processing tasks to execute, such as "nutrition", "ingredients", and "allergens". Defaults to ["nutrition", "ingredients", "allergens"].

    Returns:
        None

    Raises:
        Exception: If an error occurs during data fetching or saving.
    """
    # Define columns for the DataFrame
    create_folder_if_not_exists(['results-v2'])

    # Setup global logger
    logger_handler = Logger(bucket_name,name="wesel")
    logger = logger_handler.get_logger()

    # Create agent
    agent = generate_agent(logger)

    # Output logs to local directory
    if local_output:
        output_dir = create_products_output_dir(agent.name)
    
    list_of_prods = []
    # Process each product and update DataFrame
    for product in products:

        # intialize sku variables
        product['Product Name'] = product['Product Name'].replace('/','')
        manufacturer = product.get('Manufacturer')
        product_name = product.get('Product Name')
        product_size = product.get('Size UOM')

        print(f"Searching {manufacturer} - {product_name}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create new log file for specific product
        filename = sanitize_filename(f"{product_name}-{manufacturer}-{timestamp}.md")
        if local_output:
            logger_handler.configure_logger_file(
                filename=f"{output_dir}/{filename}",
            )

        # Configure logger for GCS
        logger_handler.configure_logger_gcs(
            bucket_name,
            f'''wesel-enterprise/logging/{folder_name}/{product.get('SKU')}-{product_name}''',
            level=logging.DEBUG
        )

        # Process SKU
        prod = process_product(product, folder_name, logger, base_path, intermediate_results_path, logger_handler, bucket_name, tasks)
      
        # Save specific product log file to GCP bucket
        print(f"Completed search for '{manufacturer} - {product_name}'")

        # Reset agent for the next product
        agent = generate_agent(logger)

        # Store results locally
        prod_df = pd.DataFrame([prod])

        sku_product_manufacturer = get_sku_product_manufacturer(product)
        prod_df.to_csv(f'''./Tmp_Output/{folder_name}/{sku_product_manufacturer}/{product.get('SKU')}_{product_name}_{manufacturer}_{product_size}_output.csv''')
        local_output_path = f'''./Tmp_Output/{folder_name}/{sku_product_manufacturer}/int_output.json'''
    
        # Store results on GCP
        if upload_to_gcp:
            if os.path.exists(local_output_path.replace('int_output.json','output.txt')):
                upload_csv_to_bucket(prod, 'results-v2', folder_name)
            else:
                upload_csv_to_bucket(prod, 'failed-results-v2', folder_name)

            logger_handler.upload_log_to_gcs()

        # Append product to list of products
        list_of_prods.append(prod)

    # Save the DataFrame to a local CSV file
    df = pd.DataFrame(list_of_prods)
    df.to_csv(f'./output.csv', index=False)

def get_sku_product_manufacturer(product:dict) -> str:
    """
    Generates a SKU-based identifier by concatenating the SKU, product name, and manufacturer.
    
    This function removes spaces from the SKU and formats the identifier as:
    "<SKU_without_spaces>-<Product Name>-<Manufacturer>".

    Args:
        product (Dict[str, str]): A dictionary containing product details with the keys:
            - "SKU" (str): The product SKU (may contain spaces).
            - "Product Name" (str): The name of the product.
            - "Manufacturer" (str): The manufacturer of the product.

    Returns:
        str: A formatted SKU-based identifier.
    """
    sku_product_manufacturer = f'''{product['SKU'].replace(' ','')}-{product['Product Name']}-{product['Manufacturer']}'''
    
    return sku_product_manufacturer

def get_intermediary_paths(
    folder_name: str, 
    sku_product_manufacturer: str, 
    intermediate_results_path: str
) -> Tuple[str, str, str]:
    """
    Generates paths for local output, GCP upload, and the prompt configuration.

    This function constructs:
    - A local output path based on the folder name and SKU-based manufacturer identifier.
    - A GCP upload path by appending the SKU identifier to the intermediate results path.
    - A prompt path read from a configuration file.

    Args:
        folder_name (str): The name of the folder for organizing outputs.
        sku_product_manufacturer (str): The formatted SKU-product-manufacturer identifier.
        intermediate_results_path (str): The base path for intermediate results storage.

    Returns:
        Tuple[str, str, str]: A tuple containing:
            - local_output_path (str): The path to the locally stored JSON output.
            - gcp_upload_path (str): The GCP upload path.
            - prompt_path (str): The path to the prompt file from the base configuration.
    """
    # Define Local Output Path
    local_output_path = f'''./Tmp_Output/{folder_name}/{sku_product_manufacturer}/int_output.json'''
    
    # Define GCP upload path
    gcp_upload_path = intermediate_results_path + f'''/{sku_product_manufacturer}'''
    
    # Read in prompt path
    with open("./configs/base-config.json","r") as file:
        base_config = json.load(file)
        prompt_path = base_config['prompt_path']

    return local_output_path, gcp_upload_path, prompt_path

def process_product(
    product:dict,
    folder_name: str, 
    logger: Logger, 
    base_path: str, 
    intermediate_results_path: str, 
    logger_handler: Logger, 
    bucket_name: storage, 
    tasks: list
):
    """
    Processes a product (SKU) through a pipeline-oriented architecture.

    Args:
        product (dict): A dictionary containing product details.
        folder_name (str): The name of the folder where product data is stored.
        logger (Logger): The primary logger instance for logging events.
        base_path (str): The base directory path for processing files.
        intermediate_results_path (str): Path to store intermediate results.
        logger_handler (Logger): Additional logger handler for monitoring logs.
        bucket_name (storage): Cloud storage bucket where files are uploaded.
        tasks (list): A list of processing tasks to be executed.

    Returns:
        product (dict): A dictionary containing product attributional information.

    Raises:
        Exception: If any step in the pipeline fails.
    """

    # Define base variable sku_product_manufacturer.
    sku_product_manufacturer = get_sku_product_manufacturer(product)
    
    # Make Tmp_Output local directory 
    os.makedirs(f'''./Tmp_Output/{folder_name}/{sku_product_manufacturer}''',exist_ok = True)

    # Get intermediary paths
    local_output_path, gcp_upload_path, prompt_path = get_intermediary_paths(folder_name,sku_product_manufacturer,intermediate_results_path)

    try:
                
        # 0. Set up configurations and initialize classes
        load_dotenv()
        gpt_model = GPTModel()
        gemini_model = GeminiModel()

        input_object = {
            "product": product,
            "bucket_name": bucket_name,
            "logger": logger,
            "logger_handler": logger_handler,
            "base_path": base_path,
            "prompt_path": prompt_path,
            "local_output_path": local_output_path,
            "gpt_model": gpt_model,
            "image_to_text_model": gemini_model,
            "tasks": tasks,
            "sku_product_manufacturer": sku_product_manufacturer
        }

        logger_handler.set_upload_path(gcp_upload_path)
        
        # 1. Extract scraped data from bucket
        gcp_retrieval = CanteenGCPRetrieval(input_object)
        gcp_retrieval.run()
        if gcp_retrieval.exit_flag:
            return product

        # 2. Clean and Preprocess Text/Image
        pre_process = CanteenPreProcessor()
        pre_process.run()
        if pre_process.exit_flag:
            return product

        # 3. LLM Parsing 
        llm_parser = CanteenParser()
        llm_parser.run()
        if llm_parser.exit_flag:
            print("exited on parser")
            return product
        
        # 4. Validator
        validator = CanteenValidator()
        validator.run()
        if validator.exit_flag:
            print("exited on validator")
            return product
        
        # 5. LLM Finalizer
        canteen_finalize = CanteenFinalizer()
        canteen_finalize.run()
        if canteen_finalize.exit_flag:
            print("exited on finalizer")
            return product
        
        print("exited at end")
        return canteen_finalize.product

    except json.JSONDecodeError as e:
        logger.debug(f"ERROR - Could not parse response: {e}")
        product["error"] = str(e)
        return product


    except Exception as e:
        product["error"] = str(e)
        logger.debug(f"ERROR - Unexpected error occurred: {e}")
        return product
