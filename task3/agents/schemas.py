"""
Typed message schemas for inter-agent communication.

All traffic between agents MUST validate against these schemas.
No free-form strings across agent boundaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RETRIEVER = "retriever"
    SYNTHESIZER = "synthesizer"
    SAFETY_REVIEWER = "safety_reviewer"


class SafetyVerdictType(str, Enum):
    APPROVED = "approved"
    REGENERATE = "regenerate"
    REDACT = "redact"
    REJECT = "reject"


class UserRole(str, Enum):
    INTERN = "intern"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


# ---------------------------------------------------------------------------
# Envelope (A2A-style)
# ---------------------------------------------------------------------------

class MessageEnvelope(BaseModel):
    """Every inter-agent message is wrapped in this envelope."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str  # ties together all messages in one user request
    sender: AgentRole
    recipient: AgentRole
    message_type: str
    payload: dict = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @field_validator("message_type")
    @classmethod
    def known_type(cls, v: str) -> str:
        known = {
            "RetrievalRequest", "RetrievalResult",
            "SynthesisRequest", "SynthesisResult",
            "SafetyReviewRequest", "SafetyVerdict",
            "OrchestratorPlan", "UserQuery",
            "StatusUpdate", "ErrorNotification",
        }
        if v not in known:
            raise ValueError(f"Unknown message_type: {v}")
        return v


# ---------------------------------------------------------------------------
# Payload schemas
# ---------------------------------------------------------------------------

class RetrievalRequest(BaseModel):
    """Orchestrator -> Retriever."""
    query: str
    top_k: int = 20
    user_role: UserRole = UserRole.EMPLOYEE
    filters: dict = Field(default_factory=dict)


class ChunkMetadata(BaseModel):
    """Metadata for a single retrieved chunk."""
    chunk_id: str
    doc_id: str
    doc_title: str
    chunk_index: int
    min_role: UserRole = UserRole.INTERN
    dense_score: float = 0.0
    sparse_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: Optional[float] = None


class RetrievedChunk(BaseModel):
    """A single retrieved chunk with its scores and content."""
    metadata: ChunkMetadata
    content: str
    fusion_rank: int = 0


class RetrievalResult(BaseModel):
    """Retriever -> Orchestrator."""
    query: str
    chunks: list[RetrievedChunk]
    retrieval_time_ms: float = 0.0


class SynthesisRequest(BaseModel):
    """Orchestrator -> Synthesizer."""
    question: str
    chunks: list[RetrievedChunk]
    user_role: UserRole = UserRole.EMPLOYEE
    conversation_history: list[dict] = Field(default_factory=list)


class Citation(BaseModel):
    """A single citation in the synthesized answer."""
    chunk_id: str
    doc_title: str
    excerpt: str = ""


class SynthesisResult(BaseModel):
    """Synthesizer -> Orchestrator."""
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    has_sufficient_info: bool = True
    model_used: str = ""


class SafetyReviewRequest(BaseModel):
    """Orchestrator -> Safety Reviewer."""
    user_message: str
    draft_response: str
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    user_role: UserRole = UserRole.EMPLOYEE
    round_number: int = 1


class SafetyIncident(BaseModel):
    """Structured incident log entry."""
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    rule_triggered: str
    severity: str = "WARNING"  # WARNING, BLOCK, REDACT
    redacted_input: str = ""  # sanitized version for logging
    decision: str = ""  # REJECT / REDACT / REGENERATE
    details: str = ""


class SafetyVerdict(BaseModel):
    """Safety Reviewer -> Orchestrator."""
    verdict: SafetyVerdictType
    critique: str = ""  # feedback to synthesizer if REGENERATE
    redacted_response: str = ""  # if REDACT, the cleaned response
    incidents: list[SafetyIncident] = Field(default_factory=list)
    model_used: str = ""


class TraceEntry(BaseModel):
    """One step in the request trace log."""
    step: int
    direction: str  # e.g., "orchestrator -> retriever"
    message_type: str
    payload_summary: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RequestTrace(BaseModel):
    """Full trace for a single user request."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str
    user_query: str
    entries: list[TraceEntry] = Field(default_factory=list)
    final_answer: str = ""
    final_citations: list[Citation] = Field(default_factory=list)
    safety_verdict: Optional[SafetyVerdict] = None
    total_rounds: int = 0
    completed: bool = False