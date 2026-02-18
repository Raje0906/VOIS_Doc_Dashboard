import os
import requests
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        self.api_url = os.getenv("LANGFLOW_URL")
        self.api_token = os.getenv("LANGFLOW_API_TOKEN")
        
        if not self.api_token:
            print("Warning: LANGFLOW_API_TOKEN not found in environment variables")
        if not self.api_url:
            print("Warning: LANGFLOW_URL not found in environment variables")

    def query_agent(self, message, tweaks=None):
        """
        Sends a message to the Langflow agent and returns the response.
        """
        # Configuration provided by user for Doctor App
        api_url = "https://aws-us-east-2.langflow.datastax.com/lf/5db4f5b7-e030-4086-b5c5-b8dbd45a42c1/api/v1/run/cce9bd23-a780-4afd-96cd-4dfb83e183df"
        org_id = "d9534c49-4182-4860-85ea-1af8d3b41043"
        
        # Use env var token if available, otherwise warn
        if not self.api_token:
            print("Warning: LANGFLOW_API_TOKEN is missing. Please check .env")

        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
        }
        
        if tweaks:
            payload["tweaks"] = tweaks

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "X-DataStax-Current-Org": org_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract text safely
            try:
                outputs = data.get('outputs', [])
                if outputs:
                    result = outputs[0]['outputs'][0]['results']['message']
                    if isinstance(result, dict) and 'text' in result:
                        return result['text']
                    elif hasattr(result, 'data') and 'text' in result.data:
                         return result.data['text']
                    else:
                         return str(result)
                return "No response from agent."
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error parsing Langflow response: {e}")
                return "Error parsing agent response."

        except requests.exceptions.RequestException as e:
            print(f"RAG Service Error: {e}")
            return f"Error connecting to AI agent: {str(e)}"

    def get_medicine_recommendations(self, condition):
        """
        Asks the agent for medicine recommendations based on a condition.
        """
        prompt = f"Suggest standard medicines and treatments for the following condition, keeping in mind CKD (Chronic Kidney Disease) constraints if applicable: {condition}. Provide a concise list."
        return self.query_agent(prompt)
