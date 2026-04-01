"""
normalizer.py — IMPROVED v2
Changes:
  1. Expanded TANGLISH_DICT with 200+ common Telugu-Roman words
  2. Added normalize_spelling_variants() for common misspellings
  3. Improved elongation handling for Telugu-specific patterns
  4. normalize_spelling_variants called inside normalize_tanglish pipeline
  5. All original cleaning steps preserved
"""
import re
import unicodedata

# ── Tanglish dictionary: Telugu-Roman → English ───────────────────────────────
TANGLISH_DICT = {
    # Pronouns
    "nenu": "I", "naenu": "I", "nEnu": "I",
    "meeru": "you", "nuvvu": "you", "mee": "your",
    "memu": "we", "mana": "our", "vaadu": "he",
    "aame": "she", "vaallu": "they", "idi": "this",
    "adi": "that", "ikkade": "here", "akkade": "there",

    # Greetings & common expressions
    "namaskaram": "hello", "namasthe": "hello", "bayalu": "bye",
    "sari": "okay", "sare": "okay", "ante": "means",
    "kada": "right", "kadha": "right", "emo": "maybe",
    "enti": "what", "enduku": "why", "ekkada": "where",
    "ela": "how", "evaru": "who", "yem": "what",
    "please": "please", "thanks": "thanks", "thankyou": "thank you",

    # Common verbs
    "cheppadu": "he said", "cheppindi": "she said", "cheppanu": "I said",
    "cheppali": "should say", "cheppu": "tell",
    "vachadu": "he came", "vachindi": "she came", "vacchanu": "I came",
    "veltanu": "I will go", "veltunnanu": "I am going", "velladu": "he went",
    "chustunnanu": "I am watching", "chusa": "I watched", "chudali": "should watch",
    "tintunnanu": "I am eating", "tinna": "I ate", "tinali": "should eat",
    "padutunnanu": "I am sleeping", "padukunnanu": "I am sleeping",
    "chestunnanu": "I am doing", "chesanu": "I did", "chesadu": "he did",
    "istanu": "I will give", "ivvadu": "he gave", "teesukunnanu": "I took",
    "ostunnanu": "I am coming", "osthanu": "I will come",
    "pampanu": "I sent", "pampadu": "he sent",
    "nerchukunnanu": "I learned", "nerchukో": "learn",
    "chudandi": "please watch", "cheyandi": "please do",
    "randi": "please come", "vellandi": "please go",

    # Emotions & feelings
    "santhosham": "happiness", "santosham": "happiness",
    "dukham": "sadness", "dukkham": "sadness",
    "kopam": "anger", "kோpam": "anger",
    "bhayam": "fear", "prema": "love",
    "ishtam": "like", "aanandam": "joy",
    "virakti": "boredom", "ascharyam": "surprise",
    "sokkaga": "happily", "kastanga": "difficultly",
    "manchiga": "nicely", "chedduga": "badly",

    # Food
    "biryani": "biryani", "pulihora": "tamarind rice",
    "pesarattu": "green gram dosa", "idli": "idli",
    "dosa": "dosa", "upma": "upma", "chapati": "chapati",
    "roti": "roti", "rice": "rice", "annam": "rice",
    "pappu": "dal", "rasam": "rasam", "sambar": "sambar",
    "pickle": "pickle", "pachadi": "chutney",
    "halwa": "halwa", "laddu": "laddu", "pongal": "pongal",
    "vada": "vada", "bajji": "bajji", "bonda": "bonda",
    "tiffin": "tiffin", "coffee": "coffee", "tea": "tea",
    "lassi": "lassi", "buttermilk": "buttermilk",

    # Cricket
    "batting": "batting", "bowling": "bowling",
    "wicket": "wicket", "century": "century",
    "sixer": "six", "four": "four", "out": "out",
    "match": "match", "team": "team", "player": "player",
    "captain": "captain", "umpire": "umpire",
    "innings": "innings", "score": "score",
    "ipl": "IPL", "test": "test match", "odi": "ODI",

    # Movies & entertainment
    "hero": "hero", "heroine": "heroine", "villain": "villain",
    "comedy": "comedy", "climax": "climax", "interval": "interval",
    "trailer": "trailer", "release": "release", "ott": "OTT",
    "movie": "movie", "film": "film", "song": "song",
    "dance": "dance", "director": "director", "producer": "producer",
    "acting": "acting", "scene": "scene", "dialogue": "dialogue",
    "review": "review", "hit": "hit", "flop": "flop",

    # Family
    "amma": "mother", "nanna": "father", "akka": "elder sister",
    "anna": "elder brother", "chelli": "younger sister",
    "thammudu": "younger brother", "attha": "aunt",
    "babai": "uncle", "thatha": "grandfather", "ammamma": "grandmother",
    "pellam": "wife", "bhartha": "husband", "pillalu": "children",

    # Adjectives & descriptors
    "manchidi": "good", "manchodu": "good person",
    "cheddudi": "bad", "pedda": "big", "chinna": "small",
    "pakkaga": "exactly", "baaga": "very well",
    "chala": "very", "chala": "very much", "chaala": "very",
    "super": "super", "best": "best", "worst": "worst",
    "easy": "easy", "hard": "hard", "fast": "fast",
    "slow": "slow", "new": "new", "old": "old",
    "correct": "correct", "wrong": "wrong",

    # Time
    "ipudu": "now", "ippudu": "now", "roju": "today",
    "ninna": "yesterday", "repu": "tomorrow",
    "morning": "morning", "evening": "evening", "night": "night",
    "late": "late", "early": "early", "mundhu": "before",
    "tarvata": "after", "inkaa": "still", "already": "already",

    # Places
    "hyderabad": "Hyderabad", "hyd": "Hyderabad",
    "vizag": "Visakhapatnam", "vijayawada": "Vijayawada",
    "tirupati": "Tirupati", "warangal": "Warangal",
    "guntur": "Guntur", "nellore": "Nellore",
    "college": "college", "school": "school", "office": "office",
    "hospital": "hospital", "market": "market", "home": "home",
    "intlo": "at home", "outside": "outside",

    # Technology
    "mobile": "mobile", "phone": "phone", "laptop": "laptop",
    "internet": "internet", "wifi": "wifi", "app": "app",
    "software": "software", "coding": "coding", "data": "data",
    "online": "online", "offline": "offline", "download": "download",
    "upload": "upload", "share": "share", "post": "post",
    "ee": "this", "aa": "that",
    "ee": "this","ela": "how is","undhi": "is","undi": "is","vuundhi": "is",
    "baundhi": "is", "baundi": "is", "vuundi": "is",
    "tech": "technology", "technical": "technical",
    "software": "software", "hardware": "hardware",
    "coding": "coding", "programming": "programming",
    "ai": "artificial intelligence", "ml": "machine learning",
    "data": "data", "cloud": "cloud computing",
    "startup": "startup", "engineer": "engineer",
    "developer": "developer", "github": "github",
    "python": "python programming", "java": "java programming",
    "website": "website", "database": "database",
    "server": "server", "api": "API",
    "machine": "machine", "learning": "learning",
    "deep": "deep", "neural": "neural network",
    "model": "model", "training": "training",
    "chatgpt": "AI chatbot", "gpt": "AI model",
    # Common filler words
    "ra": "", "da": "", "di": "", "le": "",
    "ga": "like", "ki": "to", "lo": "in", "tho": "with",
    "nunchi": "from", "varaku": "until", "gurinchi": "about",
    "kosam": "for", "valla": "because of",

    # Extended verbs - past tense
    "choodanu": "I saw", "choodadam": "seeing", "chudanu": "I saw",
    "vinnanu": "I heard", "vinanu": "I heard", "vinnadu": "he heard",
    "tinnanu": "I ate", "tintanu": "I will eat", "tinadu": "he ate",
    "pillanu": "I called", "pilichadu": "he called", "pilichindi": "she called",
    "raksanu": "I wrote", "raasanu": "I wrote", "raasadu": "he wrote",
    "chadivanu": "I read", "chadivadu": "he read", "chadivindi": "she read",
    "nerchukunna": "learned", "nerchukuntanu": "I am learning",
    "aadanu": "I played", "aadadu": "he played", "aadindi": "she played",
    "paddanu": "I fell", "paddadu": "he fell",
    "niddurpoyanu": "I slept", "nidurpoyadu": "he slept",
    "tiraganu": "I walked", "tirugutunnanu": "I am walking",
    "pampanu": "I sent", "pampadu": "he sent", "pampindi": "she sent",
    "teesukonna": "I took", "teesukunnanu": "I am taking",
    "ichanu": "I gave", "ichadu": "he gave", "ichindi": "she gave",
    "adugutunnanu": "I am asking", "adugadu": "he asked",
    "chepputunnanu": "I am telling", "cheppukuntunnanu": "I am saying",
    "vachestunnanu": "I am coming", "vastunna": "coming",
    "velutunnanu": "I am going", "veltunna": "going",

    # Extended adjectives & sentiment
    "adhbutam": "amazing", "adbhutam": "amazing", "asadhyam": "impossible",
    "kastam": "difficult", "easy ga": "easily", "simple ga": "simply",
    "chinna vishayam": "small matter", "pedda vishayam": "big matter",
    "nijam": "truth", "abaddam": "lie", "correct": "correct",
    "wrong": "wrong", "perfect": "perfect", "awesome": "awesome",
    "brilliant": "brilliant", "terrible": "terrible", "horrible": "horrible",
    "boring": "boring", "interesting": "interesting", "beautiful": "beautiful",
    "ugly": "ugly", "clean": "clean", "dirty": "dirty",
    "fresh": "fresh", "old": "old", "new": "new",
    "heavy": "heavy", "light": "light", "strong": "strong", "weak": "weak",

    # Extended common nouns
    "vishayam": "matter", "samacharam": "news", "kotha": "new",
    "paata": "old", "manchi": "good", "chetta": "bad",
    "pedda": "big", "chinna": "small", "velalu": "fingers",
    "cheyi": "hand", "kalu": "leg", "kannu": "eye", "chevi": "ear",
    "nalupu": "black", "tella": "white", "erra": "red", "pachi": "green",
    "neeli": "blue", "pachi": "green", "pandu": "fruit",
    "chettu": "tree", "puvvu": "flower", "illu": "house",
    "veedhi": "street", "nadi": "river", "konda": "hill",
    "samudram": "ocean", "aakasham": "sky", "bhumi": "earth",
    "neerru": "water", "agni": "fire", "gaali": "air",

    # Time expressions
    "ippude": "right now", "konchamsepti": "after some time",
    "mundhu": "before", "tarvata": "after", "motham": "total",
    "prathi": "every", "anni": "all", "emi ledu": "nothing",
    "emi": "what", "emaina": "anything", "ela aina": "somehow",
    "enduku aina": "for some reason", "enni": "how many",
    "yekka": "how much", "chala time": "long time",
    "tvaraga": "quickly", "mellaga": "slowly",
    "gattiga": "loudly", "softga": "softly",

    # Social media specific
    "share cheyyi": "please share", "like cheyyi": "please like",
    "comment cheyyi": "please comment", "subscribe cheyyi": "please subscribe",
    "follow cheyyi": "please follow", "repost cheyyi": "please repost",
    "viral": "viral", "trending": "trending", "meme": "meme",
    "reel": "reel", "story": "story", "post chesanu": "I posted",
    "upload chesanu": "I uploaded", "download chesanu": "I downloaded",

    # Quality descriptors
    "bagundi": "good", "baagundi": "good", "bagundhi": "good",
    "ledu": "not there", "undi": "is there", "unnadi": "it is",
    "avutundi": "it will happen", "ayindi": "it happened",
    "kaadu": "no", "avadu": "not possible", "pakka": "sure",
    "definitely": "definitely", "maybe": "maybe",
    "baundhi": "is good",
    "baundi": "is good", 
    "vuundi": "is there",
    "undi": "is there",
    "undhi": "is there",
    "ledu": "is not",
    "kaadu": "is not",
    "avutundi": "is happening",
    "chesindi": "is done",
    "chesadu": "he did",
    "chestundi": "is doing",
}

