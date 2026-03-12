from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    GENERAL = "general"
    RESEARCHER = "researcher"
    BUSINESS = "business"

class User(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    name: str
    created_at: Optional[datetime] = None

class Translation(BaseModel):
    user_id: str
    role: str
    tanglish_text: str
    telugu_text: str
    english_text: str
    timestamp: datetime

class TopicModel(BaseModel):
    topic_id: int
    keywords: List[str]
    count: int
    name: str

class TopicModelingRequest(BaseModel):
    dataset_id: Optional[str] = None
    text_column: str = "text"
    language: str = "telugu"
    num_topics: int = 10

class TopicModelingResponse(BaseModel):
    topics: List[TopicModel]
    topic_evolution: Dict[str, Any]
    keyword_distribution: Dict[str, int]

class DashboardData(BaseModel):
    recent_translations: List[Dict[str, Any]]
    top_topics: List[Dict[str, Any]]
    topic_frequency: Dict[str, int]
    sentiment_data: Optional[Dict[str, Any]] = None
