from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    app_name: str = "Mencius Agent"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # LLM
    glm_api_key: str = ""
    
    # Vector DB
    vector_db_type: str = "qdrant"
    vector_db_url: str = "http://localhost:6333"
    vector_db_collection_name: str = "mencius"
    
    # Server
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    
    # Model
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
