from pymongo import MongoClient
from pymongo.database import Database
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bertopic_db")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    db: Database = client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")
except Exception as e:
    print(f"Warning: MongoDB connection failed: {e}")
    print("The application will start but database operations may fail.")
    print("Please ensure MongoDB is running and MONGO_URI is correct in .env file")
    client = MongoClient(MONGO_URI)
    db: Database = client[DATABASE_NAME]

def get_database():
    return db

def init_database():
    users_collection = db["users"]
    translations_collection = db["translations"]
    topics_collection = db["topics"]
    datasets_collection = db["datasets"]
    
    users_collection.create_index("email", unique=True)
    translations_collection.create_index("user_id")
    translations_collection.create_index("timestamp")
    topics_collection.create_index("user_id")
    topics_collection.create_index("dataset_id")
    
    return db
