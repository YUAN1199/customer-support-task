"""Orchestrator Agent - plans workflow, dispatches sub-tasks, aggregates results.

Implements the Orchestrator-Worker pattern with delegation:
  1. Receives UserQuery
  2. Plans workflow (retrieve → synthesize → review)
  3. Dispatches RetrievalRequest to Retriever
  4. Dispatches SynthesisRequest to Synthesizer
  5. Dispatches SafetyReviewRequest to Safety Reviewer
  6. If verdict = REGENERATE, loops back to step 4 (max MAX_ROUNDS)
  7. Returns final answer or rejection

Also implements the feedback loop:
  Safety Reviewer rejects → Orchestrator re-dispatches to Synthesizer with critique.

Produces a full trace log for each request.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from agents.schemas import (
    MessageEnvelope, AgentRole, UserRole, SafetyVerdictType,
    RetrievalRequest, RetrievalResult, RetrievedChunk,
    SynthesisRequest, SynthesisResult, Citation,
    SafetyReviewRequest, SafetyVerdict,
    TraceEntry, RequestTrace,
)

# Maximum regeneration rounds
MAX_ROUNDS = 3


class Orchestrator:
    """Orchestrates the multi-agent workflow.

    Communication pattern: Orchestrator-Worker with delegation.
    - Orchestrator sends typed messages to workers
    - Workers return typed results
    - No agent talks directly to another — all through the orchestrator
    """

    def __init__(
        self,
        retriever_agent,
        synthesizer_agent,
        safety_reviewer_agent,
        input_guardrails=None,
        trace_dir: str = "logs/traces",
    ):
        self.retriever = retriever_agent
        self.synthesizer = synthesizer_agent
        self.safety_reviewer = safety_reviewer_agent
        self.input_guardrails = input_guardrails
        self.trace_dir = trace_dir
        os.makedirs(trace_dir, exist_ok=True)
        self.role = AgentRole.ORCHESTRATOR

    def process_query(
        self,
        user_query: str,
        user_role: str = "employee",
        conversation_history: List[dict] = None,
    ) -> dict:
        """Process a user query end-to-end and return the response.

        Args:
            user_query: The user's question
            user_role: "intern", "employee", "manager", or "admin"
            conversation_history: Optional list of previous turns

        Returns:
            dict with keys: response, citations, trace_id, safety_verdict,
            rounds, guardrail_status
        """
        correlation_id = str(uuid.uuid4())
        trace = RequestTrace(
            correlation_id=correlation_id,
            user_query=user_query,
        )
        trace_entries: List[TraceEntry] = []

        step = 0

        print("\n" + "=" * 60)
        print(f"ORCHESTRATOR: Processing query [{correlation_id}]")
        print(f"  Query: {user_query[:100]}")
        print(f"  Role: {user_role}")
        print("=" * 60)

        # ====================================================================
        # STEP 0: INPUT GUARDRAILS
        # ====================================================================
        if self.input_guardrails:
            step += 1
            print(f"\n[Step {step}] Input guardrails check...")
            guard_result = self.input_guardrails.evaluate(user_query)

            trace_entries.append(TraceEntry(
                step=step,
                direction="orchestrator -> input_guardrails",
                message_type="InputGuardrails",
                payload_summary=f"passed={guard_result.passed}, reason={guard_result.reject_reason or 'N/A'}",
            ))

            if not guard_result.passed:
                print(f"  INPUT REJECTED: {guard_result.reject_reason}")
                trace.entries = trace_entries
                trace.completed = True
                trace.final_answer = f"[REJECTED] {guard_result.reject_reason}"
                self._save_trace(trace)
                return {
                    "response": f"I'm sorry, I cannot process this request. {guard_result.reject_reason}",
                    "citations": [],
                    "trace_id": trace.trace_id,
                    "safety_verdict": "rejected",
                    "rounds": 0,
                    "guardrail_status": "rejected_input",
                }

            user_query = guard_result.sanitized_text
            print(f"  Input guardrails: PASSED")

        # ====================================================================
        # STEP 1: RETRIEVAL
        # ====================================================================
        step += 1
        print(f"\n[Step {step}] Dispatching RetrievalRequest...")

        retrieval_req = RetrievalRequest(
            query=user_query,
            top_k=20,
            user_role=UserRole(user_role.lower()),
        )

        retrieval_envelope = MessageEnvelope(
            correlation_id=correlation_id,
            sender=self.role,
            recipient=AgentRole.RETRIEVER,
            message_type="RetrievalRequest",
            payload=retrieval_req.model_dump(),
        )

        trace_entries.append(TraceEntry(
            step=step,
            direction="orchestrator -> retriever",
            message_type="RetrievalRequest",
            payload_summary=f"query='{user_query[:60]}', top_k=20",
        ))

        retrieval_response = self.retriever.handle_request(retrieval_envelope)
        retrieval_result = RetrievalResult(**retrieval_response.payload)

        trace_entries.append(TraceEntry(
            step=step,
            direction="retriever -> orchestrator",
            message_type="RetrievalResult",
            payload_summary=f"chunks={len(retrieval_result.chunks)}, time={retrieval_result.retrieval_time_ms:.1f}ms",
        ))

        print(f"  Retrieved {len(retrieval_result.chunks)} chunks in {retrieval_result.retrieval_time_ms:.1f}ms")

        # ====================================================================
        # STEPS 2-N: SYNTHESIZE → REVIEW → (REGENERATE LOOP)
        # ====================================================================
        chunks = retrieval_result.chunks
        max_rounds = MAX_ROUNDS
        final_answer = ""
        final_citations: List[Citation] = []
        final_verdict = None

        for round_num in range(1, max_rounds + 1):
            trace.total_rounds = round_num

            # --- SYNTHESIZE ---
            step += 1
            print(f"\n[Step {step}] Dispatching SynthesisRequest (round {round_num})...")

            synth_req = SynthesisRequest(
                question=user_query,
                chunks=chunks,
                user_role=UserRole(user_role.lower()),
                conversation_history=conversation_history or [],
            )

            synth_envelope = MessageEnvelope(
                correlation_id=correlation_id,
                sender=self.role,
                recipient=AgentRole.SYNTHESIZER,
                message_type="SynthesisRequest",
                payload=synth_req.model_dump(),
            )

            trace_entries.append(TraceEntry(
                step=step,
                direction="orchestrator -> synthesizer",
                message_type="SynthesisRequest",
                payload_summary=f"question='{user_query[:60]}', chunks={len(chunks)}, round={round_num}",
            ))

            synth_response = self.synthesizer.handle_request(synth_envelope)
            synth_result = SynthesisResult(**synth_response.payload)

            trace_entries.append(TraceEntry(
                step=step,
                direction="synthesizer -> orchestrator",
                message_type="SynthesisResult",
                payload_summary=f"citations={len(synth_result.citations)}, has_info={synth_result.has_sufficient_info}, len={len(synth_result.answer)}",
            ))

            print(f"  Synthesized answer ({len(synth_result.answer)} chars, {len(synth_result.citations)} citations)")
            print(f"  Has sufficient info: {synth_result.has_sufficient_info}")

            # --- SAFETY REVIEW ---
            step += 1
            print(f"\n[Step {step}] Dispatching SafetyReviewRequest (round {round_num})...")

            safety_req = SafetyReviewRequest(
                user_message=user_query,
                draft_response=synth_result.answer,
                citations=synth_result.citations,
                retrieved_chunks=chunks,
                user_role=UserRole(user_role.lower()),
                round_number=round_num,
            )

            safety_envelope = MessageEnvelope(
                correlation_id=correlation_id,
                sender=self.role,
                recipient=AgentRole.SAFETY_REVIEWER,
                message_type="SafetyReviewRequest",
                payload=safety_req.model_dump(),
            )

            trace_entries.append(TraceEntry(
                step=step,
                direction="orchestrator -> safety_reviewer",
                message_type="SafetyReviewRequest",
                payload_summary=f"round={round_num}, response_len={len(synth_result.answer)}",
            ))

            safety_response = self.safety_reviewer.handle_request(safety_envelope)
            safety_verdict = SafetyVerdict(**safety_response.payload)

            trace_entries.append(TraceEntry(
                step=step,
                direction="safety_reviewer -> orchestrator",
                message_type="SafetyVerdict",
                payload_summary=f"verdict={safety_verdict.verdict.value}, critique='{safety_verdict.critique[:80]}', incidents={len(safety_verdict.incidents)}",
            ))

            print(f"  Safety Verdict: {safety_verdict.verdict.value}")
            if safety_verdict.critique:
                print(f"  Critique: {safety_verdict.critique[:120]}")

            # --- Handle verdict ---
            if safety_verdict.verdict == SafetyVerdictType.APPROVED:
                final_answer = synth_result.answer
                final_citations = synth_result.citations
                final_verdict = safety_verdict
                print(f"  ✅ APPROVED — answer is grounded and safe")
                break

            elif safety_verdict.verdict == SafetyVerdictType.REDACT:
                final_answer = safety_verdict.redacted_response or synth_result.answer
                final_citations = synth_result.citations
                final_verdict = safety_verdict
                print(f"  ⚠️ REDACTED — PII removed, answer otherwise valid")
                break

            elif safety_verdict.verdict == SafetyVerdictType.REGENERATE:
                print(f"  🔄 REGENERATE requested (round {round_num}/{max_rounds})")
                if round_num < max_rounds:
                    # Feedback loop: re-dispatch to synthesizer with critique
                    print(f"  Feedback loop: sending critique to synthesizer...")
                    synth_response = self.synthesizer.regenerate(
                        synth_envelope,
                        safety_verdict.critique,
                        chunks,
                    )
                    synth_result = SynthesisResult(**synth_response.payload)

                    trace_entries.append(TraceEntry(
                        step=step,
                        direction="orchestrator -> synthesizer (regenerate)",
                        message_type="SynthesisRequest",
                        payload_summary=f"regenerate with critique: '{safety_verdict.critique[:60]}'",
                    ))
                else:
                    # Max rounds reached
                    final_answer = synth_result.answer
                    final_citations = synth_result.citations
                    final_verdict = safety_verdict
                    print(f"  ⚠️ Max rounds ({max_rounds}) reached — using last answer")
                    break

            elif safety_verdict.verdict == SafetyVerdictType.REJECT:
                final_answer = f"[REJECTED] Response rejected by safety reviewer: {safety_verdict.critique}"
                final_citations = []
                final_verdict = safety_verdict
                print(f"  ❌ REJECTED — response blocked by safety")
                break

        # ====================================================================
        # FINALIZE
        # ====================================================================
        trace.entries = trace_entries
        trace.final_answer = final_answer
        trace.final_citations = final_citations
        trace.safety_verdict = final_verdict
        trace.completed = True

        self._save_trace(trace)

        print(f"\n{'=' * 60}")
        print(f"REQUEST COMPLETE [{correlation_id}]")
        print(f"  Rounds: {trace.total_rounds}")
        print(f"  Verdict: {final_verdict.verdict.value if final_verdict else 'N/A'}")
        print(f"  Answer length: {len(final_answer)} chars")
        print(f"  Citations: {len(final_citations)}")
        print(f"  Trace saved: {self.trace_dir}/trace_{trace.trace_id}.json")
        print(f"{'=' * 60}\n")

        return {
            "response": final_answer,
            "citations": [c.model_dump() for c in final_citations],
            "trace_id": trace.trace_id,
            "safety_verdict": final_verdict.model_dump() if final_verdict else None,
            "rounds": trace.total_rounds,
            "guardrail_status": "passed",
        }

    def _save_trace(self, trace: RequestTrace):
        """Save the trace as structured JSON."""
        trace_path = os.path.join(self.trace_dir, f"trace_{trace.trace_id}.json")
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace.model_dump(), f, indent=2, ensure_ascii=False, default=str)

    def print_trace(self, trace_id: str):
        """Print a formatted trace from disk."""
        trace_path = os.path.join(self.trace_dir, f"trace_{trace_id}.json")
        if not os.path.exists(trace_path):
            print(f"Trace not found: {trace_path}")
            return

        with open(trace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("\n" + "=" * 60)
        print(f"TRACE: {trace_id}")
        print(f"Correlation: {data['correlation_id']}")
        print(f"Query: {data['user_query']}")
        print("=" * 60)
        for entry in data.get("entries", []):
            print(f"  [{entry['step']}] {entry['direction']}")
            print(f"       Type: {entry['message_type']}")
            print(f"       Summary: {entry['payload_summary']}")
        print(f"\n  Final Answer ({len(data.get('final_answer', ''))} chars):")
        print(f"  {data.get('final_answer', '')[:500]}...")
        print(f"  Citations: {len(data.get('final_citations', []))}")
        print(f"  Safety Verdict: {data.get('safety_verdict', {})}")
        print("=" * 60)