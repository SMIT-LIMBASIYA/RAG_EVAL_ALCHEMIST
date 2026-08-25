"""
Text splitting and chunking manager.
Supports RecursiveCharacterTextSplitter with customizable chunk size and overlap.
"""

from typing import List, Dict, Any
from config import config
from utils.logger import logger

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    HAS_LANGCHAIN_SPLITTERS = True
except ImportError:
    HAS_LANGCHAIN_SPLITTERS = False


class TextChunker:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

        if HAS_LANGCHAIN_SPLITTERS:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        else:
            self.splitter = None

    def split_text(self, text: str) -> List[str]:
        """Splits raw text into overlapping chunks."""
        if self.splitter:
            chunks = self.splitter.split_text(text)
        else:
            # Fallback simple sliding window
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                if end == len(text):
                    break
                start += max(1, self.chunk_size - self.chunk_overlap)

        # Filter out empty or whitespace-only chunks
        clean_chunks = [c.strip() for c in chunks if len(c.strip()) > 20]
        logger.info(f"Chunked text into {len(clean_chunks)} segments (size={self.chunk_size}, overlap={self.chunk_overlap}).")
        return clean_chunks

    def chunk_documents(self, text: str, source: str = "book") -> List[Dict[str, Any]]:
        """Splits text and packages each chunk with index metadata."""
        raw_chunks = self.split_text(text)
        chunk_dicts = []
        for idx, chunk in enumerate(raw_chunks):
            chunk_dicts.append({
                "chunk_id": f"{source}_chunk_{idx}",
                "text": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": idx,
                    "char_count": len(chunk)
                }
            })
        return chunk_dicts
