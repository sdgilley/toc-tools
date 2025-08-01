# WORK IN PROGRESS

These scripts attempt to use Foundry to help summarize the articles.

## Add agent responses to spreadsheet

> ⚠️ **WARNING:** This big beautiful script would be great except for one tiny detail. The agent doesn't return correct results. Leaving it here for now, but not using it. I'll create a more mundane way of getting this info for now.

Use an Azure AI Foundry agent to analyze each URL in your spreadsheet and extract structured data. The agent will return JSON data with HUB-ONLY, CODE, TABS, PORTAL, and SCREENSHOTS fields (all as True/False values).

The agent looks at published files, not local ones.
  
NOTE: If you have pivots, this agent is only giving information for the default pivot.

### Setup for docs agent

1. In Foundry, create an agent.  Give it these instructions:

    ```plaintext
    You are analyzing Microsoft Learn documentation pages. For each URL provided, carefully examine the content and extract the following information. Be thorough and accurate in your analysis.

    For the given URL, extract this information:
    1. HUB-ONLY: Does the article discuss or require AI Foundry hubs, hub-based projects, or hub resources? Look for any mentions of "hub", "AI Foundry hub", "create a hub", "hub resources", or content that is specifically about working with hubs. Return true if the article is primarily about hub functionality or requires hub creation/usage. (True/False)
    
    2. CODE: Does the article contain actual code examples, code blocks, or programming snippets? Look for code fences (```), inline code blocks, Python/JavaScript/C# code, SDK examples, or downloadable code samples. Do not count simple configuration JSON, CLI commands, or basic file paths as code. (True/False)
    
    3. TABS: Does the article use tab controls or tabbed interfaces to organize content? Look for UI elements that allow switching between different programming languages, platforms, or content sections (like "Python", "C#", "JavaScript" tabs). (True/False)
    
    4. PORTAL: Does the article contain specific instructions for using the Azure AI Foundry portal interface? Look for step-by-step portal navigation, mentions of clicking buttons/menus in the portal, or portal-specific workflows. (True/False)
    
    5. SCREENSHOTS: Does the article contain screenshots, images, or visual examples showing the Azure AI Foundry portal interface? Look for any images of the portal UI, screenshots of workflows, or visual guides. (True/False)
    
    Read the entire page content carefully, including headings, body text, and any code examples. Be inclusive rather than restrictive in your analysis. Return the results in this exact JSON format with no additional text:
    {
      "HUB-ONLY": true,
      "CODE": false,
      "TABS": true,
      "PORTAL": false,
      "SCREENSHOTS": true
    }
    ```

1. In your **.env** file, add:
    - DOCS_AGENT_ENDPOINT - your Azure AI project endpoint
    - DOCS_AGENT_ID - your agent ID
    - AGENT_OUTPUT_FILE - output filename (optional, defaults to toc_with_agent_responses.csv)
    - AGENT_DELAY_SECONDS - delay between API calls (optional, defaults to 2 seconds)
    - RESUME_PROCESSING - set to "true" to resume from partial results (optional, defaults to false)
    - MAX_RETRIES - number of retries for quota errors (optional, defaults to 3)
    - RETRY_DELAY_SECONDS - delay after quota errors (optional, defaults to 30 seconds)
    - DEBUG - set to "true" for detailed logging (optional, defaults to false)

### Run agent analysis

1. To add agent responses to your spreadsheet:

    ```bash
    python add-agent-responses.py
    ```

    This script will:
    - Read your existing CSV file
    - Query the docs agent for each URL
    - Parse JSON responses with HUB-ONLY, CODE, TABS, PORTAL, SCREENSHOTS fields
    - Add the extracted data as new columns
    - Save progress every 5 rows to avoid losing work
    - Include error handling and status tracking
    - **Handle quota limits** with automatic retries and delays
    - **Resume capability** - can continue from where it left off if interrupted

    **For large spreadsheets:**
    - The script saves progress every 5 rows
    - If interrupted, set `RESUME_PROCESSING=true` and run again to continue
    - Quota errors trigger automatic retries with longer delays
    - Completion rate and detailed statistics are shown

    **Estimated timing**: For 100 URLs with 2-second delays, expect about 3-4 minutes (assuming no quota issues).

## Model approach

Not sure the above would be any different if it were an agent or just a model, I tried both in the playground with no difference in results.

This initial attempt read the text of the md file and fed it to a model to get a short summary of the article.  Less hallucinations that way, but also way more token use and longer processing time.  PLUS - the md files don't always contain all of the content.  