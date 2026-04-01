
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
api_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print(f"Listing models with API Key: {api_key[:10]}...")
try:
    response = requests.get(api_url, timeout=15)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        models = response.json().get('models', [])
        for m in models:
            print(f"- {m['name']} (Methods: {m.get('supportedGenerationMethods')})")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
