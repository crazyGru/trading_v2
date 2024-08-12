import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb+srv://admin:trustkmp123@cluster0.celqdib.mongodb.net")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "trading")

settings = Settings()
