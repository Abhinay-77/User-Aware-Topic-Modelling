
import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

text = "Weekend lo friends tho outing ki vellali ani plan chesthunna."
prompt = f"""
Task: Process the following Telugu-English mixed sentence (Tanglish).
1. Transliteration: Convert to correct and natural Telugu script. Do not translate meaning.
2. Translation: Translate to a proper, grammatically correct English sentence.

Return ONLY a JSON object with 'telugu' and 'english' keys.
Input: {text}
"""

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.1,
        "topP": 0.95,
        "maxOutputTokens": 1024,
        "response_mime_type": "application/json"
    }
}

print(f"Testing ROBUST combined call with API Key: {api_key[:10]}...")
max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.post(f"{api_url}?key={api_key}", json=payload, timeout=60)
        print(f"Attempt {attempt+1} Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Success!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            break
        elif response.status_code == 429:
            print(f"Quota exceeded, waiting {2**(attempt+1)}s...")
            time.sleep(2 ** (attempt + 1))
        else:
            print(f"Error Response: {response.text}")
            break
    except Exception as e:
        print(f"Error on attempt {attempt+1}: {e}")
        if attempt < max_retries - 1:
            time.sleep(1)
