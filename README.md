# Flexible metadata harvesting for ecology using large language models

## 📦 Repository Overview

This repository contains a tool that harvests metadata from dataset landing pages.

Our methods are described in more detail in our upcoming paper, and further data analysis and visualisation functions (used in the paper) are found in [a separate repo](https://github.com/LTER-LIFE/meta-knowledge-harvesting).


![diagram metadata harvester v3](https://github.com/user-attachments/assets/39af634b-c8be-4174-b0e9-43227148ee4e)

---

## 🧱 Folder Structure

```bash
.
├── src/                # Source code
├── imgs/               # Images
├── requirements.txt    # Python dependencies
└── README.md           # This file
└── setup.py            # 
```

## Installation

### Prerequisites

- Python 3.8 or higher
- An API key for either [OpenAI](https://platform.openai.com/) or [Google Gemini](https://aistudio.google.com/) (see [API Key Setup](#api-key-setup) below)

### Install from GitHub

```shell
pip install git+https://github.com/LTER-LIFE/llm-metadata-harvester.git
```

### Install for Development

If you want to modify the code or contribute to the project:

```shell
git clone https://github.com/LTER-LIFE/llm-metadata-harvester.git
cd llm-metadata-harvester
pip install -e .
```

### Additional Setup

After installation, you'll need to install Playwright browsers for web scraping:

```shell
playwright install
```

### API Key Setup

This tool requires an API key for a Large Language Model service. You can use either OpenAI or Google Gemini.

**Quick Setup:**
1. Get your API key following the detailed instructions in [`llm_apikey.md`](llm_apikey.md)
2. Set your API key as an environment variable:

```shell
# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# For Gemini  
export GEMINI_API_KEY="your-api-key-here"
```

Alternatively, you can create a `.env` file in your working directory:

```
OPENAI_API_KEY=your-api-key-here
# or
GEMINI_API_KEY=your-api-key-here
```

### Verify Installation

To verify the installation worked correctly:

```python
import llm_metadata_harvester
print("Installation successful!")
```