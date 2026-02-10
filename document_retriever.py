"""
Document Retriever - Extract relevant context from documents
Uses simple but effective keyword and text-based matching
"""

from typing import List


class DocumentRetriever:
    """Retrieve relevant document chunks based on queries."""

    def __init__(self, doc_text: str, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize the retriever with document text.

        Args:
            doc_text: Full document text
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
        """
        self.doc_text = doc_text
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks = self._create_chunks()

    def _create_chunks(self) -> List[str]:
        """Split document into overlapping chunks."""
        chunks = []
        for i in range(0, len(self.doc_text), self.chunk_size - self.overlap):
            chunk = self.doc_text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks if chunks else [self.doc_text]

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve most relevant chunks for a query.

        Args:
            query: User's question
            top_k: Number of top results to return

        Returns:
            Concatenated relevant text chunks
        """
        # Simple keyword-based relevance scoring
        query_words = set(query.lower().split())

        scored_chunks = []
        for i, chunk in enumerate(self.chunks):
            # Count matching keywords
            chunk_words = set(chunk.lower().split())
            matches = len(query_words & chunk_words)

            # Also score by position (earlier chunks in document weighted slightly higher)
            position_boost = 1.0 - (i / len(self.chunks)) * 0.1
            score = matches * position_boost

            # Always include if top_k not met
            if score > 0 or len(scored_chunks) < top_k:
                scored_chunks.append((score, chunk))

        # Sort by score and take top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]

        # If no matches found, return first chunk
        if not top_chunks:
            top_chunks = [self.chunks[0]]

        return "\n\n".join(top_chunks)
