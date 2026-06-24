"""Hybrid Retrieval: dense (FAISS) + sparse (BM25) + reranking.

Strategy:
- Dense: sentence-transformers/all-MiniLM-L6-v2 embeddings indexed with FAISS.
- Sparse: BM25 via rank_bm25 for keyword matching.
- Fusion: Reciprocal Rank Fusion (RRF) with k=60.
- Reranking: cross-encoder/ms-marco-MiniLM-L-6-v2 or LLM-based rescoring.
"""

import os
import json
import time
import pickle
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

import numpy as np

from rag.ingestion import Chunk, ingest_corpus


# ============================================================================
# Fusion Strategy: Reciprocal Rank Fusion (RRF)
# ============================================================================
#
# RRF formula: score(chunk) = sum_{r in rankings} 1 / (k + rank(r, chunk))
# where k=60 (standard value) and rank is 1-indexed.
#
# Why RRF over linear combination?
# - Dense scores (cosine similarity, 0..1) and sparse scores (BM25, 0..∞)
#   live on different scales. Normalizing them is brittle.
# - RRF sidesteps normalization entirely by working in rank space.
# - Empirically robust: top-1 in either list gets a strong vote.
# - No hyperparameter tuning needed (k=60 is robust across corpora).
# ============================================================================

RRF_K = 60

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ScoredChunk:
    """A chunk with retrieval scores."""
    chunk: Chunk
    dense_score: float = 0.0
    sparse_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: Optional[float] = None

    @property
    def final_score(self) -> float:
        return self.rerank_score if self.rerank_score is not None else self.fused_score


# ============================================================================
# Vector Store (FAISS wrapper)
# ============================================================================

class VectorStore:
    """Simple FAISS flat L2 index wrapped with metadata."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = None
        self.chunks: List[Chunk] = []
        self._init_faiss()

    def _init_faiss(self):
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
        except ImportError:
            # Fallback: use numpy if faiss not installed
            self.index = None

    def add(self, chunks: List[Chunk], embeddings: np.ndarray):
        """Add chunks and their embeddings to the index."""
        if self.index is not None and embeddings.shape[0] > 0:
            self.index.add(embeddings.astype(np.float32))
        self.chunks.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[int, float]]:
        """Search and return (chunk_index, distance) sorted by distance ascending."""
        if self.index is None or len(self.chunks) == 0:
            return []

        q = query_embedding.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(q, min(top_k, len(self.chunks)))

        results = []
        for d, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                # Convert L2 distance to similarity score (0..1)
                similarity = 1.0 / (1.0 + float(d))
                results.append((int(idx), similarity))
        return results


# ============================================================================
# BM25 Sparse Retrieval
# ============================================================================

class BM25Retriever:
    """BM25-based sparse retrieval."""

    def __init__(self):
        self.bm25 = None
        self.chunks: List[Chunk] = []
        self.tokenized_corpus: List[List[str]] = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer."""
        import re
        return re.findall(r'\b\w+\b', text.lower())

    def index_chunks(self, chunks: List[Chunk]):
        """Build BM25 index from chunks."""
        self.chunks = chunks
        self.tokenized_corpus = [self._tokenize(c.text) for c in chunks]

        try:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        except ImportError:
            self.bm25 = None

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """Search and return (chunk_index, bm25_score)."""
        if self.bm25 is None or len(self.chunks) == 0:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:min(top_k, len(scores))]
        results = [(int(i), float(scores[i])) for i in top_indices if scores[i] > 0]
        return results


# ============================================================================
# Reranker
# ============================================================================

