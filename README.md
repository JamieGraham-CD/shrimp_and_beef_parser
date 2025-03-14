# Generalized Parser

## Overview
This is a generalized parsing codebase for LLM-based information extraction from scraped text sources--specific to shrimp and beef HTML parsing. The entry point of the code base is `main.py`.

---

## Prerequisites
Ensure you have the following installed:
- Python 3.x
- pip
- Jupyter Notebook

---

## Setup Steps

### 1. Create a Virtual Environment
Create a Python virtual environment named `venv`:
```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```
- On Windows:
  ```bash
  venv\Scripts\activate
  ```

Once activated, your terminal prompt should reflect the virtual environment.

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

Then run:
```bash
sudo apt-get install poppler-utils
sudo apt-get install tesseract-ocr
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth -P weights
```

### 4. Ensure Jupyter Notebook Has Access to the Virtual Environment
Add your virtual environment as a kernel in Jupyter Notebook:
```bash
python -m ipykernel install --user --name=venv --display-name "Python (venv)"
```

### 5. Select the Virtual Environment Kernel
1. Open the minimal_agent_framework notebook or create a new one.
2. Select the kernel dropdown (usually at the top-right).
3. Choose `Python (venv)` from the list.

---

## Configuration Fields

For a given run of this project, you need to specify run parameters as such: This project uses a JSON-based configuration file at  `./configs/config.json` to manage essential parameters. Below is a description of each configuration field and its purpose.

### Configuration Parameters

| **Field**                     | **Type**  | **Description**                                                                                                                                                                    |
|------------------------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `project_id`                 | `str`    | The Google Cloud Platform (GCP) project ID where the application is deployed. This is required for accessing cloud resources such as Secret Manager.                                |
| `secret_name`                | `str`    | The name of the secret stored in GCP Secret Manager that contains credentials or sensitive environment variables.                                                                   |
| `max_chunk_size`             | `int`    | The maximum number of characters per chunk when splitting large text inputs for processing. Larger values improve efficiency but may exceed model token limits.                     |
| `output_filepath`            | `str`    | The file path where the processed output will be saved. Default format is CSV (`.csv`).                                                                                            |
| `input_type`                 | `str`    | The type of input file being processed. Can be `pdf`, `images`, `html`, or other supported formats.                                                                                   |
| `user_input_path`            | `str`    | The local file path to the input document that will be processed by the application.                                                                                               |
| `dynamic_schema_prompt`      | `str`    | The file path to the prompt template used for dynamically generating structured output schemas based on the document content.                                                      |
| `dynamic_schema_instructions`| `str`    | The file path to the instruction set that guides schema generation logic for extracting structured data.                                                                            |
| `system_prompt_path`         | `str`    | The file path to the system-level prompt that defines the AI model’s behavior and constraints.                                                                                      |
| `run_id`                     | `str`    | A unique identifier for each processing run. Used for tracking executions and debugging.                                                                                           |
| `max_llm_retries`            | `int`    | The maximum number of retries allowed if the LLM request fails due to network issues or API rate limits.                                                                            |
| `base_temperature`           | `float`  | The temperature setting for the LLM model, controlling response randomness. Lower values (e.g., `0.2`) make responses more deterministic, while higher values increase creativity.  |
| `llm-model-deployment-name`  | `str`    | The deployment name of the Azure OpenAI model used for inference. This is required for API calls to the LLM.                                                                        |
| `merge_system_prompt`        | `str`    | The file path to the instruction set that guides merging logic for combining partial responses resulted from chunking.                                                             |
| `use_llm_vision`            | `bool`   | Boolean flag to use LLM vision (set to true) or OCR for images extraction (set to false).                                                                                          |
| `gcp_png_path`              | `str`   | Path to GCP bucket where image or image folder is stored. 
---

### Example Configuration File (`config.json`)

```json
{
    "project_id": "cd-ds-384118",
    "secret_name": "generalized-parser-des",
    "max_chunk_size": 50000,
    "output_filepath": "./outputs/output.csv",
    "input_type": "pdf",
    "user_input_path": "./inputs/large_document.pdf",
    "dynamic_schema_prompt": "./prompts/dynamic_schema_prompt.txt",
    "dynamic_schema_instructions": "./prompts/dynamic_schema_instructions.txt",
    "system_prompt_path": "./prompts/system_prompt.txt",
    "run_id": "sdfdsr2398w90r",
    "max_llm_retries": 3,
    "base_temperature": 0.2,
    "llm-model-deployment-name": "docs-dev-struct-4o"
}
```

---

## Gemini Structured Outputs

When using **Gemini** for structured JSON output, here are **key considerations**:

1. **Schema Definition Counts Toward Tokens**  
   - The **schema** you provide (for instance, a JSON schema from your Pydantic model) is included in the model’s token usage. Complex or large schemas may reduce the available token space for the actual prompt content.

2. **Supported Mime Types**  
   - Gemini currently supports only certain output formats. Commonly `application/json` works for structured generation. If you request an unsupported type, the request may fail or be ignored.

3. **Complex Schemas Can Error Out**  
   - If your schema is too complex or has many nested arrays, optional fields, or large enums, you might see `InvalidArgument: 400`. Simplify property names, reduce constraints, or flatten nested structures to fix.

4. **Subset of Vertex AI Schema Fields**  
   - Not all advanced fields are respected. For example, `format` with `date-time` is recognized, but more exotic constraints might be ignored. Check [Supported schema fields](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output) for a list.

5. **No UI Support**  
   - You must define the schema via the **API**. The console does not provide a direct interface for adding your JSON schema.  

If you encounter repeated schema-related errors, try:

- **Shortening** property or enum names.  
- **Flattening** deeply nested arrays or objects.  
- **Reducing** the number of optional fields or enumerations.  

---
# shrimp_and_beef_parser
