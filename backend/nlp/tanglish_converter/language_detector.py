import re
from typing import Dict, Tuple

# Common Telugu words in Tanglish (non-exhaustive list)
TELUGU_KEYWORDS = {
    'nuvvu', 'nenu', 'meeru', 'manam', 'vallu', 'vadu', 'adi', 'idi',
    'vellanu', 'velanu', 'vellanu', 'vastanu', 'vastanu', 'vastanu',
    'chesthanu', 'chesthanu', 'chesthanu', 'untundi', 'undhi', 'undi',
    'ledhu', 'ledu', 'ledhu', 'kaadu', 'kadu', 'kaadu',
    'baga', 'bagundhi', 'bagundi', 'chala', 'chaala', 'chaala',
    'ippudu', 'ippude', 'ippudu', 'taruvatha', 'taruvata', 'taruvatha',
    'ki', 'ku', 'ki', 'lo', 'la', 'lo', 'ni', 'nu', 'ni',
    'naaku', 'naku', 'naaku', 'neeku', 'neku', 'neeku',
    'mee', 'me', 'mee', 'naa', 'na', 'naa'
}

# Common English words that appear in Tanglish
ENGLISH_KEYWORDS = {
    'office', 'home', 'school', 'college', 'work', 'time', 'today',
    'tomorrow', 'yesterday', 'now', 'then', 'here', 'there', 'this', 'that',
    'good', 'bad', 'nice', 'fine', 'ok', 'okay', 'yes', 'no', 'maybe'
}

def detect_language_mix(text: str) -> Tuple[str, float]:
    """
    Detect if text is Tanglish (code-mixed Telugu-English).
    Returns: (detected_language, confidence_score)
    """
    if not text:
        return "unknown", 0.0
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words:
        return "unknown", 0.0
    
    telugu_count = 0
    english_count = 0
    total_words = len(words)
    
    for word in words:
        # Check against Telugu keywords
        if word in TELUGU_KEYWORDS:
            telugu_count += 1
        # Check against English keywords
        elif word in ENGLISH_KEYWORDS:
            english_count += 1
        # Pattern-based detection for Telugu words
        elif re.match(r'^[a-z]+(u|nu|lu|ki|ku|lo|la|ni|nu)$', word):
            telugu_count += 0.5
    
    telugu_ratio = telugu_count / total_words if total_words > 0 else 0
    english_ratio = english_count / total_words if total_words > 0 else 0
    
    # Determine language
    if telugu_ratio > 0.3 or (telugu_ratio > 0.1 and english_ratio > 0.1):
        confidence = min(0.9, telugu_ratio + english_ratio)
        return "Tanglish", confidence
    elif english_ratio > 0.5:
        return "English", 0.7
    elif telugu_ratio > 0.5:
        return "Telugu", 0.7
    else:
        return "Tanglish", 0.5

def separate_telugu_english_tokens(text: str) -> Tuple[list, list]:
    """
    Separate Telugu and English tokens from Tanglish text.
    Returns: (telugu_tokens, english_tokens)
    """
    words = re.findall(r'\b\w+\b', text.lower())
    
    telugu_tokens = []
    english_tokens = []
    
    for word in words:
        if word in TELUGU_KEYWORDS:
            telugu_tokens.append(word)
        elif word in ENGLISH_KEYWORDS:
            english_tokens.append(word)
        elif re.match(r'^[a-z]+(u|nu|lu|ki|ku|lo|la|ni|nu)$', word):
            telugu_tokens.append(word)
        else:
            # Default to Telugu if ambiguous
            telugu_tokens.append(word)
    
    return telugu_tokens, english_tokens
