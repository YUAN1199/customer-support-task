"""Safety Reviewer Agent - runs output guardrails, produces SafetyVerdict.

Uses a different model than the Synthesizer to reduce collusion risk.
This is the Dual-LLM pattern applied at the output boundary.
"""

import os
from typing import List

from agents.schemas import (
    SafetyReviewRequest, SafetyVerdict, SafetyIncident, RetrievedChunk,
    MessageEnvelope, AgentRole, SafetyVerdictType,
)


class SafetyReviewerAgent:
    """Reviews draft responses against safety policies.

    Runs output guardrails: grounding check, PII leak check, indirect injection.
    Returns approve / redact / regenerate / reject verdict.
    """

    def __init__(self, output_guardrails, model_name: str = None):
        self.guardrails = output_guardrails
        self.model_name = model_name or os.getenv("SAFETY_REVIEWER_MODEL", "gpt-3.5-turbo")
        self.role = AgentRole.SAFETY_REVIEWER

    def handle_request(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Process a SafetyReviewRequest and return a SafetyVerdict envelope."""
        req = SafetyReviewRequest(**envelope.payload)

        # Convert RetrievedChunk to ScoredChunk-like format for guardrails
        # The output guardrails expect ScoredChunk objects with .chunk attribute
        class ChunkWrapper:
            def __init__(self, chunk_id, title, text, metadata):
                self.chunk_id = chunk_id
                self.title = title
                self.text = text
                self.metadata = metadata or {}

        wrapped_chunks = []
        for rc in req.retrieved_chunks:
            cw = ChunkWrapper(
                chunk_id=rc.metadata.chunk_id,
                title=rc.metadata.doc_title,
                text=rc.content,
                metadata={"min_role": rc.metadata.min_role.value},
            )
            # Create a ScoredChunk-like object
            class ScoredChunkLike:
                def __init__(self, chunk):
                    self.chunk = chunk
            wrapped_chunks.append(ScoredChunkLike(cw))

        # Run output guardrails
        safety_result = self.guardrails.evaluate(
            draft_response=req.draft_response,
            retrieved_chunks=wrapped_chunks,
            question=req.user_message,
        )

        # Map guardrail verdict to schema verdict
        verdict_map = {
            "approve": SafetyVerdictType.APPROVED,
            "redact": SafetyVerdictType.REDACT,
            "regenerate": SafetyVerdictType.REGENERATE,
            "reject": SafetyVerdictType.REJECT,
        }

        schema_verdict = verdict_map.get(safety_result.verdict, SafetyVerdictType.REJECT)

        # Build incidents list
        incidents = []
        if safety_result.incident:
            inc = safety_result.incident
            incidents.append(SafetyIncident(
                incident_id=inc.incident_id,
                rule_triggered=inc.rule_triggered,
                severity="BLOCK" if inc.decision == "reject" else "WARNING",
                redacted_input=inc.redacted_input,
                decision=inc.decision,
                details=str(inc.details),
            ))

        # Build critique for regenerate
        critique = ""
        if safety_result.verdict == "regenerate":
            critique = "; ".join(safety_result.grounding_issues)

        verdict = SafetyVerdict(
            verdict=schema_verdict,
            critique=critique,
            redacted_response=safety_result.redacted_response,
            incidents=incidents,
            model_used=self.model_name,
        )

        return MessageEnvelope(
            correlation_id=envelope.correlation_id,
            sender=self.role,
            recipient=AgentRole.ORCHESTRATOR,
            message_type="SafetyVerdict",
            payload=verdict.model_dump(),
        )