from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    app_name: str = "Mencius Agent"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # LLM
    glm_api_key: str = ""
    
    # Server
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    
    # Model
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
