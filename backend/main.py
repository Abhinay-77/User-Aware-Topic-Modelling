from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from auth.routes import router as auth_router
from translation.routes import router as translation_router
from topic_modeling.routes import router as topic_router
from dashboards.routes import router as dashboard_router
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="User-Aware BERTopic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(translation_router, prefix="/api/translation", tags=["translation"])
app.include_router(topic_router, prefix="/api/topic", tags=["topic"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
def root():
    return {"message": "User-Aware BERTopic API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Changed to 8001 as requested in frontend/src/services/api.js
    uvicorn.run(app, host="0.0.0.0", port=8001)
