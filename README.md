# toc-tools

tools to help inventory and organize a toc

## Setup for Python

To run any of the scripts in this repo, first follow these steps.

1. Create an environment:

    ```bash
    py -3 -m venv .venv
    .venv\scripts\activate
    ```

1. Install packages into environment:

    ```bash
    pip install -r requirements.txt
    ```

1. Rename the **env-sample.txt** file in this repo to **.env**

1. Modify the values for:
    * TOC_FILE - the path to the TOC file you want to use (in your local repo)
    * URL_PATH - base URL for the files in that TOC file
    * OUTPUT_FILE - the name of the CSV file you want to use

## Build a CSV file showing all the files in your TOC

This script runs quickly, even for large TOCs.  It creates a spreadsheet showing the TOC structure along with the file name and URL.  

1. Create the spreadsheet:

    ```bash
    python build-spreadsheet.py
    ```

## Add summaries with Foundry Models

Use an Azure AI Foundry model to summarize each of the files in your spreadsheet.  This script takes awhile to run, so make sure you've looked at the CSV file first to make sure the URLs are correct.

Here are some benchmarks:

* TOC with 51 files, approximately 15 minutes.  

You may also run into rate limits.  Not sure I know what to do about that.  

### Setup for Founry Models

Now deploy a model in Foundry:

1. Sign in to Azure AI Foundry (https://ai.azure.com).
1. Create or select a project.
1. Select a model to use for summaries.  I used **gpt-4.1-mini**.  Set the TPM to the maximum you can when you deploy the model.  
1. On the models page, copy the ENDPOINT value, and add it to your **.env** file.
    !Note: If the URL you copy is long, delete everything after *azure.com/
1. If you use a different model name, replace the current value it to the **.env** file as well.

### Add summaries for each file

1. To add AI generated summaries to the entries in your spreadsheet:  

    1. Log in to the same account used in Azure AI Foundry:

        ```bash
        az login
        ```

    1. *Test*: Once you're logged in, make sure the summarize file works correctly.

        ```bash
        python utils/summarize_doc.py
        ```

    1. Add summaries to every row in your spreadsheet:

        ```bash
        python add-summaries.py
        ```

        !NOTE: this script calls your deployed model for each file.  It will take some time. For a TOC with 51 files, it took approximately 15 minutes.
