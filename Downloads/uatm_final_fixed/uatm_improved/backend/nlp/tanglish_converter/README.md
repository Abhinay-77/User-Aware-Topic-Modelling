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

## Dependencies

- transformers (optional, falls back gracefully)
- torch (optional, required by transformers)

The module works without ML dependencies but provides better results with them installed.
