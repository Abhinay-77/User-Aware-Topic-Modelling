from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database.connection import get_database
from database.models import User, UserRole
from auth.jwt_handler import create_access_token, verify_token
from auth.password_handler import hash_password, verify_password
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from typing import Optional
import secrets

router = APIRouter()
security = HTTPBearer()

class SignupRequest:
    def __init__(self, email: str, password: str, role: str, name: str):
        self.email = email
        self.password = password
        self.role = role
        self.name = name

class LoginRequest:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

@router.post("/signup")
async def signup(request: dict, db: Database = Depends(get_database)):
    email = request.get("email")
    password = request.get("password")
    role = request.get("role", "general")
    name = request.get("name", "")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    users_collection = db["users"]
    
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(password)
    
    user_data = {
        "email": email,
        "password": hashed_password,
        "role": role,
        "name": name,
        "created_at": datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)
    user_data.pop("password")
    
    token = create_access_token({"user_id": str(result.inserted_id), "email": email, "role": role})
    
    return {
        "message": "User created successfully",
        "user": user_data,
        "token": token
    }

@router.post("/login")
async def login(request: dict, db: Database = Depends(get_database)):
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    users_collection = db["users"]
    user = users_collection.find_one({"email": email})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    })
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user.get("name", "")
        }
    }

@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Database = Depends(get_database)
):
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    users_collection = db["users"]
    try:
        user = users_collection.find_one({"_id": ObjectId(payload["user_id"])})
    except:
        user = None
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "name": user.get("name", "")
    }

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["user_id"]

def get_current_user_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["role"]
