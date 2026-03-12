import re

# Comprehensive Telugu transliteration mapping
TELUGU_VOWELS = {
    'a': 'అ', 'aa': 'ా', 'e': 'ే', 'ee': 'ీ', 'i': 'ి', 'ii': 'ీ',
    'o': 'ో', 'oo': 'ూ', 'u': 'ు', 'uu': 'ూ',
}

TELUGU_CONSONANTS = {
    # Velar
    'k': 'క', 'kh': 'ఖ', 'g': 'గ', 'gh': 'ఘ', 'ng': 'ఙ',
    # Palatal
    'ch': 'చ', 'chh': 'ఛ', 'j': 'జ', 'jh': 'ఝ', 'ny': 'ఞ',
    # Retroflex
    'tt': 'ట', 'tth': 'ఠ', 'dd': 'డ', 'ddh': 'ఢ', 'nn': 'ణ',
    # Dental
    't': 'త', 'th': 'థ', 'd': 'ద', 'dh': 'ధ', 'n': 'న',
    # Labial
    'p': 'ప', 'ph': 'ఫ', 'b': 'బ', 'bh': 'భ', 'm': 'ము',
    # Semivowels and others
    'y': 'య', 'r': 'ర', 'l': 'ల', 'w': 'వ', 'v': 'వ', 's': 'స', 'sh': 'శ', 'ss': 'ష', 'h': 'హ'
}

# Complete dictionary of common Tanglish words to Telugu - ENHANCED
TANGLISH_DICT = {
    # Pronouns
    'nuvvu': 'నువ్వు', 'nenu': 'నేను', 'meeru': 'మీరు', 'miru': 'మీరు', 'manam': 'మనం',
    'adi': 'అది', 'vi': 'వి', 'vayi': 'వాయి', 'aame': 'ఆమె', 'ame': 'ఆమె', 'naku': 'నాకు',
    
    # Common verbs - EXPANDED with case-insensitive variations
    'vellanu': 'వెళ్ళను', 'velanu': 'వెళ్ళను', 'vella': 'వెళ్ళ', 'vel': 'వెళ్ళ',
    'vastanu': 'వస్తున్నాను', 'vasta': 'వస్తుంది', 'vaste': 'వస్తే', 'vastunna': 'వస్తున్న',
    'chesthanu': 'చేస్తున్నాను', 'chesta': 'చేస్తుంది', 'chestanu': 'చేస్తున్నాను', 'chey': 'చేయ్',
    'chestunnanu': 'చేస్తున్నాను',
    'untundi': 'ఉంది', 'undhi': 'ఉంది', 'undi': 'ఉంది', 'unnadi': 'ఉన్నది', 'unna': 'ఉన్న',
    'untaru': 'ఉంటారు', 'unta': 'ఉంటా',
    'bagunnanu': 'బాగున్నాను', 'bagunnanu': 'బాగున్నాను', 'bagundi': 'బాగుంది',
    'ledu': 'లేదు', 'ledhu': 'లేదు', 'kaadu': 'కాదు', 'kadu': 'కాదు',
    'koni': 'కోని', 'konidi': 'కోనిది',
    'kavali': 'కావాలి', 'kavalli': 'కావాలి', 'kalista': 'కలిస్తా',
    'kaluddam': 'కలుద్దాం', 'kaludu': 'కలుద్ద',
    
    # Adjectives - EXPANDED
    'baga': 'బాగా', 'bagundi': 'బాగుంది', 'bagundhi': 'బాగుంది', 'bagunnandu': 'బాగున్నాను',
    'chala': 'చాలా', 'chaala': 'చాలా', 'chalaa': 'చాలా',
    'manchi': 'మంచి', 'manchigo': 'మంచిగో', 'manchidi': 'మంచిది',
    'andamga': 'అందంగా', 'andam': 'అందం', 'andamga': 'అందంగా',
    'pedda': 'పెద్ద', 'chinna': 'చిన్న', 'valla': 'వల్ల',
    
    # Adverbs - EXPANDED
    'ippudu': 'ఇప్పుడు', 'ippude': 'ఇప్పుడే', 'ippud': 'ఇప్పుడు',
    'taruvatha': 'తరువాత', 'taruvata': 'తరువాత', 'tarvatha': 'తరువాత', 'repu': 'రేపు',
    'inka': 'ఇంక', 'inkuva': 'ఇంకువ', 'inkapudu': 'ఇంకా ఇప్పుడు',
    'nithyam': 'నిత్యం', 'sadharani': 'సాధారణ',
    
    # Postpositions - EXPANDED
    'ki': 'కి', 'ku': 'కు', 'lo': 'లో', 'la': 'ల', 'ni': 'ని', 'nu': 'ను',
    'tho': 'తో', 'thone': 'తోనే', 'kosam': 'కోసం', 'valla': 'వల్ల', 'nundi': 'నుండి',
    
    # Questions
    'emi': 'ఏమి', 'emiti': 'ఏమిటి', 'enti': 'ఏమిటి', 'enduku': 'ఎందుకు', 'evaru': 'ఎవరు',
    'ekkada': 'ఎక్కడ', 'eppudu': 'ఎప్పుడు', 'yenta': 'యెంత', 'entalo': 'ఎంతలో',
    
    # Common nouns - EXPANDED
    'mama': 'మమ', 'papa': 'పప', 'nonna': 'నన్న', 'pedda': 'పెద్ద',
    'kodukulu': 'కోడుకులు', 'ammayi': 'అమ్మాయి', 'pillodu': 'పిల్లోడు',
    'peru': 'పేరు', 'intlo': 'ఇంట్లో', 'intika': 'ఇంటిక',
    'coffee': 'కాఫీ', 'tea': 'టీ', 'movie': 'సినిమా', 'cinema': 'సినిమా',
    'job': 'ఉద్యోగం', 'work': 'పని', 'office': 'ఆఫీసు',
    'ee': 'ఈ', 'mee': 'మీ', 'naa': 'నా',
    
    # Common phrases/expressions
    'hello': 'హలో', 'hi': 'హాయ్', 'bye': 'బై', 'thankyou': 'ధన్యవాదాలు',
    'please': 'దయచేసి', 'sorry': 'సారీ', 'ok': 'సరి',
    
    # Additional common Tanglish - from examples
    'bagunnanu': 'బాగున్నాను',
    'try': 'ప్రయత్న',
    'chestunnanu': 'చేస్తున్నాను',
}

