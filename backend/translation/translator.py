import os
import json
import requests
import asyncio
import re
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

class GeminiService:
    """Senior NLP Engineer implemented Gemini service with advanced retry logic and stability."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Use gemini-flash-latest as found in the API model list
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        self._cache = {}

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def call_gemini(self, text: str, task_type: str) -> Any:
        """Centralized Gemini call with exponential backoff retries, 60s timeout and Vision support."""
        if not text or not text.strip():
            return ""

        if not self.is_available():
            print(f"[GEMINI_SERVICE] API Key missing. Falling back to original text.")
            return text

        cache_key = f"{task_type}:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # ── Detect Image/Vision Task ──────────────────────────────────────────
        is_image = False
        image_data = None
        
        # Check if text is a Base64 image
        if text.startswith("data:image/") and ";base64," in text:
            is_image = True
            try:
                mime_type = text.split(";")[0].split(":")[1]
                base64_data = text.split(",")[1]
                image_data = {"mime_type": mime_type, "data": base64_data}
            except:
                is_image = False

        # Check if text is an Image URL
        elif re.match(r'^https?://.*\.(jpg|jpeg|png|webp|gif)$', text.lower()):
            is_image = True
            # For URLs, we ask Gemini to fetch/describe if the API supports it, 
            # or we fetch it ourselves and send as bytes. 
            # To keep it simple, we'll treat the URL as a prompt for now.

        if is_image:
            prompt = "Describe this image in detail for topic modeling purposes. What is the main subject and context?"
            content_part = [{"text": prompt}]
            if image_data:
                content_part.append({"inline_data": image_data})
            else:
                content_part[0]["text"] += f" URL: {text}"
            
            # For images, we return a description that serves as both telugu and english proxy
            # to keep the pipeline happy
            task_type = "vision" # Override for logging
        elif task_type == "combined":
            prompt = f"""
            Task: Process the following Telugu-English mixed sentence (Tanglish).
            1. Transliteration: Convert to correct and natural Telugu script. Do not translate meaning.
            2. Translation: Translate to a proper, grammatically correct English sentence.
            
            Return ONLY a JSON object with 'telugu' and 'english' keys.
            Input: {text}
            """
            content_part = [{"text": prompt}]
        else:
            prompts = {
                "transliteration": f"Convert the following Telugu-English mixed sentence (Tanglish) into correct and natural Telugu script. Do not translate meaning, only convert to proper Telugu writing:\n{text}",
                "translation": f"Translate the following Telugu-English mixed sentence (Tanglish) into a proper, grammatically correct English sentence:\n{text}"
            }
            prompt = prompts.get(task_type, text)
            content_part = [{"text": prompt}]
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": content_part}],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "maxOutputTokens": 1024,
                "response_mime_type": "application/json" if task_type == "combined" and not is_image else "text/plain"
            }
        }

        # Enhanced Retry Logic (3 attempts with exponential backoff)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(
                        f"{self.api_url}?key={self.api_key}", 
                        headers=headers, 
                        json=payload, 
                        timeout=60 # Increased to 60s for maximum reliability
                    )
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and data['candidates']:
                        result_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        if task_type == "vision":
                            # For images, return description as both keys
                            result = {"telugu": "[Image Description]: " + result_text, "english": result_text}
                            self._cache[cache_key] = result
                            return result

                        if task_type == "combined":
                            try:
                                result = json.loads(result_text)
                                self._cache[cache_key] = result
                                return result
                            except json.JSONDecodeError:
                                # Regex fallback for non-strict JSON output
                                match = re.search(r'\{.*\}', result_text, re.DOTALL)
                                if match:
                                    result = json.loads(match.group())
                                    self._cache[cache_key] = result
                                    return result
                                return {"telugu": text, "english": text}
                        
                        self._cache[cache_key] = result_text
                        return result_text
                
                elif response.status_code == 429:
                    print(f"[GEMINI_QUOTA] Attempt {attempt+1}: Quota exceeded. Retrying in {2**(attempt+1)}s...")
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    print(f"[GEMINI_API_ERROR] Status {response.status_code}: {response.text}")
                    break # Don't retry on non-transient errors
                    
            except requests.exceptions.Timeout:
                print(f"[GEMINI_TIMEOUT] Attempt {attempt+1}: Connection timed out. Retrying...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1) # Short wait before retry
                continue
            except Exception as e:
                print(f"[GEMINI_EXCEPTION] Attempt {attempt+1}: {str(e)}")
                break

        return {"telugu": text, "english": text} if task_type == "combined" else text

# Global Singleton
gemini_service = GeminiService()

def clean_text(text: str) -> str:
    """NLP utility to clean text for modeling."""
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text.strip()
