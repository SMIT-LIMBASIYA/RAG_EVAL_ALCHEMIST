"""
Retrieval engine querying Vector Database.
"""

from typing import List, Dict, Any, Optional
from config import config
from utils.logger import logger
from database.vector_db import get_vector_db
from chunking_embeddings.embedder import get_embedding_engine


class Retriever:
    def __init__(self, top_k: Optional[int] = None):
        self.top_k = top_k or config.TOP_K
        self.db = get_vector_db()
        self.embedder = get_embedding_engine()

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """
        Retrieves the top-k most relevant text chunks for a given query string.
        """
        k = top_k or self.top_k
        query_emb = self.embedder.embed_query(query)

        results = self.db.query(
            query_text=query if query_emb is None else None,
            query_embeddings=query_emb,
            n_results=k
        )

        contexts = [r["document"] for r in results]
        logger.info(f"Retrieved {len(contexts)} contexts for query: '{query[:60]}...'")
        return contexts

    def retrieve_with_details(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves chunks with document IDs, scores, and metadata.
        """
        k = top_k or self.top_k
        query_emb = self.embedder.embed_query(query)

        return self.db.query(
            query_text=query if query_emb is None else None,
            query_embeddings=query_emb,
            n_results=k
        )


_retriever_instance: Optional[Retriever] = None


def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance
