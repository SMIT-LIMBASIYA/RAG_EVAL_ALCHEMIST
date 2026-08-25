"""
ChromaDB Vector Database manager for document storage, persistence, and similarity search.
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from config import config
from utils.logger import logger

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("chromadb is not installed. Using local fallback vector database.")


class VectorDBManager:
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.persist_directory = persist_directory or config.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.client = None
        self.collection = None
        self._fallback_store = []  # For fallback when chromadb is not available

        self._initialize_client()

    def _initialize_client(self):
        """Initializes persistent ChromaDB client or in-memory fallback."""
        if HAS_CHROMADB:
            try:
                Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=self.persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": config.RETRIEVAL_METRIC}
                )
                logger.info(f"Connected to ChromaDB collection '{self.collection_name}' at '{self.persist_directory}'")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB PersistentClient: {e}. Falling back to memory.")
                self.client = None
        else:
            logger.info("ChromaDB not found in environment, running with fallback vector store.")

    def reset_collection(self):
        """Deletes and recreates the collection."""
        if HAS_CHROMADB and self.client:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": config.RETRIEVAL_METRIC}
            )
            logger.info(f"Reset collection '{self.collection_name}'.")
        self._fallback_store = []

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """Adds text documents and their embeddings to the vector store."""
        if not ids:
            ids = [f"doc_{i}" for i in range(len(documents))]
        if not metadatas:
            metadatas = [{} for _ in documents]

        if HAS_CHROMADB and self.collection:
            kwargs = {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids,
            }
            if embeddings is not None:
                kwargs["embeddings"] = embeddings
            self.collection.add(**kwargs)
            logger.info(f"Added {len(documents)} documents to ChromaDB collection '{self.collection_name}'.")
        else:
            for doc, meta, doc_id, emb in zip(documents, metadatas, ids, embeddings or [None]*len(documents)):
                self._fallback_store.append({
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta,
                    "embedding": emb
                })
            logger.info(f"Added {len(documents)} documents to in-memory fallback store.")

    def query(
        self,
        query_text: Optional[str] = None,
        query_embeddings: Optional[List[float]] = None,
        n_results: int = 4
    ) -> List[Dict[str, Any]]:
        """Queries the vector database and returns matching document chunks."""
        results = []
        if HAS_CHROMADB and self.collection:
            kwargs = {"n_results": n_results}
            if query_embeddings is not None:
                kwargs["query_embeddings"] = [query_embeddings]
            elif query_text:
                kwargs["query_texts"] = [query_text]

            res = self.collection.query(**kwargs)
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            ids = res.get("ids", [[]])[0]
            distances = res.get("distances", [[]])[0] if "distances" in res else [None] * len(docs)

            for d, m, i, dist in zip(docs, metas, ids, distances):
                results.append({
                    "id": i,
                    "document": d,
                    "metadata": m,
                    "distance": dist
                })
        else:
            # Fallback simple keyword match
            q_lower = (query_text or "").lower()
            sorted_docs = sorted(
                self._fallback_store,
                key=lambda x: sum(1 for word in q_lower.split() if word in x["document"].lower()),
                reverse=True
            )
            for item in sorted_docs[:n_results]:
                results.append({
                    "id": item["id"],
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "distance": 0.0
                })

        return results

    def count(self) -> int:
        """Returns the total number of documents indexed."""
        if HAS_CHROMADB and self.collection:
            return self.collection.count()
        return len(self._fallback_store)


_vector_db_instance: Optional[VectorDBManager] = None


def get_vector_db() -> VectorDBManager:
    """Returns singleton VectorDBManager instance."""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDBManager()
    return _vector_db_instance
