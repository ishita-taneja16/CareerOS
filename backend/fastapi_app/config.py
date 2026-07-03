from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Career Copilot Engine"
    API_V1_STR: str = "/api/v1"
    
    # DB Configuration
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "aicopilot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379/1"
    
    # Chroma Vector DB
    CHROMA_HOST: str = "chroma"
    CHROMA_PORT: int = 8000
    
    # External APIs
    GEMINI_API_KEY: str = Field(default="")
    
    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # Options: gemini, ollama, huggingface
    LLM_MODEL: str = ""           # Optional override
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
