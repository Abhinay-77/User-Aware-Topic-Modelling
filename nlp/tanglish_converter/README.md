# Tanglish Converter Module

Production-ready NLP pipeline for converting Tanglish (Telugu written in English letters) to proper Telugu script and grammatically correct English.

## Usage

```python
from nlp.tanglish_converter import convert_tanglish

result = convert_tanglish("office ki vellanu")
# Returns:
# {
#     "original_text": "office ki vellanu",
#     "telugu_text": "ఆఫీస్ కి వెళ్ళను",
#     "english_text": "I am going to the office",
#     "detected_language": "Tanglish",
#     "confidence_score": 0.85
# }
```

## API Endpoint

POST `/api/translation/tanglish`

Request:
```json
{
  "text": "office ki vellanu"
}
```

Response:
```json
{
  "message": "Tanglish conversion successful",
  "result": {
    "original_text": "office ki vellanu",
    "telugu_text": "ఆఫీస్ కి వెళ్ళను",
    "english_text": "I am going to the office",
    "detected_language": "Tanglish",
    "confidence_score": 0.85,
    "_id": "...",
    "user_id": "...",
    "timestamp": "..."
  }
}
```

## Pipeline Steps

1. **Normalization**: Cleans and normalizes input text
2. **Language Detection**: Detects code-mixing and language
3. **Transliteration**: Converts Tanglish to Telugu script
4. **Post-processing**: Improves Telugu grammar
5. **Translation**: Translates Telugu to English

## High-Level Model Support (NEW)

This module now supports **LLM-based transliteration and translation** for maximum accuracy. To enable:

1. Obtain a **Gemini API Key** from Google AI Studio.
2. Add it to your `.env` file: `GEMINI_API_KEY=your_key_here`
3. The pipeline will automatically use Gemini for processing, providing state-of-the-art results for complex Telugu words and ligatures.

## Local Phonetic Engine

If no LLM API key is provided, the module uses a robust **Syllable-Aware Phonetic Engine** that covers:
- All independent vowels and dependent maatras.
- All consonants including aspirated forms.
- Consonant ligatures (vattulu) for words like "nuvvu", "thinnava".
- Dictionary-based high-accuracy mapping for common words.
