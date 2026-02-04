"""
Configuration settings for the Citation Graph Visualizer backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # LLM Provider
    llm_provider: str = "bedrock"  # or "deepseek"
    
    # AWS Bedrock Settings
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    bedrock_model_id: str = "us.meta.llama3-3-70b-instruct-v1:0"
    bedrock_model_temperature: float = 0.7
    
    # DeepSeek Settings
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    
    # Semantic Scholar API
    semantic_scholar_api_key: Optional[str] = None
    
    # ArXiv API
    arxiv_api_base_url: str = "http://export.arxiv.org/api/query"
    
    # Application Settings
    max_papers_in_graph: int = 200
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