# ── Spelling variant map: all variants → canonical form ───────────────────────
SPELLING_VARIANTS = {
    # nenu variants
    "naenu": "nenu", "nEnu": "nenu", "nenuu": "nenu",

    # bagundi variants
    "bagundhi": "bagundi", "baagundi": "bagundi", "baagundhi": "bagundi",
    "bagundee": "bagundi", "baagunna": "bagundi",
    "baaundhi": "baundhi",
    "baawundhi": "baundhi",
    "bavundhi": "baundhi",
    "bavundi": "baundhi",

    # chala variants
    "challa": "chala", "chalaa": "chala", "chalaaa": "chala",
    "chaala": "chala", "chaalaa": "chala",

    # super variants
    "suuper": "super", "suuperr": "super", "sooper": "super",

    # manchidi variants
    "manchidhi": "manchidi", "maanchidi": "manchidi", "manchii": "manchidi",

    # ante variants
    "antee": "ante", "anthe": "ante", "anthee": "ante",

    # undi variants
    "undhi": "undi", "unndi": "undi", "unndhi": "undi",

    # meeru variants
    "miru": "meeru", "miiru": "meeru", "meeruu": "meeru",

    # ela variants
    "yela": "ela", "yelaa": "ela", "elaa": "ela",

    # enti variants
    "yenti": "enti", "enthi": "enti", "yenthi": "enti",

    # sari variants
    "sare": "sari", "saree": "sari", "sariii": "sari",

    # ipudu variants
    "ippudu": "ipudu", "ipuduu": "ipudu", "ippuduu": "ipudu",

    # okka variants
    "okaa": "oka", "okkaa": "oka",

    # ishtam variants
    "ishttam": "ishtam", "ishtham": "ishtam",

    # coffee variants
    "kaafi": "coffee", "kaafee": "coffee",

    # biryani variants
    "biriyani": "biryani", "biriani": "biryani", "biriyan": "biryani",
}


