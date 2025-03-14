# Generalized Parser

## Overview
This is a parsing codebase for LLM-based information extraction from scraped text sources--specific to shrimp and beef HTML parsing. The entry point of the code base is `main.py`.

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
# shrimp_and_beef_parser
