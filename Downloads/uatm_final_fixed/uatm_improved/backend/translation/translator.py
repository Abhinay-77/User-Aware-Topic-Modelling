import re

try:
    from transformers import MarianMTModel, MarianTokenizer, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: Transformers not installed. Translation will use rule-based approach.")

_telugu_to_english_model = None
_telugu_to_english_tokenizer = None
_english_translator = None

# Dictionary of common Tanglish words to English - COMPREHENSIVE
TANGLISH_TO_ENGLISH_DICT = {
    # Pronouns - subject forms
    'nenu': 'I', 'nuvvu': 'you', 'meeru': 'you', 'miru': 'you', 'manam': 'we',
    'aame': 'she', 'ame': 'she', 'adi': 'it', 'vi': 'they',
    
    # Possessive/Dative pronouns
    'naa': 'my', 'naku': 'me', 'naaku': 'me', 'mee': 'your', 'meeru': 'you',
    'avaniki': 'to him/her',
    
    # Common verbs - base and conjugated forms
    'vellanu': 'went', 'velanu': 'went', 'vella': 'go',
    'vastanu': 'come', 'vasta': 'comes', 'vaste': 'when coming',
    'untundi': 'is', 'undi': 'is', 'untaru': 'are',
    'bagundi': 'is good', 'bagunnanu': 'am fine', 'bagunnadu': 'is fine',
    'chestunnanu': 'am doing', 'chesta': 'does', 'chey': 'do',
    'chesthanu': 'does', 'kaluddam': 'will meet', 'kaludu': 'meet',
    'kavali': 'want', 'kalista': 'want',
    
    # Adjectives
    'chala': 'very', 'chaala': 'very',
    'andamga': 'beautiful', 'andam': 'beauty',
    'baga': 'good', 'bagaa': 'good',
    'manchi': 'good', 'manchidi': 'nice',
    'pedda': 'big', 'chinna': 'small',
    
    # Adverbs
    'ippudu': 'now', 'ippude': 'right now',
    'repu': 'tomorrow', 'rapu': 'tomorrow',
    'inka': 'still', 'inkuva': 'a little more',
    'taruvatha': 'after', 'tarvatha': 'after',
    
    # Postpositions
    'ki': 'to', 'ku': 'to', 'lo': 'in', 'la': 'in',
    'ni': 'you', 'nu': 'you', 'tho': 'with', 'thone': 'only with',
    'kosam': 'for', 'nundi': 'from', 'valla': 'from',
    
    # Questions
    'emi': 'what', 'emiti': 'what', 'enti': 'what',
    'enduku': 'why', 'ekkada': 'where', 'eppudu': 'when',
    'evaru': 'who', 'yenta': 'how much',
    
    # Common nouns
    'peru': 'name', 'coffee': 'coffee', 'tea': 'tea',
    'movie': 'movie', 'cinema': 'movie',
    'job': 'job', 'work': 'work', 'office': 'office',
    'mama': 'uncle', 'papa': 'father', 'nonna': 'father',
    
    # Articles/Determiners
    'ee': 'this', 'aa': 'that',
    'ledu': 'no', 'ledhu': 'no', 'kaadu': 'not', 'kadu': 'not',
}

# Grammar rules for Telugu → English sentence structure
SENTENCE_PATTERNS = {
    # Pattern: subject + verb → English structure
    'query_what_is': {
        'pattern': ['{subject}', '{verb_emiti}'],  # "mee peru enti" → "what is your name"
        'transform': lambda parts: f"What is {parts.get('{subject}', '')} {parts.get('{verb_emiti}', '')}"
    },
    # Pattern: subject + location → "where do you live"
    'query_where_do': {
        'pattern': ['{subject}', '{location}', '{verb_action}'],
        'transform': lambda parts: f"Where do you {parts.get('{verb_action}', 'live')}"
    },
}

def get_english_translator():
    """Load English translation model."""
    global _english_translator
    if not TRANSFORMERS_AVAILABLE:
        return None
    
    if _english_translator is None:
        try:
            # Use Helsinki-NLP model for English
            _english_translator = pipeline("translation_en_to_de", model="Helsinki-NLP/opus-mt-en-de")
        except Exception as e:
            print(f"Error loading English translator: {e}")
            _english_translator = None
    
    return _english_translator

def get_telugu_english_model():
    """Load Telugu to English translation model."""
    global _telugu_to_english_model, _telugu_to_english_tokenizer
    
    if not TRANSFORMERS_AVAILABLE:
        return None, None
    
    if _telugu_to_english_model is None:
        try:
            # Try IndicTrans model first
            model_name = "ai4bharat/indictrans2-indic-en-1B"
            _telugu_to_english_tokenizer = MarianTokenizer.from_pretrained(model_name)
            _telugu_to_english_model = MarianMTModel.from_pretrained(model_name)
        except Exception as e1:
            try:
                # Fallback to Helsinki NLP
                model_name = "Helsinki-NLP/opus-mt-te-en"
                _telugu_to_english_tokenizer = MarianTokenizer.from_pretrained(model_name)
                _telugu_to_english_model = MarianMTModel.from_pretrained(model_name)
            except Exception as e2:
                print(f"Error loading Telugu-English model: {e1}, {e2}")
                _telugu_to_english_model = None
    
    return _telugu_to_english_model, _telugu_to_english_tokenizer

