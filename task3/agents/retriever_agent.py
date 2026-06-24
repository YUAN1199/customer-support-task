"""Retriever Agent - owns the vector store, handles RetrievalRequests."""

import time
from typing import Optional

from rag.retrieval import HybridRetriever, ScoredChunk
from agents.schemas import (
    RetrievalRequest, RetrievalResult, RetrievedChunk, ChunkMetadata,
    MessageEnvelope, AgentRole, UserRole,
)


class RetrieverAgent:
    """Agent that owns the vector store and handles retrieval requests.

    Receives RetrievalRequest via MessageEnvelope, returns RetrievalResult.
    """

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.role = AgentRole.RETRIEVER

    def handle_request(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Process a RetrievalRequest and return a RetrievalResult envelope."""
        req = RetrievalRequest(**envelope.payload)

        t0 = time.time()
        scored_chunks = self.retriever.retrieve(
            query=req.query,
            top_k=req.top_k,
            user_role=req.user_role.value if hasattr(req.user_role, 'value') else req.user_role,
        )
        elapsed_ms = (time.time() - t0) * 1000

        # Convert to schema chunks
        schema_chunks = []
        for rank, sc in enumerate(scored_chunks, 1):
            c = sc.chunk
            metadata = ChunkMetadata(
                chunk_id=c.chunk_id,
                doc_id=c.document_id,
                doc_title=c.title,
                chunk_index=c.chunk_index,
                min_role=UserRole(c.metadata.get("min_role", "intern")),
                dense_score=sc.dense_score,
                sparse_score=sc.sparse_score,
                hybrid_score=sc.fused_score,
                rerank_score=sc.rerank_score,
            )
            rc = RetrievedChunk(
                metadata=metadata,
                content=c.text,
                fusion_rank=rank,
            )
            schema_chunks.append(rc)

        result = RetrievalResult(
            query=req.query,
            chunks=schema_chunks,
            retrieval_time_ms=elapsed_ms,
        )

        return MessageEnvelope(
            correlation_id=envelope.correlation_id,
            sender=self.role,
            recipient=AgentRole.ORCHESTRATOR,
            message_type="RetrievalResult",
            payload=result.model_dump(),
        )