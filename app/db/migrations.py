from pymongo import MongoClient
from app.core.config import settings

def run_migrations():
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Example migration: Adding a new field to existing documents
    db.users.update_many({}, {"$set": {"new_field": "default_value"}})

if __name__ == "__main__":
    run_migrations()
