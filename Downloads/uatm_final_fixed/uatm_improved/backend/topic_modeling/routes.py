"""
topic_modeling/routes.py  —  IMPROVED
Changes:
  1. Passes user_id and timestamp columns to BERTopicService
  2. Returns user_distributions, user_entropy, temporal_drift, coherence in response
  3. New endpoint GET /user-profile/{user_id} for per-user topic profile
  4. New endpoint GET /drift/{user_id} for per-user temporal drift
  5. New endpoint GET /corpus-stats for dataset-level summary
  6. Better error messages
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import get_current_user_id, get_current_user_role
from topic_modeling.bertopic_service import BERTopicService
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from typing import List, Dict, Optional
import io

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

router = APIRouter()
security = HTTPBearer()
bertopic_service = BERTopicService()

# ── Run topic modeling ────────────────────────────────────────────────────────

@router.post("/run")
async def run_topic_modeling(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    user_id = get_current_user_id(credentials)
    user_role = get_current_user_role(credentials)

    if user_role != "researcher":
        raise HTTPException(status_code=403, detail="Only researchers can run topic modeling")

    if not PANDAS_AVAILABLE:
        raise HTTPException(status_code=500, detail="pandas required. pip install pandas")

    dataset_id = request.get("dataset_id")
    text_column = request.get("text_column", "text")
    user_column = request.get("user_column")        # NEW: optional user_id column in CSV
    time_column = request.get("time_column")        # NEW: optional timestamp column
    language = request.get("language", "english")
    num_topics = request.get("num_topics", 10)

    # Load dataset
    if dataset_id:
        try:
            dataset = db["datasets"].find_one({"_id": ObjectId(dataset_id), "user_id": user_id})
        except Exception:
            dataset = None
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        try:
            df = pd.read_csv(dataset["file_path"])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading dataset: {e}")
    else:
        try:
            df = pd.read_csv("data/social_media_samples.csv")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading default dataset: {e}")

    if text_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{text_column}' not found. Available: {list(df.columns)}")

    texts = df[text_column].dropna().astype(str).tolist()
    if len(texts) < 5:
        raise HTTPException(status_code=400, detail="Need at least 5 text documents")

    # Extract user_ids and timestamps if columns exist
    user_ids = None
    if user_column and user_column in df.columns:
        user_ids = df[user_column].dropna().astype(str).tolist()
        if len(user_ids) != len(texts):
            user_ids = None  # mismatched — skip

    timestamps = None
    if time_column and time_column in df.columns:
        timestamps = df[time_column].dropna().astype(str).tolist()
        if len(timestamps) != len(texts):
            timestamps = None

    try:
        results = bertopic_service.run_topic_modeling(
            texts=texts,
            language=language,
            num_topics=num_topics,
            user_ids=user_ids,
            timestamps=timestamps,
        )

        topic_data = {
            "user_id": user_id,
            "dataset_id": dataset_id,
            "language": language,
            "num_topics": num_topics,
            "topics": results["topics"],
            "topic_evolution": results["topic_evolution"],
            "keyword_distribution": results["keyword_distribution"],
            # NEW fields persisted to DB
            "user_distributions": results.get("user_distributions", {}),
            "user_entropy": results.get("user_entropy", {}),
            "temporal_drift": results.get("temporal_drift", {}),
            "coherence_score": results.get("coherence_score", -1.0),
            "outlier_count": results.get("outlier_count", 0),
            "topic_diversity": results.get("topic_diversity", 0.0),
            "timestamp": datetime.utcnow(),
        }

        result = db["topics"].insert_one(topic_data)
        topic_data["_id"] = str(result.inserted_id)

        return {"message": "Topic modeling completed", "results": topic_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic modeling error: {e}")


# ── NEW: per-user topic profile ───────────────────────────────────────────────

@router.get("/user-profile/{target_user_id}")
async def get_user_topic_profile(
    target_user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    """Return topic distribution and entropy for a specific user."""
    get_current_user_id(credentials)  # auth check

    # Find the most recent topic result that contains this user
    result = db["topics"].find_one(
        {f"user_distributions.{target_user_id}": {"$exists": True}},
        sort=[("timestamp", -1)],
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"No topic data for user '{target_user_id}'")

    dist = result["user_distributions"].get(target_user_id, {})
    entropy = result.get("user_entropy", {}).get(target_user_id, None)

    # Attach topic keywords
    topic_lookup = {str(t["topic_id"]): t["keywords"] for t in result.get("topics", [])}
    enriched = [
        {
            "topic_id": tid,
            "proportion": prop,
            "keywords": topic_lookup.get(tid, []),
        }
        for tid, prop in sorted(dist.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "user_id": target_user_id,
        "entropy": entropy,
        "top_topics": enriched[:10],
        "total_topics_engaged": len(enriched),
    }


# ── NEW: per-user temporal drift ──────────────────────────────────────────────

@router.get("/drift/{target_user_id}")
async def get_user_drift(
    target_user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    """Return temporal topic drift for a specific user."""
    get_current_user_id(credentials)

    result = db["topics"].find_one(
        {f"temporal_drift.{target_user_id}": {"$exists": True}},
        sort=[("timestamp", -1)],
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"No drift data for user '{target_user_id}'")

    drift_data = result["temporal_drift"].get(target_user_id, {})
    return {"user_id": target_user_id, **drift_data}


# ── NEW: corpus-level stats endpoint ─────────────────────────────────────────



@router.post("/run-lda-baseline")
async def run_lda_baseline(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    """Run LDA baseline for paper Table III comparison (Cv coherence, diversity)."""
    if get_current_user_role(credentials) != "researcher":
        raise HTTPException(status_code=403, detail="Researcher role required")
    text_column = request.get("text_column", "text")
    n_topics = int(request.get("n_topics", 10))
    n_iter = int(request.get("n_iterations", 500))
    dataset_id = request.get("dataset_id")
    user_id = get_current_user_id(credentials)
    if dataset_id:
        try:
            dataset = db["datasets"].find_one({"_id": ObjectId(dataset_id), "user_id": user_id})
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
            df = pd.read_csv(dataset["file_path"])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Dataset load error: {e}")
    else:
        import os
        default_path = os.path.join(os.path.dirname(__file__), "../../data/social_media_samples.csv")
        try:
            df = pd.read_csv(default_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Default dataset error: {e}")
    if text_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column not found. Available: {list(df.columns)}")
    texts = df[text_column].dropna().astype(str).tolist()
    if len(texts) < 5:
        raise HTTPException(status_code=400, detail="Need at least 5 documents")
    try:
        import sys, os as _os
        sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
        from baselines.lda_baseline import LDABaseline
        lda = LDABaseline(n_topics=n_topics, n_iterations=n_iter)
        result = lda.run(texts)
        result.pop("model", None)
        result.pop("topic_words", None)
        return {"message": "LDA baseline complete", "results": result}
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing packages (scikit-learn/gensim): {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LDA error: {str(e)}")

@router.get("/corpus-stats")
async def get_corpus_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    """Return aggregate statistics across all topic runs."""
    get_current_user_id(credentials)

    results = list(db["topics"].find({}).sort("timestamp", -1).limit(20))
    if not results:
        raise HTTPException(status_code=404, detail="No topic modeling results yet")

    latest = results[0]
    coherence_scores = [r.get("coherence_score", -1) for r in results if r.get("coherence_score", -1) > 0]

    # Aggregate entropy across all users
    all_entropy = {}
    for r in results:
        all_entropy.update(r.get("user_entropy", {}))

    entropy_values = list(all_entropy.values())
    mean_entropy = round(sum(entropy_values) / len(entropy_values), 4) if entropy_values else None

    return {
        "total_runs": len(results),
        "latest_run_id": str(latest["_id"]),
        "latest_topics": len(latest.get("topics", [])),
        "latest_coherence": latest.get("coherence_score"),
        "latest_diversity": latest.get("topic_diversity"),
        "latest_outlier_rate": round(
            latest.get("outlier_count", 0) / max(latest.get("total_documents", 1), 1), 4
        ),
        "mean_coherence_across_runs": round(sum(coherence_scores)/len(coherence_scores), 4) if coherence_scores else None,
        "total_profiled_users": len(all_entropy),
        "mean_user_entropy": mean_entropy,
    }


# ── Existing endpoints (unchanged) ───────────────────────────────────────────

@router.post("/upload-dataset")
async def upload_dataset(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    user_id = get_current_user_id(credentials)
    if get_current_user_role(credentials) != "researcher":
        raise HTTPException(status_code=403, detail="Only researchers can upload datasets")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    if not PANDAS_AVAILABLE:
        raise HTTPException(status_code=500, detail="pandas required")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {e}")

    import os
    os.makedirs("data/uploads", exist_ok=True)
    file_path = f"data/uploads/{user_id}_{datetime.utcnow().timestamp()}.csv"
    df.to_csv(file_path, index=False)

    dataset_data = {
        "user_id": user_id,
        "filename": file.filename,
        "file_path": file_path,
        "row_count": len(df),
        "columns": list(df.columns),
        "timestamp": datetime.utcnow(),
    }
    result = db["datasets"].insert_one(dataset_data)
    dataset_data["_id"] = str(result.inserted_id)
    return {"message": "Dataset uploaded successfully", "dataset": dataset_data}


@router.get("/datasets")
async def get_datasets(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    user_id = get_current_user_id(credentials)
    datasets = list(db["datasets"].find({"user_id": user_id}).sort("timestamp", -1))
    for d in datasets:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].isoformat()
    return {"datasets": datasets, "count": len(datasets)}


@router.get("/results")
async def get_topic_results(
    limit: int = 5,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    user_id = get_current_user_id(credentials)
    results = list(db["topics"].find({"user_id": user_id}).sort("timestamp", -1).limit(limit))
    for r in results:
        r["_id"] = str(r["_id"])
        r["timestamp"] = r["timestamp"].isoformat()
    return {"results": results, "count": len(results)}


@router.get("/download/{result_id}")
async def download_results(
    result_id: str,
    format: str = "csv",
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database),
):
    user_id = get_current_user_id(credentials)
    try:
        result = db["topics"].find_one({"_id": ObjectId(result_id), "user_id": user_id})
    except Exception:
        result = None
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    from fastapi.responses import Response
    import csv, json

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Topic ID", "Topic Name", "Keywords", "Count"])
        for topic in result["topics"]:
            writer.writerow([topic["topic_id"], topic["name"], ", ".join(topic["keywords"]), topic["count"]])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=topic_results_{result_id}.csv"},
        )
    else:
        return Response(
            content=json.dumps(result, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=topic_results_{result_id}.json"},
        )
