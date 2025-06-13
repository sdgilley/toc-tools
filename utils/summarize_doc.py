# Functions to summarize a document from a URL using Azure OpenAI
# Requires the Azure OpenAI service and the requests and BeautifulSoup libraries

import requests
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

def create_client():
    """Create and return an Azure OpenAI client."""
    endpoint = os.getenv("ENDPOINT_URL")

    # Initialize Azure OpenAI client with Entra ID authentication
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )

    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2025-01-01-preview",
    )



def summarize_document(doc_text: str, client, deployment) -> str:
    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that summarizes documents. What is the main purpose of this document? Provide short one or two main bullets. Instead of phrases like 'The purpose of this document is...' just jump right in with 'Provides' No need for complete sentences. Also use * for bullets, not -."
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": doc_text
                }
            ]
        }
    ]

    completion = client.chat.completions.create(
        model=deployment,
        messages=chat_prompt,
        max_tokens=200,
        temperature=0.5,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )

    # Extract and return the summary text
    return completion.choices[0].message.content

def get_page_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # Get all visible text
    text = soup.get_text(separator="\n", strip=True)
    return text

# test the summarize_document function with a URL
if __name__ == "__main__":
    # Create the Azure OpenAI client
    client = create_client()
    deployment = os.getenv("DEPLOYMENT_NAME")

    url = "https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry"
    url = "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code"
    page_text = get_page_text(url)
    summary = summarize_document(page_text, client, deployment)
    print(summary)
    # print(page_text)