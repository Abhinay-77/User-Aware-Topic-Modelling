import re

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: Transformers not installed. Using fallback translation.")

# Model cache
_telugu_to_english_model = None
_telugu_to_english_tokenizer = None

def get_telugu_english_model():
    """
    Load IndicTrans2 or NLLB model for Telugu to English translation.
    Falls back to available models if IndicTrans2 is not available.
    """
    global _telugu_to_english_model, _telugu_to_english_tokenizer
    
    if not TRANSFORMERS_AVAILABLE:
        return None, None
    
    if _telugu_to_english_model is None:
        try:
            # Try IndicTrans2 first (AI4Bharat)
            model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
            _telugu_to_english_tokenizer = AutoTokenizer.from_pretrained(model_name)
            _telugu_to_english_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception as e1:
            try:
                # Fallback to NLLB
                model_name = "facebook/nllb-200-distilled-600M"
                _telugu_to_english_tokenizer = AutoTokenizer.from_pretrained(model_name)
                _telugu_to_english_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            except Exception as e2:
                try:
                    # Fallback to Helsinki models
                    from transformers import MarianMTModel, MarianTokenizer
                    model_name = "Helsinki-NLP/opus-mt-te-en"
                    _telugu_to_english_tokenizer = MarianTokenizer.from_pretrained(model_name)
                    _telugu_to_english_model = MarianMTModel.from_pretrained(model_name)
                except Exception as e3:
                    print(f"Error loading translation models: {e1}, {e2}, {e3}")
                    _telugu_to_english_model = None
                    _telugu_to_english_tokenizer = None
    
    return _telugu_to_english_model, _telugu_to_english_tokenizer

def translate_telugu_to_english(telugu_text: str) -> str:
    """
    Translate Telugu text to grammatically correct English.
    If translation models are not available, use rule-based translation.
    """
    if not telugu_text or not telugu_text.strip():
        return ""
    
    # Check if text contains Telugu script
    has_telugu_script = bool(re.search(r'[\u0C00-\u0C7F]', telugu_text))
    
    # If no Telugu script, it might be Tanglish - use rule-based
    if not has_telugu_script:
        return translate_telugu_rule_based(telugu_text)
    
    model, tokenizer = get_telugu_english_model()
    
    if model is None or tokenizer is None:
        # Fallback: use rule-based translation for common phrases
        return translate_telugu_rule_based(telugu_text)
    
    try:
        # Prepare input
        inputs = tokenizer(
            telugu_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        # Generate translation
        with torch.no_grad():
            translated = model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
                early_stopping=True
            )
        
        # Decode result
        english_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        
        # Post-process
        english_text = post_process_english(english_text)
        
        return english_text
    
    except Exception as e:
        print(f"Translation error: {e}")
        return post_process_english_fallback(telugu_text)

def post_process_english(text: str) -> str:
    """
    Post-process English translation to improve grammar and readability.
    """
    if not text:
        return ""
    
    # Fix capitalization
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    # Fix spacing
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    text = re.sub(r'([.,!?])\s*', r'\1 ', text)
    
    # Fix common translation artifacts
    text = text.replace(' ,', ',')
    text = text.replace(' .', '.')
    text = text.replace(' !', '!')
    text = text.replace(' ?', '?')
    
    return text.strip()

def translate_telugu_rule_based(telugu_text: str) -> str:
    """
    Rule-based translation for common Telugu phrases when ML models are not available.
    """
    if not telugu_text:
        return ""
    
    text_lower = telugu_text.lower()
    
    # Common phrase translations (full phrases first)
    phrase_translations = {
        'office కి వెళ్ళను': 'I am going to the office',
        'office కు వెళ్ళను': 'I am going to the office',
        'office ki vellanu': 'I am going to the office',
        'office ku vellanu': 'I am going to the office',
        'office కి వస్తున్నాను': 'I am coming to the office',
        'office కు వస్తున్నాను': 'I am coming to the office',
        'నేను బాగా ఉన్నాను': 'I am fine',
        'నేను బాగుంది': 'I am good',
        'చాలా బాగుంది': 'Very good',
    }
    
    # Check for full phrase matches
    for phrase, translation in phrase_translations.items():
        if phrase.lower() in text_lower:
            return translation
    
    # Word-by-word translations
    word_translations = {
        'నేను': 'I', 'నువ్వు': 'you', 'మీరు': 'you',
        'వెళ్ళను': 'am going', 'వస్తున్నాను': 'am coming',
        'చేస్తున్నాను': 'am doing', 'ఉంది': 'is', 'ఉన్నాను': 'am',
        'లేదు': 'no', 'కాదు': 'not', 'బాగా': 'well', 'బాగుంది': 'good',
        'చాలా': 'very', 'ఇప్పుడు': 'now', 'తరువాత': 'later',
        'నాకు': 'to me', 'నీకు': 'to you', 'కి': 'to', 'కు': 'to',
        'లో': 'in', 'ల': 'in',
    }
    
    # Parse the sentence
    words = telugu_text.split()
    english_parts = []
    subject = None
    verb = None
    object_word = None
    location = None
    
    i = 0
    while i < len(words):
        word = words[i]
        word_clean = re.sub(r'[^\w\u0C00-\u0C7F]', '', word.lower())
        
        # Check if it's Telugu script
        if re.search(r'[\u0C00-\u0C7F]', word):
            if word_clean in word_translations:
                trans = word_translations[word_clean]
                if word_clean in ['నేను', 'నువ్వు', 'మీరు']:
                    subject = trans
                elif 'going' in trans or 'coming' in trans or 'doing' in trans:
                    verb = trans
                elif word_clean in ['కి', 'కు']:
                    # Next word is location
                    if i + 1 < len(words):
                        location = words[i + 1]
                        i += 1
                else:
                    object_word = trans
        else:
            # English word
            if word_clean in ['office', 'home', 'school', 'college', 'work']:
                location = word
            elif not subject:
                subject = 'I'  # Default subject
        
        i += 1
    
    # Construct sentence
    if subject and verb and location:
        english_text = f"{subject} {verb} to the {location}"
    elif subject and verb:
        english_text = f"{subject} {verb}"
    elif verb and location:
        english_text = f"I {verb} to the {location}"
    else:
        # Fallback: simple word replacement
        english_words = []
        for word in words:
            word_clean = re.sub(r'[^\w\u0C00-\u0C7F]', '', word.lower())
            if re.search(r'[\u0C00-\u0C7F]', word_clean):
                english_words.append(word_translations.get(word_clean, word))
            else:
                english_words.append(word)
        english_text = ' '.join(english_words)
    
    return post_process_english_fallback(english_text)

def post_process_english_fallback(text: str) -> str:
    """
    Fallback English processing when models are not available.
    """
    # Basic cleaning
    text = re.sub(r'\s+', ' ', text.strip())
    if text:
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    return text
