import re

# ── Telugu Phonetic Mapping (Comprehensive) ───────────────────────────────────

# Independent Vowels
VOWELS_INDEPENDENT = {
    'a': 'అ', 'aa': 'ఆ', 'A': 'ఆ',
    'i': 'ఇ', 'ii': 'ఈ', 'I': 'ఈ',
    'u': 'ఉ', 'uu': 'ఊ', 'U': 'ఊ',
    'e': 'ఎ', 'ee': 'ఏ', 'E': 'ఏ',
    'o': 'ఒ', 'oo': 'ఓ', 'O': 'ఓ',
    'ai': 'ఐ', 'au': 'ఔ', 'am': 'అం', 'ah': 'అః'
}

# Dependent Vowel Signs (Maatras)
VOWELS_DEPENDENT = {
    'a': '', 'aa': 'ా', 'A': 'ా',
    'i': 'ి', 'ii': 'ీ', 'I': 'ీ',
    'u': 'ు', 'uu': 'ూ', 'U': 'ూ',
    'e': 'ె', 'ee': 'ే', 'E': 'ే',
    'o': 'ొ', 'oo': 'ో', 'O': 'ో',
    'ai': 'ై', 'au': 'ౌ'
}

# Consonants (Phonetic)
CONSONANTS = {
    'k': 'క', 'kh': 'ఖ', 'g': 'గ', 'gh': 'ఘ', 'ng': 'ఙ',
    'ch': 'చ', 'chh': 'ఛ', 'j': 'జ', 'jh': 'ఝ', 'ny': 'ఞ',
    't': 'త', 'th': 'థ', 'd': 'ద', 'dh': 'ధ', 'n': 'న',
    'T': 'ట', 'Th': 'ఠ', 'D': 'డ', 'Dh': 'ఢ', 'N': 'ణ',
    'p': 'ప', 'ph': 'ఫ', 'b': 'బ', 'bh': 'భ', 'm': 'మ',
    'y': 'య', 'r': 'ర', 'l': 'ల', 'v': 'వ', 'w': 'వ',
    's': 'స', 'sh': 'శ', 'S': 'ష', 'h': 'హ', 'L': 'ళ', 'ksh': 'క్ష', 'tr': 'త్ర'
}

# Consonant Ligatures (Vattulu)
VATTULU = {
    'k': '్క', 'kh': '్ఖ', 'g': '్గ', 'gh': '్ఘ',
    'ch': '్చ', 'chh': '్ఛ', 'j': '్జ', 'jh': '్ఝ',
    't': '్త', 'th': '్థ', 'd': '్ద', 'dh': '్ధ', 'n': '్న',
    'T': '్ట', 'Th': '్ఠ', 'D': '్డ', 'Dh': '్ఢ', 'N': '్ణ',
    'p': '్ప', 'ph': '్ఫ', 'b': '్బ', 'bh': '్భ', 'm': '్మ',
    'y': '్య', 'r': '్ర', 'l': '్ల', 'v': '్వ', 'w': '్వ',
    's': '్స', 'sh': '్శ', 'S': '్ష', 'h': '్హ'
}

# Comprehensive Tanglish Dictionary
TANGLISH_DICT = {
    'nenu': 'నేను', 'nuvvu': 'నువ్వు', 'meeru': 'మీరు', 'miru': 'మీరు', 'manam': 'మనం',
    'ippudu': 'ఇప్పుడు', 'eppudu': 'ఎప్పుడు', 'ekkada': 'ఎక్కడ', 'enduku': 'ఎందుకు',
    'ela': 'ఎలా', 'enti': 'ఏంటి', 'emi': 'ఏమి', 'chala': 'చాలా', 'bagundi': 'బాగుంది',
    'ledu': 'లేదు', 'kaadu': 'కాదు', 'kavali': 'కావాలి', 'vastunna': 'వస్తున్నా',
    'vellu': 'వెళ్ళు', 'undhi': 'ఉంది', 'undi': 'ఉంది', 'vella': 'వెళ్ళా',
    'thinnava': 'తిన్నావా', 'paduko': 'పడుకో', 'ra': 'రా', 'po': 'పో',
    'movie': 'సినిమా', 'cinema': 'సినిమా', 'tech': 'టెక్', 'mobile': 'మొబైల్'
}

def phonetic_transliterate(word: str) -> str:
    """Robust phonetic transliteration of a single word."""
    word = word.lower().strip()
    if word in TANGLISH_DICT:
        return TANGLISH_DICT[word]
    
    res = ""
    i = 0
    n = len(word)
    
    while i < n:
        # 1. Handle vowel at start or after another vowel
        if i == 0 or word[i-1] in 'aeiou':
            found_vowel = False
            for length in [2, 1]:
                if i + length <= n:
                    chunk = word[i:i+length]
                    if chunk in VOWELS_INDEPENDENT:
                        res += VOWELS_INDEPENDENT[chunk]
                        i += length
                        found_vowel = True
                        break
            if found_vowel: continue

        # 2. Handle Consonant + Vowel clusters
        found_cluster = False
        for c_len in [3, 2, 1]:
            if i + c_len <= n:
                c_chunk = word[i:i+c_len]
                if c_chunk in CONSONANTS:
                    v_found = False
                    for v_len in [2, 1]:
                        if i + c_len + v_len <= n:
                            v_chunk = word[i+c_len:i+c_len+v_len]
                            if v_chunk in VOWELS_DEPENDENT:
                                res += CONSONANTS[c_chunk] + VOWELS_DEPENDENT[v_chunk]
                                i += c_len + v_len
                                v_found = True
                                break
                    
                    if v_found:
                        found_cluster = True
                        break
                    
                    # Double consonants
                    if i + c_len * 2 <= n and word[i+c_len:i+c_len*2] == c_chunk:
                        v_after_double = False
                        for v_len in [2, 1]:
                            if i + c_len * 2 + v_len <= n:
                                v_chunk = word[i+c_len*2:i+c_len*2+v_len]
                                if v_chunk in VOWELS_DEPENDENT:
                                    res += CONSONANTS[c_chunk] + VATTULU.get(c_chunk, '') + VOWELS_DEPENDENT[v_chunk]
                                    i += c_len * 2 + v_len
                                    v_after_double = True
                                    break
                        if v_after_double:
                            found_cluster = True
                            break

                    res += CONSONANTS[c_chunk] + '్'
                    i += c_len
                    found_cluster = True
                    break
        
        if not found_cluster:
            res += word[i]
            i += 1
            
    res = res.replace('్ ', ' ').replace('్.', '.').replace('్,', ',')
    if res.endswith('్'): res = res[:-1]
    return res

def transliterate_tanglish_to_telugu(text: str) -> str:
    if not text: return ""
    tokens = re.split(r'(\s+|[.,!?;:])', text)
    result = []
    for token in tokens:
        if not token.strip() or re.match(r'[.,!?;:]', token):
            result.append(token)
        else:
            result.append(phonetic_transliterate(token))
    return "".join(result)

def post_process_telugu(text: str) -> str:
    if not text: return ""
    text = re.sub(r'్(\s|[.,!?;:])', r'\1', text)
    text = re.sub(r'ము(\s|$)', r'ం\1', text)
    return text