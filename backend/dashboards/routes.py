from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import get_current_user_id, get_current_user_role
from topic_modeling.bertopic_service import topic_service as bertopic_service, clean_text
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
    
    if user_role.lower() != "general":
        raise HTTPException(status_code=403, detail="Access denied")
    
    translations_collection = db["translations"]
    topics_collection = db["topics"]
    
    # Get all translations for this user to compute complete metrics
    all_user_translations = list(
        translations_collection.find({"user_id": user_id})
        .sort("timestamp", -1)
    )
    
    # Recent translations for the history table (limit to 50 for bulk visibility)
    recent_translations = all_user_translations[:50]
    
    for trans in recent_translations:
        trans["_id"] = str(trans["_id"])
        if isinstance(trans["timestamp"], datetime):
            trans["timestamp"] = trans["timestamp"].isoformat()
    
    # Compute metrics from ALL user translations
    user_topics = []
    topic_counts = {}
    translation_timeline = []
    
    for trans in all_user_translations:
        # Topic statistics
        if trans.get("predicted_topic"):
            topic = trans["predicted_topic"]
            topic_name = topic.get("name", "Unknown")
            topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
            # Keep first 10 for the topics list
            if len(user_topics) < 10:
                user_topics.append(topic)
        
        # Timeline statistics
        timestamp = trans.get("timestamp")
        if timestamp:
            if isinstance(timestamp, datetime):
                date_str = timestamp.strftime("%Y-%m-%d")
            elif isinstance(timestamp, str):
                try:
                    date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%Y-%m-%d")
                except:
                    continue
            else:
                continue
                
            translation_timeline.append(date_str)
    
    # Aggregate timeline by date
    timeline_dict = Counter(translation_timeline)
    timeline_data = [{"date": k, "count": v} for k, v in sorted(timeline_dict.items())]
    
    # Get top 5 topics across ALL data
    top_topics = [{"keyword": name, "count": count} for name, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    # Calculate active days from ALL data
    active_days = len(timeline_dict)

    # Mock accuracy data based on user activity (varied but consistent)
    import random
    random.seed(user_id)
    accuracy_trend = []
    base_acc_translit = 85
    base_acc_trans = 80
    
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(7):
        accuracy_trend.append({
            "day": days_of_week[i],
            "transliteration": base_acc_translit + random.randint(-5, 5),
            "translation": base_acc_trans + random.randint(-5, 5)
        })

    return {
        "recent_translations": recent_translations,
        "top_topics": top_topics,
        "user_topics": user_topics,
        "translation_timeline": timeline_data[-7:] if timeline_data else [],
        "total_translations": len(all_user_translations),
        "active_days": active_days,
        "accuracy_trend": accuracy_trend
    }

@router.get("/researcher")
async def get_researcher_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role.lower() != "researcher":
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
async def get_analyst_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role.lower() != "analyst":
        raise HTTPException(status_code=403, detail="Access denied")
    
    topics_collection = db["topics"]
    translations_collection = db["translations"]
    users_collection = db["users"]
    
    # Get all topic documents (including analyst uploads)
    all_topics = list(topics_collection.find({}).sort("timestamp", -1).limit(100))
    
    topic_frequency = {}
    total_topics_count = 0
    pos_total = neg_total = neu_total = 0
    
    # NEW: Customer Insights & Feedback
    customer_insights = []
    
    # Process all topic documents
    for topic_result in all_topics:
        # Aggregated topic frequency
        for topic in topic_result.get("topics", []):
            topic_name = topic.get("name", "Unknown")
            count = topic.get("count", topic.get("frequency", 0))
            topic_frequency[topic_name] = topic_frequency.get(topic_name, 0) + count
            total_topics_count += count
            
        # Aggregated sentiment data
        sd = topic_result.get("sentiment_data", {})
        if sd:
            pos_total += sd.get("positive", 0)
            neg_total += sd.get("negative", 0)
            neu_total += sd.get("neutral", 0)
            
        # Extract insights from topic descriptions/keywords
        for topic in topic_result.get("topics", []):
            if topic.get("count", 0) > 5 or topic.get("frequency", 0) > 5:
                keywords = topic.get("keywords", [])
                customer_insights.append({
                    "topic": topic.get("name"),
                    "insight": f"High engagement detected in {topic.get('name')}. Key terms: {', '.join(keywords[:3])}",
                    "sentiment": "Positive" if pos_total > neg_total else "Mixed",
                    "timestamp": topic_result.get("timestamp").isoformat() if topic_result.get("timestamp") else None
                })
    
    # Default insights if none found
    if not customer_insights:
        customer_insights = [
            {"topic": "Service Quality", "insight": "Users frequently mention 'fast' and 'reliable' in recent translations.", "sentiment": "Positive", "timestamp": datetime.now().isoformat()},
            {"topic": "App Interface", "insight": "Feedback suggests a need for darker theme options in the dashboard.", "sentiment": "Mixed", "timestamp": datetime.now().isoformat()}
        ]

    # Trending topics (top 10)
    trending_topics = []
    if topic_frequency:
        sorted_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        trending_topics = [{"topic": name, "frequency": freq} for name, freq in sorted_topics]
    
    # Fallback sentiment if none exists
    if pos_total + neg_total + neu_total == 0:
        pos_total = neu_total = neg_total = 1
    
    sentiment_data = {
        "positive": pos_total,
        "neutral": neu_total,
        "negative": neg_total,
    }
    
    # Time-based trends (last 7 days)
    time_based_trends = []
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        date_str = date.strftime("%Y-%m-%d")
        # Count documents created on this date
        count = sum(1 for t in all_topics if t.get("timestamp") and date_str in str(t.get("timestamp")))
        time_based_trends.append({"date": date_str, "count": count})
    
    # Get users data
    all_users = list(users_collection.find({}, {"password": 0}).sort("created_at", -1).limit(100))
    users_data = []
    for user in all_users:
        uid = str(user["_id"])
        users_data.append({
            "id": uid,
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "role": user.get("role", "general"),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
        })
    
    # Calculate metrics
    total_analyst_records = sum(t.get("total_records", 0) for t in all_topics if t.get("source") == "analyst_upload")
    total_translations = translations_collection.count_documents({})
    
    # Activity Trends (Last 7 Days)
    activity_trends = []
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        date_str = date.strftime("%Y-%m-%d")
        
        # Count document activity for this day
        topic_uploads = sum(1 for t in all_topics if t.get("timestamp") and date_str in str(t.get("timestamp")))
        user_conversions = translations_collection.count_documents({
            "timestamp": {
                "$gte": datetime.combine(date, datetime.min.time()),
                "$lte": datetime.combine(date, datetime.max.time())
            }
        })
        
        activity_trends.append({
            "date": date.strftime("%a"), # e.g., Mon, Tue
            "uploads": topic_uploads,
            "conversions": user_conversions
        })

    return {
        "trending_topics": trending_topics,
        "sentiment_data": sentiment_data,
        "time_based_trends": time_based_trends,
        "activity_trends": activity_trends,
        "customer_insights": customer_insights[:5],
        "users_data": users_data,
        "total_users": len(all_users),
        "total_translations": total_translations + total_analyst_records,
        "avg_engagement": round((total_translations + total_analyst_records) / max(len(all_users), 1), 1),
        "total_topics": len(topic_frequency)
    }

@router.post("/analyst/upload-topics-csv")
async def upload_topics_csv(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    """
    Analyst Dashboard: Upload CSV with predefined topics and counts
    Format: topic_id, name, keywords, count
    """
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)
    
    if user_role.lower() != "analyst":
        raise HTTPException(status_code=403, detail="Only analyst users can upload topic CSV.")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
        
        # Process topics from CSV
        topics_data = []
        for idx, row in df.iterrows():
            try:
                topic_info = {
                    "topic_id": int(row.get("topic_id", 0)) if pd.notna(row.get("topic_id")) else idx,
                    "name": str(row.get("name", row.get("topic", "Unknown"))).strip(),
                    "keywords": [k.strip() for k in str(row.get("keywords", "")).split(",") if k.strip()] if pd.notna(row.get("keywords")) else [],
                    "count": int(row.get("count", 0)) if pd.notna(row.get("count")) else 0
                }
                topics_data.append(topic_info)
            except Exception:
                continue
        
        if not topics_data:
            raise HTTPException(status_code=400, detail="No valid topics found in CSV")
        
        topic_upload_data = {
            "user_id": user_id,
            "source": "csv_upload",
            "filename": file.filename,
            "topics": topics_data,
            "upload_count": len(topics_data),
            "timestamp": datetime.utcnow()
        }
        
        result = db["topics"].insert_one(topic_upload_data)
        
        return {
            "message": f"Successfully imported {len(topics_data)} topics from CSV",
            "topics_imported": len(topics_data),
            "document_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")


# ============= NEW ENDPOINT FOR SOCIAL MEDIA ANALYSIS =============

@router.post("/analyst/analyze-social-media")
async def analyze_social_media_csv(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    """
    Analyst Dashboard: Upload social media data and analyze topics.
    CSV format: user_id, text
    """
    try:
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        if not PANDAS_AVAILABLE:
            raise HTTPException(status_code=500, detail="pandas is required on server")
        
        user_id = get_current_user_id(credentials)
        user_role = get_current_user_role(credentials)
        
        if user_role.lower() != "analyst":
            raise HTTPException(status_code=403, detail="Only analysts can upload social media data")
        
        # Read the entire content into memory
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Try to parse CSV with multiple possible encodings
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(contents), encoding='latin1')
        
        # Normalize column names (lowercase and strip whitespace)
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Identify required columns with flexible naming
        text_col = next((c for c in ['text', 'content', 'message', 'tweet', 'tanglish_text'] if c in df.columns), None)
        user_col = next((c for c in ['user_id', 'user', 'userid', 'author'] if c in df.columns), None)
        time_col = next((c for c in ['timestamp', 'date', 'created_at', 'time'] if c in df.columns), None)
        
        if not text_col or not user_col:
            available_cols = ", ".join(df.columns.tolist())
            raise HTTPException(status_code=400, detail=f"CSV must have 'text' and 'user_id' columns. Found: {available_cols}")
        
        # Clean and Prepare Data
        df = df.dropna(subset=[text_col, user_col])
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV contains no valid data rows after cleaning")

        texts = df[text_col].astype(str).tolist()
        user_ids = df[user_col].astype(str).tolist()
        timestamps = df[time_col].astype(str).tolist() if time_col else None
        
        if len(texts) < 3: # Reduced requirement slightly for testing
            raise HTTPException(status_code=400, detail="Need at least 3 valid records for analysis")
            
        # 2. Run BERTopic Modeling (Async)
        import asyncio
        topic_results = await asyncio.to_thread(
            bertopic_service.run_topic_modeling,
            texts=texts,
            user_ids=user_ids,
            timestamps=timestamps
        )
        
        # 3. Simple Sentiment Analysis for Charts
        pos_count = sum(1 for t in texts if any(w in t.lower() for w in ['good', 'great', 'awesome', 'happy', 'love', 'nice', 'super']))
        neg_count = sum(1 for t in texts if any(w in t.lower() for w in ['bad', 'worst', 'hate', 'sad', 'angry', 'poor', 'waste']))
        neu_count = len(texts) - pos_count - neg_count
        
        # 4. Build Analysis Data
        analysis_data = {
            "analyst_id": user_id,
            "filename": file.filename,
            "total_records": len(texts),
            "source": "analyst_upload",
            "topics": topic_results.get("topics", []),
            "user_distributions": topic_results.get("user_distributions", {}),
            "user_entropy": topic_results.get("user_entropy", {}),
            "temporal_drift": topic_results.get("temporal_drift", {}),
            "coherence_score": topic_results.get("coherence_score", 0.0),
            "topic_evolution": topic_results.get("topic_evolution", {}),
            "sentiment_data": {
                "positive": pos_count,
                "neutral": neu_count,
                "negative": neg_count
            },
            "timestamp": datetime.utcnow()
        }
        
        # 5. Store in database
        topics_collection = db["topics"]
        result = topics_collection.insert_one(analysis_data)
        
        return {
            "message": "Upload and topic modeling successful",
            "analysis_id": str(result.inserted_id),
            "summary": {
                "total_records": len(texts),
                "topics_found": len(topic_results.get("topics", [])),
                "coherence": topic_results.get("coherence_score", 0.0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error processing CSV: {str(e)}")


# ============= HELPER FUNCTIONS FOR SENTIMENT & TOPIC ANALYSIS =============

def analyze_sentiment_simple(text: str) -> float:
    """Simple keyword-based sentiment analysis"""
    text_lower = text.lower()
    
    positive_words = ["good", "great", "excellent", "amazing", "love", "best", "awesome", "perfect", "great", "wonderful"]
    negative_words = ["bad", "terrible", "hate", "worst", "awful", "horrible", "poor", "sad", "angry"]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count + negative_count == 0:
        return 0.0
    
    sentiment = (positive_count - negative_count) / (positive_count + negative_count)
    return round(sentiment, 3)


def extract_keywords_simple(text: str) -> List[str]:
    """Extract simple keywords from text (non-stop words)"""
    stop_words = {"the", "a", "an", "and", "or", "but", "is", "are", "am", "be", "been", "have", "has", "do", "does", "did"}
    words = text.lower().split()
    keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
    return keywords[:5]  # Top 5 keywords


def classify_topic_simple(text: str) -> str:
    """Simple topic classification based on keywords"""
    text_lower = text.lower()
    
    topics = {
        "Technology": ["tech", "software", "ai", "coding", "programming", "computer", "internet", "online"],
        "Sports": ["cricket", "football", "sports", "game", "match", "player", "team", "score"],
        "Entertainment": ["movie", "film", "actor", "music", "song", "music", "concert", "show"],
        "Food": ["food", "restaurant", "recipe", "cooking", "eat", "drink", "cuisine", "dish"],
        "Politics": ["politics", "government", "election", "vote", "minister", "party", "parliament"],
        "Education": ["school", "college", "university", "student", "education", "learning", "study"],
        "Health": ["health", "medicine", "doctor", "illness", "disease", "hospital", "fitness"],
        "Business": ["business", "money", "market", "stock", "company", "trade", "profit"],
    }
    
    for topic, keywords in topics.items():
        for keyword in keywords:
            if keyword in text_lower:
                return topic
    
    return "General"