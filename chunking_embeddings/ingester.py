"""
Document Ingestion pipeline.
Loads source text file (The Alchemist), chunks it, generates embeddings, and saves into ChromaDB.
"""

import sys
import shutil
from pathlib import Path
from typing import Optional

from config import config
from utils.logger import logger
from database.vector_db import get_vector_db
from chunking_embeddings.chunker import TextChunker
from chunking_embeddings.embedder import get_embedding_engine


class DocumentIngester:
    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = get_embedding_engine()
        self.db = get_vector_db()

    def _resolve_document_path(self, filepath: Optional[str] = None) -> Path:
        """Finds the document and ensures it is placed inside data/ directory."""
        candidates = [
            Path(filepath) if filepath else None,
            Path(config.DOCUMENT_PATH),
            Path("./data/achemist.txt"),
            Path("./achemist.txt"),
        ]

        target_data_file = Path("./data/achemist.txt")

        for p in candidates:
            if p and p.exists() and p.is_file():
                if p.resolve() != target_data_file.resolve():
                    target_data_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(str(p), str(target_data_file))
                    logger.info(f"Copied {p} -> {target_data_file}")
                return target_data_file

        raise FileNotFoundError(f"Could not locate '{config.DOCUMENT_PATH}' or 'achemist.txt' in workspace.")

    def ingest(self, filepath: Optional[str] = None, reset: bool = False) -> int:
        """
        Executes full ingestion pipeline for the document.
        """
        doc_path = self._resolve_document_path(filepath)
        logger.info(f"Starting ingestion for document: {doc_path}")

        if reset:
            self.db.reset_collection()

        with open(doc_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        logger.info(f"Loaded document with {len(raw_text)} characters.")

        # 1. Chunk document
        chunk_items = self.chunker.chunk_documents(raw_text, source=doc_path.stem)
        if not chunk_items:
            logger.warning("No chunks generated from document.")
            return 0

        documents = [c["text"] for c in chunk_items]
        metadatas = [c["metadata"] for c in chunk_items]
        ids = [c["chunk_id"] for c in chunk_items]

        # 2. Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedder.embed_texts(documents)

        # 3. Save to Vector DB
        logger.info("Writing chunks to Vector Database...")
        self.db.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )

        total_count = self.db.count()
        logger.info(f"Ingestion complete. Vector DB collection now contains {total_count} total chunks.")
        return total_count


def run_ingestion():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest document into Vector DB.")
    parser.add_argument("--file", type=str, default=None, help="Path to input text file.")
    parser.add_argument("--reset", action="store_true", help="Reset existing collection before ingestion.")
    args = parser.parse_args()

    ingester = DocumentIngester()
    ingester.ingest(filepath=args.file, reset=args.reset)


if __name__ == "__main__":
    run_ingestion()
