"""
Global Configuration module for RAG Evaluation system.
Loads settings from .env with fallback defaults using Pydantic Settings.
"""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    COHERE_API_KEY: Optional[str] = Field(default=None)

    # Model Providers & High Quality Selection
    LLM_PROVIDER: str = Field(default="openai")  # 'openai', 'gemini', 'groq', 'anthropic'
    LLM_MODEL_NAME: str = Field(default="gpt-4o-mini")  # e.g., 'gpt-4o', 'gemini-1.5-pro', 'llama-3.3-70b-versatile'
    LLM_TEMPERATURE: float = Field(default=0.0)

    # Embedding Model (State of the art)
    EMBEDDING_PROVIDER: str = Field(default="openai")  # 'openai', 'gemini', 'chroma_default'
    EMBEDDING_MODEL_NAME: str = Field(default="text-embedding-3-small")  # or 'text-embedding-3-large', 'models/text-embedding-004'

    # Evaluation LLM Judge Model
    EVAL_JUDGE_MODEL: str = Field(default="gpt-4o-mini")  # 'gpt-4o', 'gpt-4o-mini'

    # Vector Database
    VECTOR_STORE_TYPE: str = Field(default="chroma_local")
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db")
    CHROMA_COLLECTION_NAME: str = Field(default="alchemist_knowledge_base")
    CHROMA_HOST: str = Field(default="localhost")
    CHROMA_PORT: int = Field(default=8000)
    CHROMA_AUTH_TOKEN: Optional[str] = Field(default=None)

    # Chunking & Document Ingestion (Optimized for The Alchemist)
    DOCUMENT_PATH: str = Field(default="./data/achemist.txt")
    CHUNK_SIZE: int = Field(default=600)
    CHUNK_OVERLAP: int = Field(default=100)

    # Retrieval
    TOP_K: int = Field(default=4)
    RETRIEVAL_METRIC: str = Field(default="cosine")

    # DeepEval Metric Thresholds
    RETRIEVAL_RECALL_THRESHOLD: float = Field(default=0.70)
    RETRIEVAL_PRECISION_THRESHOLD: float = Field(default=0.70)
    FAITHFULNESS_THRESHOLD: float = Field(default=0.70)
    ANSWER_RELEVANCY_THRESHOLD: float = Field(default=0.70)
    CONTEXT_RELEVANCY_THRESHOLD: float = Field(default=0.70)

    # File Paths & Reporting
    GOLDEN_RETRIEVAL_PATH: str = Field(default="./data/golden_retrieval.json")
    GOLDEN_GENERATOR_PATH: str = Field(default="./data/golden_generator.json")
    GOLDEN_PIPELINE_PATH: str = Field(default="./data/golden_rag_pipeline.json")
    ANALYSIS_OUTPUT_DIR: str = Field(default="./analyses")
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def persist_path(self) -> Path:
        p = Path(self.CHROMA_PERSIST_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir_path(self) -> Path:
        p = Path(self.ANALYSIS_OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p


# Global Singleton Config Instance
config = AppConfig()
