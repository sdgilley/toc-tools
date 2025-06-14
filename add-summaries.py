# read a csv file and summarize the files
import pandas as pd
import os       
import time
import utils.summarize_doc as sd
from tqdm import tqdm
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


csv_file = os.getenv("OUTPUT_FILE")  # CSV file containing URLs to summarize

script_dir = os.path.dirname(os.path.abspath(__file__))
# append the script directory to the file path
file_path = os.path.join(script_dir, csv_file)  # Path to your CSV


def add_summaries(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Create the Azure OpenAI client
    client = sd.create_client()    # Load environment variables
    deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4.1-nano")
    
    # Prepare a list to hold summaries
    summaries = []
    
    # Start timing
    start_time = time.time()
    print(f"Starting to process {len(df)} rows...")
    
    # Iterate through each row in the DataFrame
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Summarizing files"):
        url = row['URL']
        if pd.isna(url) or not url.strip():
            continue  # Skip rows with no URL
        
        try:            # Get the page text
            doc_text = sd.get_page_text(url)
            if not doc_text.strip():
                continue  # Skip empty documents
            
            # Summarize the document
            summary = sd.summarize_document(doc_text, client, deployment)
            summaries.append({"URL": url, "Summary": summary})
        
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    # End timing and calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nProcessing completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"Average time per row: {duration/len(df):.2f} seconds")
    print(f"Successfully processed {len(summaries)} out of {len(df)} rows")

    # Convert summaries to DataFrame and save to CSV
    summary_df = pd.DataFrame(summaries)
    # merge with original DataFrame
    summary_df = pd.merge(df, summary_df, on='URL', how='left')
    summary_file_path = os.path.splitext(file_path)[0] + "_summaries.csv"
    summary_df.to_csv(summary_file_path, index=False)
    
    print(f"Summaries saved to {summary_file_path}")


if os.path.exists(file_path):
    add_summaries(file_path)