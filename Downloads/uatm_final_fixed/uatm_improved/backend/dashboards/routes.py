from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import get_current_user_id, get_current_user_role
from pymongo.database import Database
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict
import json
import io

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

router = APIRouter()
security = HTTPBearer()

@router.get("/user")
async def get_user_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role != "general":
        raise HTTPException(status_code=403, detail="Access denied")
    
    translations_collection = db["translations"]
    topics_collection = db["topics"]
    
    recent_translations = list(
        translations_collection.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(10)
    )
    
    for trans in recent_translations:
        trans["_id"] = str(trans["_id"])
        trans["timestamp"] = trans["timestamp"].isoformat()
    
    all_topics = list(topics_collection.find({}).sort("timestamp", -1).limit(50))
    
    # Get topics from user's translations
    user_topics = []
    topic_counts = {}
    translation_timeline = []
    
    for trans in recent_translations:
        if trans.get("predicted_topic"):
            topic = trans["predicted_topic"]
            topic_name = topic.get("name", "Unknown")
            topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
            user_topics.append(topic)
        
        # Build timeline data
        timestamp = trans.get("timestamp")
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    date_obj = timestamp
                translation_timeline.append({
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "count": 1
                })
            except:
                pass
    
    # Aggregate timeline by date
    timeline_dict = {}
    for item in translation_timeline:
        date = item["date"]
        timeline_dict[date] = timeline_dict.get(date, 0) + 1
    
    timeline_data = [{"date": k, "count": v} for k, v in sorted(timeline_dict.items())]
    
    # Get top topics
    top_topics = [{"keyword": name, "count": count} for name, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    return {
        "recent_translations": recent_translations,
        "top_topics": top_topics,
        "user_topics": user_topics[:10],
        "translation_timeline": timeline_data[-7:] if timeline_data else [],
        "total_translations": len(recent_translations)
    }

@router.get("/researcher")
async def get_researcher_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role != "researcher":
        raise HTTPException(status_code=403, detail="Access denied")
    
    topics_collection = db["topics"]
    datasets_collection = db["datasets"]
    
    recent_results = list(
        topics_collection.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(5)
    )
    
    datasets = list(
        datasets_collection.find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(10)
    )
    
    for result in recent_results:
        result["_id"] = str(result["_id"])
        result["timestamp"] = result["timestamp"].isoformat()
    
    for dataset in datasets:
        dataset["_id"] = str(dataset["_id"])
        dataset["timestamp"] = dataset["timestamp"].isoformat()
    
    latest_result = recent_results[0] if recent_results else None
    
    return {
        "recent_results": recent_results,
        "datasets": datasets,
        "latest_result": latest_result
    }

@router.get("/business")
async def get_business_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role != "business":
        raise HTTPException(status_code=403, detail="Access denied")
    
    topics_collection = db["topics"]
    translations_collection = db["translations"]
    users_collection = db["users"]
    
    all_topics = list(topics_collection.find({}).sort("timestamp", -1).limit(100))
    
    topic_frequency = {}
    trending_topics = []
    
    for topic_result in all_topics:
        for topic in topic_result.get("topics", []):
            topic_name = topic.get("name", "Unknown")
            count = topic.get("count", 0)
            topic_frequency[topic_name] = topic_frequency.get(topic_name, 0) + count
    
    sorted_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    trending_topics = [{"topic": name, "frequency": freq} for name, freq in sorted_topics]
    
    sentiment_data = {
        "positive": len([t for t in all_topics if hash(str(t)) % 3 == 0]),
        "neutral": len([t for t in all_topics if hash(str(t)) % 3 == 1]),
        "negative": len([t for t in all_topics if hash(str(t)) % 3 == 2])
    }
    
    time_based_trends = []
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        date_str = date.strftime("%Y-%m-%d")
        count = len([t for t in all_topics if t.get("timestamp") and date_str in str(t.get("timestamp"))])
        time_based_trends.append({"date": date_str, "count": count})
    
    recent_translations = list(
        translations_collection.find({})
        .sort("timestamp", -1)
        .limit(20)
    )
    
    consumer_insights = []
    for trans in recent_translations[:5]:
        consumer_insights.append({
            "text": trans.get("tanglish_text", "")[:50] + "...",
            "timestamp": trans.get("timestamp").isoformat() if trans.get("timestamp") else None,
            "sentiment": ["positive", "neutral", "negative"][hash(str(trans)) % 3]
        })
    
    # Get users data
    all_users = list(users_collection.find({}, {"password": 0}).sort("created_at", -1).limit(100))
    users_data = []
    for user in all_users:
        user_id_str = str(user["_id"])
        user_translations = translations_collection.count_documents({"user_id": user_id_str})
        user_topics_count = topics_collection.count_documents({"user_id": user_id_str})
        
        users_data.append({
            "id": user_id_str,
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "role": user.get("role", "general"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "translations_count": user_translations,
            "topics_count": user_topics_count
        })
    
    # User activity over time
    user_activity = {}
    for trans in recent_translations:
        user_id_trans = trans.get("user_id")
        if user_id_trans:
            timestamp = trans.get("timestamp")
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        date_obj = timestamp
                    date_str = date_obj.strftime("%Y-%m-%d")
                    user_activity[date_str] = user_activity.get(date_str, 0) + 1
                except:
                    pass
    
    activity_timeline = [{"date": k, "count": v} for k, v in sorted(user_activity.items())]
    
    return {
        "trending_topics": trending_topics,
        "topic_frequency": topic_frequency,
        "sentiment_data": sentiment_data,
        "time_based_trends": time_based_trends,
        "consumer_insights": consumer_insights,
        "users_data": users_data,
        "user_activity": activity_timeline[-7:] if activity_timeline else [],
        "total_users": len(users_data),
        "total_translations": len(recent_translations)
    }

@router.post("/business/upload-topics-csv")
async def upload_topics_csv(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role != "business":
        raise HTTPException(status_code=403, detail="Only business users can upload topic CSV")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    if not PANDAS_AVAILABLE:
        raise HTTPException(status_code=500, detail="pandas is required for CSV processing")
    
    contents = await file.read()
    
    try:
        df = pd.read_csv(io.BytesIO(contents))
        
        # Process topics from CSV (expecting columns: topic_id, name, keywords, count)
        topics_collection = db["topics"]
        topics_imported = []
        
        for _, row in df.iterrows():
            topic_data = {
                "user_id": user_id,
                "source": "csv_upload",
                "topics": [{
                    "topic_id": int(row.get("topic_id", 0)),
                    "name": str(row.get("name", "Unknown")),
                    "keywords": str(row.get("keywords", "")).split(",") if pd.notna(row.get("keywords")) else [],
                    "count": int(row.get("count", 0))
                }],
                "timestamp": datetime.utcnow()
            }
            result = topics_collection.insert_one(topic_data)
            topics_imported.append(str(result.inserted_id))
        
        return {
            "message": f"Successfully imported {len(topics_imported)} topics from CSV",
            "topics_imported": len(topics_imported),
            "ids": topics_imported
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
