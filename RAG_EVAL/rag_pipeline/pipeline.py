"""
End-to-End RAG Pipeline: Joins Retrieval + LLM Generation.
"""

from typing import Dict, Any, List, Optional
from utils.logger import logger
from RAG_EVAL.retrieval.retriever import get_retriever, Retriever
from RAG_EVAL.generator.generator import get_llm_generator, LLMGenerator


class RAGPipeline:
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        generator: Optional[LLMGenerator] = None
    ):
        self.retriever = retriever or get_retriever()
        self.generator = generator or get_llm_generator()

    def query(self, user_query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes end-to-end RAG:
        1. Query -> Retrieval -> Contexts
        2. Contexts + Query -> LLM -> Answer
        """
        logger.info(f"Processing RAG query: '{user_query}'")
        retrieved_contexts = self.retriever.retrieve(user_query, top_k=top_k)
        answer = self.generator.generate_response(user_query, retrieved_contexts)

        return {
            "query": user_query,
            "answer": answer,
            "retrieved_contexts": retrieved_contexts,
            "num_contexts": len(retrieved_contexts)
        }


_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
