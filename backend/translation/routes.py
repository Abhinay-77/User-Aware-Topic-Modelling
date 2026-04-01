from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import get_current_user_id, get_current_user_role
from topic_modeling.bertopic_service import topic_service as bertopic_service, clean_text
from nlp.tanglish_converter import convert_tanglish
from pymongo.database import Database
from datetime import datetime
from typing import List, Dict
import asyncio

router = APIRouter()
security = HTTPBearer()
# bertopic_service is now imported from topic_modeling.bertopic_service

@router.post("/translate")
async def translate_text(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    tanglish_text = request.get("text", "").strip()
    
    if not tanglish_text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    try:
        # Use advanced NLP pipeline - now returns a list
        conversion_results = await convert_tanglish(tanglish_text)
        
        processed_results = []
        # Optimization: Parallel topic prediction for each line
        async def process_topic(res):
            try:
                # Predict topic for each line individually
                text_for_modeling = res["english_text"] or res["original_text"]
                predicted_topic = await asyncio.to_thread(bertopic_service.predict_topic_for_text, text_for_modeling)
            except:
                predicted_topic = {"topic_id": -1, "name": "General", "keywords": [], "probability": 0.0}
            
            translation_data = {
                "user_id": user_id,
                "role": user_role,
                "tanglish_text": res["original_text"],
                "telugu_text": res["telugu_text"],
                "english_text": res["english_text"],
                "detected_language": res["detected_language"],
                "confidence_score": res["confidence_score"],
                "predicted_topic": predicted_topic,
                "timestamp": datetime.utcnow()
            }
            return translation_data

        # Run topic modeling tasks in parallel
        tasks = [process_topic(res) for res in conversion_results]
        processed_results = await asyncio.gather(*tasks)
        
        # Batch store in database for performance
        if processed_results:
            db["translations"].insert_many(processed_results)
            # Remove _id for JSON serialization compatibility in response
            for r in processed_results: r["_id"] = str(r["_id"])
        
        return {
            "message": "Translation successful",
            "translation": processed_results[0] if len(processed_results) == 1 else processed_results,
            "count": len(processed_results)
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

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
        # Use advanced NLP pipeline - now returns a list
        conversion_results = convert_tanglish(tanglish_text)
        
        final_results = []
        for res in conversion_results:
            # Store each line in database
            translation_data = {
                "user_id": user_id,
                "role": user_role,
                "tanglish_text": res["original_text"],
                "telugu_text": res["telugu_text"],
                "english_text": res["english_text"],
                "detected_language": res["detected_language"],
                "confidence_score": res["confidence_score"],
                "timestamp": datetime.utcnow()
            }
            
            translations_collection = db["translations"]
            db_result = translations_collection.insert_one(translation_data)
            translation_data["_id"] = str(db_result.inserted_id)
            final_results.append(translation_data)
        
        return {
            "message": "Tanglish conversion successful",
            "result": final_results[0] if len(final_results) == 1 else final_results
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
@router.post("/transliterate")
async def transliterate_single(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    text = request.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text field is required")
    
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    try:
        from nlp.tanglish_converter.pipeline import convert_tanglish as _pipeline_ct
        
        # 1. Transliteration & Translation (now returns a list)
        conversion_results = await _pipeline_ct(text)
        
        final_results = []
        db_entries = []
        
        for res in conversion_results:
            # 2. Cleaned Text for Topic Modeling
            english = res.get("english_text", res["original_text"])
            cleaned = clean_text(english)
            
            # 3. Topic Modeling
            topic_info = await asyncio.to_thread(bertopic_service.predict_topic_for_text, cleaned)
            
            # Merge all into one response item
            item = {
                "original_text": res["original_text"],
                "telugu_text": res["telugu_text"],
                "english_text": res["english_text"],
                "detected_language": res["detected_language"],
                "confidence_score": res["confidence_score"],
                "cleaned_text": cleaned,
                "topic_id": topic_info.get("topic_id", -1),
                "topic_name": topic_info.get("name", "General"),
                "topic_keywords": topic_info.get("keywords", []),
                "probability": topic_info.get("probability", 0.0)
            }
            final_results.append(item)
            
            # Prepare database entry for history
            db_entry = {
                "user_id": user_id,
                "role": user_role,
                "tanglish_text": res["original_text"],
                "telugu_text": res["telugu_text"],
                "english_text": res["english_text"],
                "detected_language": res["detected_language"],
                "confidence_score": res["confidence_score"],
                "predicted_topic": {
                    "topic_id": topic_info.get("topic_id", -1),
                    "name": topic_info.get("name", "General"),
                    "keywords": topic_info.get("keywords", []),
                    "probability": topic_info.get("probability", 0.0)
                },
                "timestamp": datetime.utcnow()
            }
            db_entries.append(db_entry)
        
        # Batch store in database for history
        if db_entries:
            db["translations"].insert_many(db_entries)
        
        # If only one line, return object, else return list for the frontend to handle
        return final_results[0] if len(final_results) == 1 else {"results": final_results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transliteration failed: {str(e)}")


@router.post("/transliterate-bulk")
async def transliterate_bulk(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    try:
        import pandas as pd
        import io as _io
        from nlp.tanglish_converter import convert_tanglish
        from fastapi.responses import Response
        
        contents = await file.read()
        df = pd.read_csv(_io.BytesIO(contents))
        text_col = next((c for c in ['text','statement','sentence','input','tanglish_text'] if c in df.columns), df.columns[0])
        
        # Parallel processing for speed
        async def process_row(idx, raw):
            try:
                # convert_tanglish now returns a list, we take the first item
                conversion_results = await convert_tanglish(raw)
                out = conversion_results[0]
                
                english = out.get("english_text", raw)
                cleaned = clean_text(english)
                topic_info = await asyncio.to_thread(bertopic_service.predict_topic_for_text, cleaned)
                
                result_item = {
                    "original": raw,
                    "telugu_script": out.get("telugu_text", raw),
                    "english_translation": english,
                    "cleaned_text": cleaned,
                    "topic_id": topic_info.get("topic_id", -1),
                    "topic_name": topic_info.get("name", "General"),
                    "topic_keywords": ", ".join(topic_info.get("keywords", [])),
                    "probability": topic_info.get("probability", 0.0),
                    "detected_language": out.get("detected_language", "unknown"),
                    "confidence": out.get("confidence_score", 0.0),
                }

                # Prepare for DB storage
                db_entry = {
                    "user_id": user_id,
                    "role": user_role,
                    "tanglish_text": raw,
                    "telugu_text": out.get("telugu_text", raw),
                    "english_text": english,
                    "detected_language": out.get("detected_language", "unknown"),
                    "confidence_score": out.get("confidence_score", 0.0),
                    "predicted_topic": {
                        "topic_id": topic_info.get("topic_id", -1),
                        "name": topic_info.get("name", "General"),
                        "keywords": topic_info.get("keywords", []),
                        "probability": topic_info.get("probability", 0.0)
                    },
                    "timestamp": datetime.utcnow()
                }
                
                return result_item, db_entry
            except Exception as e:
                err_item = {
                    "original": raw, "telugu_script": raw, "english_translation": raw,
                    "cleaned_text": raw, "topic_id": -1, "topic_name": "Error",
                    "topic_keywords": "", "probability": 0.0,
                    "detected_language": "error", "confidence": 0.0
                }
                return err_item, None

        tasks = [process_row(i, str(row[text_col]).strip()) for i, row in df.iterrows() if str(row[text_col]).strip()]
        combined_results = await asyncio.gather(*tasks)
        
        results = [r[0] for r in combined_results]
        db_entries = [r[1] for r in combined_results if r[1] is not None]
        
        # Store in database
        if db_entries:
            db["translations"].insert_many(db_entries)
        
        out_df = pd.DataFrame(results)
        output = _io.StringIO()
        out_df.to_csv(output, index=False)
        
        return Response(
            content=output.getvalue(), 
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transliteration_results.csv"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")