class Reranker:
    """Cross-encoder based reranker or fallback MMR diversity reranker."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            print(f"  Reranker loaded: {self.model_name}")
        except Exception:
            self.model = None
            print(f"  Reranker unavailable; using MMR diversity fallback")

    def rerank(self, query: str, scored_chunks: List[ScoredChunk]) -> List[ScoredChunk]:
        """Rerank scored chunks using cross-encoder if available, else MMR."""
        if self.model is not None and len(scored_chunks) > 0:
            return self._cross_encoder_rerank(query, scored_chunks)
        else:
            return self._mmr_rerank(query, scored_chunks)

    def _cross_encoder_rerank(self, query: str, scored_chunks: List[ScoredChunk]) -> List[ScoredChunk]:
        """Use cross-encoder to rescore (query, chunk_text) pairs."""
        pairs = [(query, sc.chunk.text) for sc in scored_chunks]
        ce_scores = self.model.predict(pairs, show_progress_bar=False)

        for sc, score in zip(scored_chunks, ce_scores):
            sc.rerank_score = float(score)

        # Re-sort by rerank_score descending
        scored_chunks.sort(key=lambda x: x.rerank_score, reverse=True)
        return scored_chunks

    def _mmr_rerank(self, query: str, scored_chunks: List[ScoredChunk], lambda_param: float = 0.7) -> List[ScoredChunk]:
        """MMR (Maximal Marginal Relevance) diversity reranking.

        Balances relevance (lambda) against novelty (1-lambda) to reduce
        duplicate information across retrieved chunks.
        """
        if len(scored_chunks) <= 1:
            return scored_chunks

        selected = [scored_chunks[0]]
        remaining = scored_chunks[1:]

        # Simple MMR using word overlap as similarity
        while remaining:
            mmr_scores = []
            for sc in remaining:
                relevance = sc.fused_score
                # Max similarity to any selected chunk
                max_sim = max(
                    self._jaccard_similarity(sc.chunk.text, sel.chunk.text)
                    for sel in selected
                )
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                mmr_scores.append(mmr)

            best_idx = int(np.argmax(mmr_scores))
            selected.append(remaining.pop(best_idx))

        # Assign rerank scores as MMR scores (normalized)
        for i, sc in enumerate(selected):
            sc.rerank_score = float(len(selected) - i) / len(selected)

        return selected

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard similarity between two texts (word sets)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)


# ============================================================================
# Hybrid Retriever
# ============================================================================

class HybridRetriever:
    """Combines dense (FAISS) + sparse (BM25) retrieval with RRF fusion and reranking."""

    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        vector_store_dir: str = "vector_store",
        use_gpu: bool = False,
    ):
        self.embedding_model_name = embedding_model_name
        self.vector_store_dir = vector_store_dir
        self.use_gpu = use_gpu

        self.embedding_model = None
        self.vector_store: Optional[VectorStore] = None
        self.bm25_retriever = BM25Retriever()
        self.reranker = Reranker()
        self.all_chunks: List[Chunk] = []

        self._init_embedding_model()

    def _init_embedding_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            device = "cuda" if self.use_gpu else "cpu"
            self.embedding_model = SentenceTransformer(self.embedding_model_name, device=device)
            print(f"  Embedding model loaded: {self.embedding_model_name} on {device}")
        except Exception as e:
            print(f"  WARNING: Could not load embedding model: {e}")
            print(f"  Install: pip install sentence-transformers")
            self.embedding_model = None

    def _encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts into embeddings."""
        if self.embedding_model is None:
            # Return zero embeddings as fallback
            return np.zeros((len(texts), 384), dtype=np.float32)
        return self.embedding_model.encode(texts, show_progress_bar=False)

    def build_index(self, corpus_dir: str):
        """Full ingestion: chunk, embed, build FAISS + BM25 indices."""
        print("=" * 60)
        print("BUILDING INDEX")
        print("=" * 60)

        # Step 1: Ingest and chunk
        print("\n[1/4] Ingesting corpus...")
        chunks_by_doc = ingest_corpus(corpus_dir)
        all_chunks: List[Chunk] = []
        for chunks in chunks_by_doc.values():
            all_chunks.extend(chunks)

        self.all_chunks = all_chunks
        print(f"  Loaded {len(chunks_by_doc)} documents, {len(all_chunks)} total chunks")

        # Step 2: Generate embeddings
        print("\n[2/4] Generating embeddings...")
        texts = [c.text for c in all_chunks]
        embeddings = self._encode(texts)
        print(f"  Generated {embeddings.shape[0]} embeddings of dim {embeddings.shape[1]}")

        # Step 3: Build FAISS index
        print("\n[3/4] Building FAISS index...")
        self.vector_store = VectorStore(dimension=embeddings.shape[1])
        self.vector_store.add(all_chunks, embeddings)
        print(f"  FAISS index built: {len(self.vector_store.chunks)} vectors")

        # Step 4: Build BM25 index
        print("\n[4/4] Building BM25 index...")
        self.bm25_retriever.index_chunks(all_chunks)
        print(f"  BM25 index built: {len(self.bm25_retriever.chunks)} documents")

        print("\nIndex build complete.\n")

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
        user_role: str = "intern",
    ) -> List[ScoredChunk]:
        """Run hybrid retrieval: dense + sparse → RRF fusion → rerank.

        Args:
            query: The search query.
            top_k: Number of final results to return.
            dense_top_k: Candidates from dense retrieval.
            sparse_top_k: Candidates from sparse retrieval.
            user_role: Filter chunks by min_role access control.

        Returns:
            List of ScoredChunk sorted by final score descending.
        """
        if self.vector_store is None or len(self.all_chunks) == 0:
            print("WARNING: Index not built. Call build_index() first.")
            return []

        # --- Step 1: Dense retrieval ---
        query_embedding = self._encode([query])
        dense_results = self.vector_store.search(query_embedding[0], top_k=dense_top_k)

        # --- Step 2: Sparse (BM25) retrieval ---
        sparse_results = self.bm25_retriever.search(query, top_k=sparse_top_k)

        # --- Step 3: Apply role-based access control ---
        role_priority = {"intern": 0, "employee": 1, "manager": 2, "admin": 3}
        user_level = role_priority.get(user_role.lower(), 0)

        def can_access(chunk: Chunk) -> bool:
            min_role = chunk.metadata.get("min_role", "intern").lower()
            required_level = role_priority.get(min_role, 0)
            return user_level >= required_level

        # --- Step 4: Reciprocal Rank Fusion ---
        dense_ranks: Dict[int, int] = {}
        for rank, (idx, _) in enumerate(dense_results, 1):
            dense_ranks[idx] = rank

        sparse_ranks: Dict[int, int] = {}
        for rank, (idx, _) in enumerate(sparse_results, 1):
            sparse_ranks[idx] = rank

        # Collect all candidate indices
        all_candidate_indices = set(dense_ranks.keys()) | set(sparse_ranks.keys())

        scored_chunks: List[ScoredChunk] = []
        for idx in all_candidate_indices:
            chunk = self.all_chunks[idx]

            # Role-based filter
            if not can_access(chunk):
                continue

            dense_rank = dense_ranks.get(idx, dense_top_k + 10)
            sparse_rank = sparse_ranks.get(idx, sparse_top_k + 10)

            # RRF score
            rrf_score = (1.0 / (RRF_K + dense_rank)) + (1.0 / (RRF_K + sparse_rank))

            # Original dense score
            dense_score = 0.0
            for di, ds in dense_results:
                if di == idx:
                    dense_score = ds
                    break

            # Original sparse score
            sparse_score = 0.0
            for si, ss in sparse_results:
                if si == idx:
                    sparse_score = ss
                    break

            sc = ScoredChunk(
                chunk=chunk,
                dense_score=dense_score,
                sparse_score=sparse_score,
                fused_score=rrf_score,
            )
            scored_chunks.append(sc)

        # Sort by fused_score descending
        scored_chunks.sort(key=lambda x: x.fused_score, reverse=True)

        # Take top candidates for reranking
        candidates_for_rerank = scored_chunks[:min(top_k * 2, len(scored_chunks))]

        # --- Step 5: Rerank ---
        print(f"\n  Dense candidates: {len(dense_results)}")
        print(f"  Sparse candidates: {len(sparse_results)}")
        print(f"  After RRF + access filter: {len(scored_chunks)}")
        print(f"  Before rerank top-3 scores:")
        for sc in scored_chunks[:3]:
            print(f"    {sc.chunk.chunk_id}: dense={sc.dense_score:.4f}, sparse={sc.sparse_score:.4f}, fused={sc.fused_score:.6f}")

        reranked = self.reranker.rerank(query, candidates_for_rerank)

        print(f"\n  After rerank top-3:")
        for sc in reranked[:3]:
            print(f"    {sc.chunk.chunk_id}: dense={sc.dense_score:.4f}, fused={sc.fused_score:.6f}, rerank={sc.rerank_score:.4f}")

        return reranked[:top_k]

    def save_index(self):
        """Persist vector store and BM25 index to disk."""
        os.makedirs(self.vector_store_dir, exist_ok=True)

        # Save chunks metadata
        chunks_data = []
        for c in self.all_chunks:
            chunks_data.append({
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "title": c.title,
                "text": c.text,
                "chunk_index": c.chunk_index,
                "start_char": c.start_char,
                "end_char": c.end_char,
                "metadata": c.metadata,
            })

        with open(os.path.join(self.vector_store_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # Save BM25
        with open(os.path.join(self.vector_store_dir, "bm25.pkl"), "wb") as f:
            pickle.dump({
                "tokenized_corpus": self.bm25_retriever.tokenized_corpus,
            }, f)

        # Save FAISS index
        if self.vector_store is not None and self.vector_store.index is not None:
            import faiss
            faiss.write_index(self.vector_store.index,
                              os.path.join(self.vector_store_dir, "faiss.index"))

        print(f"Index saved to {self.vector_store_dir}/")

    def load_index(self):
        """Load vector store and BM25 index from disk."""
        # Load chunks
        chunks_path = os.path.join(self.vector_store_dir, "chunks.json")
        if not os.path.exists(chunks_path):
            print(f"No saved index found at {chunks_path}")
            return False

        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        self.all_chunks = []
        for cd in chunks_data:
            c = Chunk(
                chunk_id=cd["chunk_id"],
                document_id=cd["document_id"],
                title=cd["title"],
                text=cd["text"],
                chunk_index=cd["chunk_index"],
                start_char=cd["start_char"],
                end_char=cd["end_char"],
                metadata=cd["metadata"],
            )
            self.all_chunks.append(c)

        # Load FAISS
        faiss_path = os.path.join(self.vector_store_dir, "faiss.index")
        if os.path.exists(faiss_path):
            import faiss
            index = faiss.read_index(faiss_path)
            self.vector_store = VectorStore(dimension=index.d)
            self.vector_store.index = index
            self.vector_store.chunks = self.all_chunks

        # Load BM25
        bm25_path = os.path.join(self.vector_store_dir, "bm25.pkl")
        if os.path.exists(bm25_path):
            with open(bm25_path, "rb") as f:
                data = pickle.load(f)
            self.bm25_retriever.tokenized_corpus = data["tokenized_corpus"]
            self.bm25_retriever.chunks = self.all_chunks
            from rank_bm25 import BM25Okapi
            self.bm25_retriever.bm25 = BM25Okapi(self.bm25_retriever.tokenized_corpus)

        print(f"Index loaded from {self.vector_store_dir}/")
        print(f"  Chunks: {len(self.all_chunks)}")
        return True


if __name__ == "__main__":
    retriever = HybridRetriever()
    retriever.build_index("corpus")

    # Test query
    results = retriever.retrieve("What is the password policy?")
    print(f"\nTop results for 'What is the password policy?':")
    for sc in results:
        print(f"  [{sc.chunk.chunk_id}] score={sc.final_score:.4f}")
        print(f"    {sc.chunk.text[:120]}...")