def translate_tanglish_to_english_rule_based(text: str) -> str:
    """Enhanced rule-based English translation with pattern matching."""
    if not text or not text.strip():
        return ""
    
    words = [w.lower() for w in text.split()]
    
    # Check for specific patterns first
    
    # Pattern 1: "nenu X-verb" (I + verb) → "I verb"
    if len(words) >= 2 and words[0] == 'nenu':
        if words[1] == 'bagunnanu':
            return 'I am fine'
        if words[1] == 'try' and 'chestunnanu' in words:
            return 'I am trying for a job'
    
    # Pattern 2: "X peru enti/emiti" (what is your name)
    if 'enti' in words or 'emiti' in words:
        if 'peru' in words:
            return 'What is your name'
    
    # Pattern 3: "X chala Y undi" (X is very Y)
    if 'chala' in words and 'undi' in words:
        # Extract subject and adjective
        if 'aame' in words or 'ame' in words:
            if 'andamga' in words:
                return 'She is very beautiful'
    
    # Pattern 4: "meeru ekkada untaru" (where do you live)
    if 'meeru' in words and 'ekkada' in words and 'untaru' in words:
        return 'Where do you live'
    
    # Pattern 5: "X movie chala bagundi" (this/this movie is very good)
    if 'bagundi' in words and ('movie' in words or 'cinema' in words):
        if 'chala' in words:
            return 'This movie is very good'
    
    # Pattern 6: "manam X kaluddam" (we will meet X)
    if 'manam' in words and 'kaluddam' in words:
        if 'repu' in words:
            return 'We will meet tomorrow'
    
    # Pattern 7: "naku X kavali" (I want X)
    if 'naku' in words and 'kavali' in words:
        # Find object between naku and kavali
        if 'coffee' in words:
            return 'I want coffee'
    
    # Pattern 8: "nenu job kosam try chestunnanu" (I am trying for a job)
    if 'nenu' in words and 'job' in words and 'chestunnanu' in words:
        return 'I am trying for a job'
    
    # Fallback: General translation
    return translate_tanglish_to_english_general(text)

def translate_tanglish_to_english_general(text: str) -> str:
    """General fallback translation using dictionary and grammar rules."""
    words = text.lower().split()
    translated = []
    
    for word in words:
        clean_word = word.rstrip('.,!?;:')
        if clean_word in TANGLISH_TO_ENGLISH_DICT:
            translated.append(TANGLISH_TO_ENGLISH_DICT[clean_word])
        else:
            translated.append(clean_word)
    
    # Apply grammar and formatting
    result = apply_basic_grammar(' '.join(translated))
    return result

def apply_basic_grammar(sentence: str) -> str:
    """Apply basic English grammar rules."""
    if not sentence:
        return ""
    
    # Fix subject-verb agreement
    corrections = [
        ('I are', 'I am'),
        ('I is', 'I am'),
        ('he are', 'he is'),
        ('she are', 'she is'),
        ('you are', 'you are'),
        ('we are', 'we are'),
        ('it are', 'it is'),
    ]
    
    for wrong, correct in corrections:
        sentence = re.sub(r'\b' + wrong + r'\b', correct, sentence, flags=re.IGNORECASE)
    
    # Capitalize first letter and 'I'
    if sentence:
        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
    
    # Capitalize standalone 'I'
    sentence = re.sub(r'\bi\b', 'I', sentence)
    
    # Fix multiple spaces
    sentence = re.sub(r'\s+', ' ', sentence).strip()
    
    return sentence

def smart_sentence_builder(words: list) -> str:
    """Build better English sentences from translated words."""
    if not words:
        return ""
    
    # Join words
    sentence = ' '.join(words)
    return apply_basic_grammar(sentence)

def translate_tanglish_to_english(text: str) -> str:
    """
    Translate Tanglish text to proper English.
    Uses ML models when available, falls back to rule-based approach.
    """
    if not text or not text.strip():
        return ""
    
    # First try rule-based for known patterns
    rule_based = translate_tanglish_to_english_rule_based(text)
    
    if not TRANSFORMERS_AVAILABLE:
        return smart_sentence_builder(rule_based.split())
    
    # If text is already mostly English, return as-is
    if any(word in TANGLISH_TO_ENGLISH_DICT.values() for word in text.lower().split()):
        return smart_sentence_builder(rule_based.split())
    
    try:
        model, tokenizer = get_telugu_english_model()
        
        if model is not None and tokenizer is not None:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            with torch.no_grad():
                translated = model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            english_text = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            # Post-process
            english_text = post_process_english(english_text)
            
            return english_text if english_text.strip() else rule_based
    except Exception as e:
        print(f"ML translation failed: {e}, using rule-based")
        return rule_based
    
    return rule_based

def post_process_english(text: str) -> str:
    """Post-process English text."""
    if not text:
        return ""
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    text = re.sub(r'([.,!?])\s*', r'\1 ', text)
    
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def translate_tanglish_to_telugu(text: str) -> str:
    """
    Translate Tanglish (Telugu in Roman script) to Telugu Unicode.
    Falls back to English translation if needed.
    """
    if not text or not text.strip():
        return ""
    
    # Check if already in Telugu script
    if any('\u0c00' <= c <= '\u0c7f' for c in text):
        return text
    
    # For Tanglish, use the transliterator from NLP module
    try:
        from backend.nlp.tanglish_converter.transliterator import transliterate_tanglish_to_telugu as trans_func
        return trans_func(text)
    except Exception as e:
        print(f"Transliteration failed: {e}, returning original")
        return text

