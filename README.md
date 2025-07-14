# Flexible metadata harvesting for ecology using large language models

## 📦 Repository Overview

This repository contains a tool that harvests metadata from dataset landing pages.

Our methods are described in more detail in our upcoming paper, and further data analysis and visualisation functions (used in the paper) are found in [a separate repo](https://github.com/LTER-LIFE/meta-knowledge-harvesting).


![diagram metadata harvester v3](https://github.com/user-attachments/assets/39af634b-c8be-4174-b0e9-43227148ee4e)

---

## 🧱 Folder Structure

```bash
.
├── src/                # Sourc code
├── imgs/               # Images
├── requirements.txt    # Python dependencies
└── README.md           # This file
└── setup.py            # 
```

## How to get API key

To use this software, you need access to a large language model (LLM) via an API call. Currently, we support [OpenAI](https://openai.com/) and [gemini](https://aistudio.google.com/).

#### OpenAI Manual

##### Step 1: Signing up

Sign up for Chat GPT at https://platform.openai.com/signup?launch
You can register using your email address or an existing Google, Microsoft, or Apple account.

##### Step 2: Open dashborad
After registration, you will go to to OpenAI dashboard https://platform.openai.com/api-keys to get your API key.

##### Step 3: Create API key
Create a new ChatGPT API key by clicking on `API Keys` to access the API Keys page. Then, click `+ Create new secret key` and enter an optional name in the popup. Click 'Create secret key' to generate your unique alphanumeric API key. Be sure to save it somewhere safe.

![Screenshot from 2024-10-18 16-51-01](https://github.com/user-attachments/assets/eda6d221-3168-4741-b14d-a0f0e6a4a8f3)

The ChatGPT API key is universal for all models; you do not need to create separate keys for each one.

#### Gemini Manual

##### Step 1: Sign into Google AI Studio

To get started, sign in to [Google AI Studio](https://aistudio.google.com/) using your Google account. If you don't have an account, you will need to create one first. All Google Workspace users have access to AI Studio by default.

##### Step 2: Navigate to Get API Key

Once you are signed in, go to the dashboard, you will see a "Get API key" button on the topright of the screen. Click this to begin the process of creating your API key.

##### Step 3: Create Your API Key

In the next screen, click on "Create API key". You may be prompted to create the API key in a new or existing project. After making your selection, your unique API key will be generated. Be sure to copy this key and store it in a secure location, as it is essential for using the Gemini API.