# toc-tools
tools to help inventory and organize a toc

## Setup for Python

1. Create an environment:

    ```bash
    py -3 -m venv .venv
    .venv\scripts\activate
    ```

1. Install packages into environment:

    ```bash
    pip install -r requirements.txt
    ```



## Scripts

1. To create an inventory of the files in your toc, First edit **build-spreadsheet.py** to provide path to the TOC.
1. To create the spreadsheet:

    ```bash
    python build-spreadsheet.py
    ```


## Add summaries 

Use Foundry to add a model that summarizes each of the files in your spreadsheet

### Setup for AI 

First, rename the **env.txt** file in this repo to **.env**

Now deploy a model in Foundry:

1. Sign in to Azure AI Foundry (https://ai.azure.com)
1. Create or select a project
1. Select a model to use for summaries.  I used **gpt-4.1-nano**
1. On the models page, copy the ENDPOINT value, and add it to your **.env** file
1. If you use a different model name, replace the current value it to the **.env** file as well
1. To add AI generated summaries to the entries:  

    1. Log in to the same account used in Azure AI Foundry:

        ```bash
        az login --use-device-code
        ```

    1. Edit **add-summaries.py** to specify the filename of your spreadsheet.  Then run:

        ```bash
        python add-summaries.py
        ```

        !NOTE: this script calls your deployed model for each file.  May become expensive?  I'll add some idea of how much for my use case when I know more.  
