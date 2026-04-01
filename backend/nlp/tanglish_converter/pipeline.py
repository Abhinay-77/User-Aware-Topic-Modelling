from typing import Dict, Any, List
import asyncio
from translation.translator import gemini_service, clean_text

async def convert_tanglish(text: str) -> List[Dict[str, Any]]:
    """
    Main pipeline function using Gemini API for high-quality conversion.
    Input → Gemini Transliteration → Gemini Translation
    """
    if not text or not text.strip():
        return []
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    results = []

    async def process_line(line: str):
        # Optimized: Single Gemini call for both tasks
        res = await gemini_service.call_gemini(line, "combined")
        
        return {
            "original_text": line,
            "telugu_text": res.get("telugu", line),
            "english_text": res.get("english", line),
            "detected_language": "telugu_english_mix",
            "confidence_score": 1.0
        }

    tasks = [process_line(line) for line in lines]
    results = await asyncio.gather(*tasks)
    return results