# Words that should NOT be transliterated (English words)
ENGLISH_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'is', 'are', 'am', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may',
    'office', 'home', 'school', 'college', 'work', 'time', 'day', 'week',
    'month', 'year', 'today', 'tomorrow', 'yesterday', 'now', 'then', 'here',
    'there', 'this', 'that', 'these', 'those', 'good', 'bad', 'nice', 'fine',
    'ok', 'okay', 'yes', 'no', 'maybe', 'email', 'phone', 'address', 'name'
}

def is_english_word(word: str) -> bool:
    """Accurately detect if a word is English."""
    word_lower = word.lower().strip()
    
    # Check against English dictionary
    if word_lower in ENGLISH_WORDS:
        return True
    
    # Check if it's mostly Latin characters and doesn't follow Telugu phonetics
    if not any(ord(c) > 0x0C00 for c in word):  # No Telugu characters
        # Check for typical English patterns
        if re.match(r'^[a-z]+$', word_lower):
            return True
    
    return False

def transliterate_word_advanced(word: str) -> str:
    """Advanced word-level transliteration."""
    word_lower = word.lower().strip()
    
    if not word_lower:
        return word
    
    # Direct mapping lookup
    if word_lower in TANGLISH_DICT:
        return TANGLISH_DICT[word_lower]
    
    # If it's English, keep it
    if is_english_word(word_lower):
        return word
    
    # Try partial matching with common endings
    for key, value in sorted(TANGLISH_DICT.items(), key=lambda x: len(x[0]), reverse=True):
        if word_lower.startswith(key) and len(word_lower) > len(key):
            suffix = word_lower[len(key):]
            # Only apply if suffix is a known postposition or ending
            if suffix in TANGLISH_DICT or suffix in ['ki', 'ku', 'lo', 'la', 'ni', 'nu', 'tho']:
                return TANGLISH_DICT[key] + (TANGLISH_DICT.get(suffix) or TANGLISH_DICT.get(suffix, suffix))
    
    # Character-level transliteration for unknown words
    result = transliterate_character_level(word_lower)
    if result != word_lower:
        return result
    
    # Default: keep original if can't transliterate
    return word

def transliterate_character_level(text: str) -> str:
    """Character-level transliteration for unknown words."""
    if not text:
        return text
    
    # Sort consonants by length (longest first) to avoid partial matches
    sorted_consonants = sorted(TELUGU_CONSONANTS.items(), key=lambda x: len(x[0]), reverse=True)
    sorted_vowels = sorted(TELUGU_VOWELS.items(), key=lambda x: len(x[0]), reverse=True)
    
    result = text
    
    # Apply consonant transliteration
    for roman, telugu in sorted_consonants:
        result = result.replace(roman, telugu)
    
    # Apply vowel transliteration
    for roman, telugu in sorted_vowels:
        result = result.replace(roman, telugu)
    
    return result

def transliterate_tanglish_to_telugu(text: str) -> str:
    """
    Main function: Convert Tanglish text to Telugu script.
    Handles mixed Telugu-English text intelligently.
    """
    if not text:
        return ""
    
    # Split into words preserving spaces
    words = text.split()
    result = []
    
    for word in words:
        # Transliterate each word
        telugu_word = transliterate_word_advanced(word)
        result.append(telugu_word)
    
    # Join with spaces
    telugu_text = ' '.join(result)
    
    # Fix spacing
    telugu_text = re.sub(r'\s+', ' ', telugu_text).strip()
    
    
    return telugu_text

def post_process_telugu(text: str) -> str:
    """Post-process Telugu text."""
    if not text:
        return ""
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([।॥।])', r'\1', text)
    text = re.sub(r'([।॥।])\s*', r'\1 ', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

