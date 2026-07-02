import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API & Hosting Config
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Database Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "voice_complaints")
    
    # Path for JSON fallback database
    DB_FALLBACK_PATH: str = os.getenv("DB_FALLBACK_PATH", "data/db_fallback.json")
    
    # Audio settings
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    
    class Config:
        env_file = ".env"

settings = Settings()
