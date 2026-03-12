from typing import Dict, Any
from .normalizer import normalize_tanglish
from .language_detector import detect_language_mix
from .transliterator import transliterate_tanglish_to_telugu, post_process_telugu

# Import enhanced translator - using absolute path approach
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from translation.translator import translate_tanglish_to_english

def convert_tanglish(text: str) -> Dict[str, Any]:
    """
    Main pipeline function to convert Tanglish to Telugu script and English.
    
    Args:
        text: Input Tanglish text (code-mixed Telugu-English)
    
    Returns:
        Dictionary with:
        - original_text: Original input text
        - telugu_text: Converted Telugu script
        - english_text: Translated English text
        - detected_language: Language detection result
        - confidence_score: Confidence score (0.0-1.0)
    """
    if not text or not text.strip():
        return {
            "original_text": text or "",
            "telugu_text": "",
            "english_text": "",
            "detected_language": "unknown",
            "confidence_score": 0.0
        }
    
    original_text = text
    
    # Step 1: Normalize text
    normalized_text = normalize_tanglish(text)
    
    # Step 2: Detect language
    detected_lang, confidence = detect_language_mix(normalized_text)
    
    # Step 3: Transliterate to Telugu script
    telugu_text = transliterate_tanglish_to_telugu(normalized_text)
    
    # Step 4: Post-process Telugu
    telugu_text = post_process_telugu(telugu_text)
    
    # Step 5: Translate to English using enhanced translator
    english_text = translate_tanglish_to_english(normalized_text)
    
    # If Telugu transliteration failed or is same as input, keep original
    if not telugu_text or telugu_text == normalized_text:
        telugu_text = normalized_text
    
    return {
        "original_text": original_text,
        "telugu_text": telugu_text,
        "english_text": english_text,
        "detected_language": detected_lang,
        "confidence_score": round(confidence, 2)
    }
