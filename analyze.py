from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from dotenv import load_dotenv
import os
import time
import requests

# Load environment variables from .env file
load_dotenv()

# Retrieve Azure credentials
endpoint = os.getenv("AZURE_ENDPOINT").rstrip('/')
key = os.getenv("AZURE_KEY")

print(f"Endpoint being used: {endpoint}")
print(f"Key length: {len(key) if key else 'No key found'}")

def read_image(uri):
    try:
        # Define the API endpoint for Read operation
        vision_url = f"{endpoint}/vision/v3.2/read/analyze"
        
        # Set up headers
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Content-Type': 'application/json'
        }
        
        # Set up the request body
        body = {'url': uri}
        
        print("Making initial request to Read API...")
        # Make initial request to start the Read operation
        response = requests.post(vision_url, headers=headers, json=body)
        response.raise_for_status()
        
        print(f"Initial response status: {response.status_code}")
        
        # Get the operation location from the response headers
        if 'Operation-Location' not in response.headers:
            print("Response headers:", response.headers)
            return "Error: No Operation-Location in response headers"
            
        operation_url = response.headers['Operation-Location']
        print(f"Operation URL: {operation_url}")
        
        # Poll for results
        max_retries = 10
        retry_delay = 1
        
        print("Polling for results...")
        for i in range(max_retries):
            result_response = requests.get(operation_url, headers={
                'Ocp-Apim-Subscription-Key': key
            })
            result_response.raise_for_status()
            
            result = result_response.json()
            print(f"Poll attempt {i+1}, status: {result.get('status')}")
            
            if result.get('status') not in ['notStarted', 'running']:
                break
                
            time.sleep(retry_delay)
        
        # Process results
        if result.get('status') == 'succeeded':
            text = []
            for read_result in result.get('analyzeResult', {}).get('readResults', []):
                for line in read_result.get('lines', []):
                    text.append(line.get('text', ''))
            return ' '.join(text)
        else:
            return f"Error: Operation failed with status {result.get('status')}"

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Response content: {e.response.content if hasattr(e, 'response') else 'No response content'}")
        return f"HTTP error: {str(e)}"
    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"An exception occurred: {str(e)}"

if __name__ == "__main__":
    # Test with an image that contains text
    test_image = "https://learn.microsoft.com/en-us/azure/cognitive-services/computer-vision/images/readsample.jpg"
    
    try:
        print("\nTesting OCR with Azure Vision API...")
        result = read_image(test_image)
        print("\nOCR Result:", result)
    except Exception as e:
        print("An error occurred:", e)