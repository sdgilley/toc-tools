from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

def query_docs_agent(url, endpoint=None, agent_id=None):
    """
    Query a documentation agent with a URL and return the response.
    
    Args:
        url (str): The documentation URL to query about
        endpoint (str, optional): Azure AI project endpoint. If None, reads from DOCS_AGENT_ENDPOINT env var
        agent_id (str, optional): Agent ID to use. If None, reads from DOCS_AGENT_ID env var
        
    Returns:
        str: The agent's response, or None if there was an error
    """
    try:
        # Get configuration from environment variables if not provided
        if not endpoint:
            endpoint = os.getenv("DOCS_AGENT_ENDPOINT")
        if not agent_id:
            agent_id = os.getenv("DOCS_AGENT_ID")
            
        if not endpoint:
            raise ValueError("Endpoint not provided and DOCS_AGENT_ENDPOINT environment variable not set")
        if not agent_id:
            raise ValueError("Agent ID not provided and DOCS_AGENT_ID environment variable not set")
        
        # Initialize the project client
        project = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=endpoint
        )
        
        # Get the agent
        agent = project.agents.get_agent(agent_id)
        
        # Create a new thread
        thread = project.agents.threads.create()
        
        # Send the URL as a message
        message = project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=url
        )
        
        # Run the agent
        run = project.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        if run.status == "failed":
            print(f"Run failed: {run.last_error}")
            return None
        
        # Get the response messages
        messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        
        # Find the agent's response (the last assistant message)
        agent_response = None
        for message in messages:
            if message.role == "assistant" and message.text_messages:
                agent_response = message.text_messages[-1].text.value
        
        return agent_response
        
    except Exception as e:
        print(f"Error querying docs agent: {e}")
        return None

def main():
    """
    Main function for testing the docs agent function.
    """
    # Example usage
    test_url = "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code"
    
    print(f"Querying docs agent with URL: {test_url}")
    response = query_docs_agent(test_url)
    
    if response:
        print(f"Agent response:\n{response}")
    else:
        print("No response received from agent")

if __name__ == "__main__":
    main()