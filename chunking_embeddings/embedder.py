"""
Embedding generator supporting OpenAI, Google Gemini, and local models.
"""

from typing import List, Optional
from config import config
from utils.logger import logger

# Check for OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Check for Google Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Check for SentenceTransformers (Local)
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class EmbeddingEngine:
    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.provider = (provider or config.EMBEDDING_PROVIDER).lower()
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        self.openai_client = None
        self.local_model = None
        self._setup()

    def _setup(self):
        if self.provider == "openai" and HAS_OPENAI and config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        elif self.provider == "gemini" and HAS_GEMINI and config.GEMINI_API_KEY and not config.GEMINI_API_KEY.startswith("AQ."):
            genai.configure(api_key=config.GEMINI_API_KEY)
        elif (self.provider in ["sentence_transformers", "local", "chroma_default", "huggingface"]) and HAS_SENTENCE_TRANSFORMERS:
            try:
                model_to_load = self.model_name if "/" in self.model_name or "minilm" in self.model_name.lower() or "bge" in self.model_name.lower() else "all-MiniLM-L6-v2"
                self.local_model = SentenceTransformer(model_to_load)
                logger.info(f"Loaded local SentenceTransformer model: {model_to_load}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to Chroma default.")

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generates embedding vectors for a list of texts."""
        if not texts:
            return []

        # 1. OpenAI Embeddings
        if self.provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=texts,
                    model=self.model_name
                )
                return [d.embedding for d in response.data]
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")

        # 2. Gemini Embeddings (only if standard Google AI Studio key)
        elif self.provider == "gemini" and HAS_GEMINI and config.GEMINI_API_KEY and not config.GEMINI_API_KEY.startswith("AQ."):
            try:
                embeddings = []
                for text in texts:
                    res = genai.embed_content(
                        model=self.model_name if "embedding" in self.model_name else "models/text-embedding-004",
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(res['embedding'])
                return embeddings
            except Exception as e:
                logger.error(f"Gemini embedding error: {e}")

        # 3. Local Sentence Transformers
        if self.local_model:
            try:
                raw_embeddings = self.local_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return [emb.tolist() for emb in raw_embeddings]
            except Exception as e:
                logger.warning(f"Local embedding failed: {e}")

        # 4. Chroma default handling
        logger.info(f"Delegating embeddings to ChromaDB default vectorizer for {len(texts)} texts.")
        return None

    def embed_query(self, query: str) -> Optional[List[float]]:
        """Generates embedding vector for a single query."""
        results = self.embed_texts([query])
        return results[0] if results else None


_embedder_instance: Optional[EmbeddingEngine] = None


def get_embedding_engine() -> EmbeddingEngine:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = EmbeddingEngine()
    return _embedder_instance
