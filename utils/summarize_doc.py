# Functions to summarize a document from a URL using Azure OpenAI
# Requires the Azure OpenAI service and the requests and BeautifulSoup libraries

import requests
import os
import time
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

def create_client():
    """Create and return an Azure OpenAI client."""
    endpoint = os.getenv("ENDPOINT_URL")
    
    # print(f"🔍 DEBUG: Raw endpoint from env: '{endpoint}'")
    
    # Check if endpoint is valid
    if not endpoint:
        raise ValueError("ENDPOINT_URL environment variable is not set")
    
    if endpoint == "add your endpoint here":
        raise ValueError("ENDPOINT_URL is still set to placeholder value. Please set your actual Azure OpenAI endpoint.")
    
    # Ensure endpoint has proper protocol
    if not endpoint.startswith(('http://', 'https://')):
        if '.' in endpoint:  # Looks like a domain name
            endpoint = f"https://{endpoint}"
            print(f"🔧 Added https:// protocol. New endpoint: '{endpoint}'")
        else:
            raise ValueError(f"Invalid endpoint URL: '{endpoint}'. Should be like 'https://your-resource.openai.azure.com'")
    
    print(f"✅ Using endpoint: '{endpoint}'")

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



def summarize_document(doc_text: str, client, deployment, max_retries=3, debug=False) -> str:
    # Truncate very long documents to avoid token limits
    doc_text = truncate_text_by_tokens(doc_text, debug=debug, max_tokens=6000)
    
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
        }    ]    # Debug: Show estimated input tokens
    if debug:
        estimated_input_tokens = count_tokens_in_messages(chat_prompt)
        print(f"🔍 Estimated input tokens: {estimated_input_tokens}")
        print(f"🔍 Document length: {len(doc_text)} characters")

    for attempt in range(max_retries):
        try:
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
              # Debug: Show actual token usage from API response
            if debug and hasattr(completion, 'usage') and completion.usage:
                print(f"📊 Actual token usage:")
                print(f"   Input tokens: {completion.usage.prompt_tokens}")
                print(f"   Output tokens: {completion.usage.completion_tokens}")
                print(f"   Total tokens: {completion.usage.total_tokens}")
            
            # Extract and return the summary text
            summary = completion.choices[0].message.content
            if debug:
                print(f"📝 Summary length: {len(summary)} characters ({estimate_tokens(summary)} estimated tokens)")
            return summary
            
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                print(f"Rate/Quota limit exceeded: {str(e)}")
                check_quota_info(str(e))
                wait_time = 60 * (attempt + 1)  # Exponential backoff: 60s, 120s, 180s
                print(f"Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                if attempt == max_retries - 1:
                    raise e
            else:
                raise e
    
    return "Error: Could not generate summary after retries"

def get_page_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # Get all visible text
    text = soup.get_text(separator="\n", strip=True)
    return text

def check_quota_info(error_message):
    """Extract quota information from error messages"""
    print(f"Full error message: {error_message}")
    if "quota" in error_message.lower():
        print("This appears to be a QUOTA limit (subscription/resource level)")
    elif "rate limit" in error_message.lower():
        print("This appears to be a RATE limit (deployment level)")
    print("Check your Azure OpenAI quotas in the Azure Portal under 'Quotas' or your resource's 'Quotas and usage'")

def estimate_tokens(text):
    """Rough estimate of tokens - approximately 4 characters per token for English text"""
    return len(text) // 4

def count_tokens_in_messages(messages):
    """Estimate total tokens in the message array"""
    total = 0
    for message in messages:
        if isinstance(message.get('content'), list):
            for content_item in message['content']:
                if content_item.get('type') == 'text':
                    total += estimate_tokens(content_item.get('text', ''))
        else:
            total += estimate_tokens(message.get('content', ''))
    return total

def truncate_text_by_tokens(text, debug,max_tokens=6000):
    """Truncate text to approximate token limit (leaving room for system prompt)"""
    estimated_tokens = estimate_tokens(text)
    if estimated_tokens <= max_tokens:
        return text
    
    # Truncate to approximate character count
    max_chars = max_tokens * 4
    truncated = text[:max_chars]
    
    # Try to cut at a sentence boundary
    last_period = truncated.rfind('.')
    if last_period > max_chars * 0.8:  # If we find a period in the last 20%
        truncated = truncated[:last_period + 1]
    if debug:
        print(f"⚠️ Truncating text from {len(text)} characters to {len(truncated)} characters ({estimate_tokens(truncated)} estimated tokens)")
    return truncated

# test the summarize_document function with a URL
if __name__ == "__main__":
    print("Starting debug...")
    
    # Check environment variables
    endpoint = os.getenv("ENDPOINT_URL")
    deployment = os.getenv("DEPLOYMENT_NAME")
    
    print(f"ENDPOINT_URL: {endpoint}")
    print(f"DEPLOYMENT_NAME: {deployment}")
    
    if not endpoint or endpoint == "add your endpoint here":
        print("ERROR: ENDPOINT_URL is not set properly!")
        print("Please set your Azure OpenAI endpoint URL in the environment variables")
        exit(1)
    
    if not deployment:
        print("ERROR: DEPLOYMENT_NAME is not set!")
        exit(1)
    
    print("Creating client...")
    try:
        # Create the Azure OpenAI client
        client = create_client()
        print("Client created successfully!")
    except Exception as e:
        print(f"Error creating client: {e}")
        exit(1)

    print("Testing URL...")
    url = "https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry"
    url = "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code"
    
    try:
        print("Getting page text...")
        page_text = get_page_text(url)
        print(f"Page text length: {len(page_text)} characters")
        
        print("Summarizing document...")
        print("Note: This may take a while due to rate limiting...")
        summary = summarize_document(page_text, client, deployment)
        print("Summary:", summary)
    except Exception as e:
        print(f"Error during processing: {e}")
        if "429" in str(e):
            print("Rate limit exceeded. Please wait a few minutes before trying again.")
        check_quota_info(str(e))
        import traceback
        traceback.print_exc()