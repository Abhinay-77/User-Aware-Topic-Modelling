from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import get_current_user_id, get_current_user_role
from translation.translator import translate_tanglish_to_telugu, translate_tanglish_to_english
from topic_modeling.bertopic_service import BERTopicService
from nlp.tanglish_converter import convert_tanglish
from pymongo.database import Database
from datetime import datetime
from typing import List, Dict

router = APIRouter()
security = HTTPBearer()
bertopic_service = BERTopicService()

@router.post("/translate")
async def translate_text(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    tanglish_text = request.get("text", "")
    
    if not tanglish_text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    # Use advanced NLP pipeline for transliteration and translation
    try:
        conversion_result = convert_tanglish(tanglish_text)
        telugu_text = conversion_result.get("telugu_text", "")
        english_text = conversion_result.get("english_text", "")
        detected_language = conversion_result.get("detected_language", "Tanglish")
        confidence_score = conversion_result.get("confidence_score", 0.0)
        
        # If pipeline English translation is empty, use direct translator
        if not english_text or english_text.strip() == "":
            try:
                english_text = translate_tanglish_to_english(tanglish_text)
            except:
                pass
        
        # If Telugu transliteration is empty, use direct translator
        if not telugu_text or telugu_text.strip() == "":
            try:
                telugu_text = translate_tanglish_to_telugu(tanglish_text)
            except:
                pass
                
    except Exception as e:
        # Fallback to direct translators on error
        try:
            telugu_text = translate_tanglish_to_telugu(tanglish_text)
            english_text = translate_tanglish_to_english(tanglish_text)
            detected_language = "Tanglish"
            confidence_score = 0.5
        except Exception as e2:
            telugu_text = f"[Translation Error: {str(e2)}]"
            english_text = f"[Translation Error: {str(e2)}]"
            detected_language = "unknown"
            confidence_score = 0.0
    
    # Predict topic for the translated text
    try:
        predicted_topic = bertopic_service.predict_topic_for_text(tanglish_text, language="telugu")
    except Exception as e:
        predicted_topic = {"topic_id": -1, "name": "Unknown", "keywords": [], "probability": 0.0}
    
    translation_data = {
        "user_id": user_id,
        "role": user_role,
        "tanglish_text": tanglish_text,
        "telugu_text": telugu_text,
        "english_text": english_text,
        "detected_language": detected_language,
        "confidence_score": confidence_score,
        "predicted_topic": predicted_topic,
        "timestamp": datetime.utcnow()
    }
    
    translations_collection = db["translations"]
    result = translations_collection.insert_one(translation_data)
    translation_data["_id"] = str(result.inserted_id)
    
    return {
        "message": "Translation successful",
        "translation": translation_data
    }

@router.get("/history")
async def get_translation_history(
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    
    translations_collection = db["translations"]
    translations = list(
        translations_collection.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(limit)
    )
    
    for trans in translations:
        trans["_id"] = str(trans["_id"])
        trans["timestamp"] = trans["timestamp"].isoformat()
    
    return {
        "translations": translations,
        "count": len(translations)
    }

@router.post("/tanglish")
async def convert_tanglish_text(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    """
    Advanced Tanglish conversion endpoint using NLP pipeline.
    Converts Tanglish to Telugu script and grammatically correct English.
    """
    tanglish_text = request.get("text", "")
    
    if not tanglish_text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    try:
        # Use advanced NLP pipeline
        result = convert_tanglish(tanglish_text)
        
        # Store in database
        translation_data = {
            "user_id": user_id,
            "role": user_role,
            "tanglish_text": result["original_text"],
            "telugu_text": result["telugu_text"],
            "english_text": result["english_text"],
            "detected_language": result["detected_language"],
            "confidence_score": result["confidence_score"],
            "timestamp": datetime.utcnow()
        }
        
        translations_collection = db["translations"]
        db_result = translations_collection.insert_one(translation_data)
        translation_data["_id"] = str(db_result.inserted_id)
        
        return {
            "message": "Tanglish conversion successful",
            "result": translation_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
