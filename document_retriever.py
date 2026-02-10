"""
Document Retrieval - Simple and robust text chunking and retrieval
Tries semantic search, falls back to keyword search
"""

import re
from typing import List


class DocumentRetriever:
    """Retrieve relevant document chunks based on queries"""

    def __init__(self, doc_text: str):
        """Initialize retriever with document text"""
        self.doc_text = doc_text
        self.chunks = self._create_chunks(doc_text)
        self.use_semantic = False

        # Try to initialize semantic search (optional enhancement)
        try:
            from llama_index.core import Document, VectorStoreIndex, Settings
            from llama_index.core.node_parser import SimpleNodeParser
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            print("[Retriever] Setting up semantic search with HuggingFace...")

            # Initialize embeddings
            embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_folder="./.cache/huggingface"
            )
            Settings.embed_model = embed_model

            # Create document
            document = Document(text=doc_text)

            # Parse into nodes
            node_parser = SimpleNodeParser.from_defaults(
                chunk_size=512,
                chunk_overlap=50
            )
            nodes = node_parser.get_nodes_from_documents([document])

            # Create index
            self.index = VectorStoreIndex(nodes, embed_model=embed_model)
            self.use_semantic = True
            print("[Retriever] ✓ Semantic search enabled")

        except Exception as e:
            print(f"[Retriever] ⚠ Semantic search unavailable: {e}")
            print("[Retriever] Falling back to keyword search")
            self.use_semantic = False

    def _create_chunks(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split document into overlapping chunks"""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """Retrieve relevant context for a query"""

        if self.use_semantic:
            return self._semantic_retrieve(query, top_k)
        else:
            return self._keyword_retrieve(query, top_k)

    def _semantic_retrieve(self, query: str, top_k: int = 3) -> str:
        """Use semantic search via LLamaIndex"""
        try:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)

            if nodes:
                context = "\n\n".join([node.get_content() for node in nodes])
                if context.strip():
                    return context

            # Fallback if retrieval failed
            return self._keyword_retrieve(query, top_k)

        except Exception as e:
            print(
                f"[Retriever] Semantic retrieve failed: {e}, using keyword fallback")
            return self._keyword_retrieve(query, top_k)

    def _keyword_retrieve(self, query: str, top_k: int = 3) -> str:
        """Simple keyword-based retrieval"""
        keywords = query.lower().split()

        # Score chunks by keyword matches
        scored_chunks = []
        for chunk in self.chunks:
            chunk_lower = chunk.lower()
            # Count keyword matches
            score = sum(chunk_lower.count(kw) for kw in keywords)
            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by score (descending) and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])

        if scored_chunks:
            context = "\n\n".join(
                [chunk for _, chunk in scored_chunks[:top_k]])
        else:
            # If no keyword matches, return first chunks
            context = "\n\n".join(self.chunks[:top_k])

        return context