def normalize_spelling_variants(text: str) -> str:
    """Map known spelling variants to their canonical Tanglish form."""
    words = text.split()
    normalized = []
    for word in words:
        normalized.append(SPELLING_VARIANTS.get(word, word))
    return ' '.join(normalized)


def apply_tanglish_dict(text: str) -> str:
    """Replace known Tanglish words with their English equivalents."""
    words = text.split()
    translated = []
    for word in words:
        # Look up in dict, keep original if not found
        replacement = TANGLISH_DICT.get(word, word)
        if replacement:  # skip empty replacements (filler words like 'ra', 'da')
            translated.append(replacement)
    return ' '.join(translated)


def normalize_tanglish(text: str) -> str:
    if not text:
        return ""

    # Passthrough if already Telugu script
    if any('\u0c00' <= c <= '\u0c7f' for c in text):
        return text.strip()

    text = text.lower().strip()

    # Remove URLs
    text = re.sub(r'http[s]?://\S+|www\.\S+', '', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)

    # Handle hashtags: keep the word (#Hyderabad → hyderabad)
    text = re.sub(r'#(\w+)', r'\1', text)

    # Remove @mentions
    text = re.sub(r'@\w+', '', text)

    # Remove emojis and other non-text symbols
    text = ''.join(
        c for c in text
        if not unicodedata.category(c).startswith('So')
        and not unicodedata.category(c).startswith('Cs')
    )

    # Normalize spelling variants BEFORE elongation (catches chalaa, baagundi etc.)
    text = normalize_spelling_variants(text)

    # Normalize elongated vowels — Telugu-specific: chalaa→chala, baagunna→bagunna
    text = re.sub(r'([aeiou])\1{2,}', r'\1\1', text)   # 3+ vowels → 2
    text = re.sub(r'([aeiou])\1{2,}', r'\1', text)         # 2 vowels → 1 (chaalaa→chala)

    # Normalize elongated consonants
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1{3,}', r'\1\1', text)
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1{2}', r'\1', text)

    # Normalize excessive punctuation
    text = re.sub(r'[!?]{2,}', '!', text)
    text = re.sub(r'\.{3,}', '...', text)

    # Remove special characters except basic punctuation and Telugu letters
    text = re.sub(r'[^\w\s\u0c00-\u0c7f.,!?\'\"-]', ' ', text)

    # Apply Tanglish dictionary translation
    text = apply_tanglish_dict(text)

    # Deduplicate consecutive repeated words
    words = text.split()
    deduped = [words[0]] if words else []
    for w in words[1:]:
        if w != deduped[-1]:
            deduped.append(w)
    text = ' '.join(deduped)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text