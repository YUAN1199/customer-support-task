"""Synthesizer Agent - produces grounded answers with citations.

Uses an LLM to synthesize a response from retrieved chunks.
Enforces citation discipline: every claim must reference a chunk ID.
"""

import os
import json
from typing import List, Optional

from agents.schemas import (
    SynthesisRequest, SynthesisResult, Citation, RetrievedChunk,
    MessageEnvelope, AgentRole,
)


# ============================================================================
# Prompt Templates (externalized)
# ============================================================================

SYNTHESIS_SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Your job is to answer questions using ONLY the information in the provided CHUNKS below.

CRITICAL RULES:
1. NEVER make up facts. If the chunks don't contain the answer, say clearly: "I don't have enough information on [topic]."
2. EVERY factual claim MUST include an inline citation to the chunk that supports it, like this: [chunk_id].
3. If multiple chunks support the same fact, cite the most relevant one.
4. Keep answers concise and professional.
5. DO NOT mention chunk IDs that you don't actually use.
6. If the question is completely outside the scope of the provided chunks, say: "I cannot answer this question — it falls outside the available knowledge base."

CHUNKS:
{chunks_text}

Now answer the user's question with proper citations."""

SYNTHESIS_USER_TEMPLATE = """Question: {question}

Provide a grounded, cited answer using ONLY the chunks above."""

REGENERATE_PROMPT = """Your previous answer was flagged for these issues:
{critique}

Please rewrite your answer addressing these issues. Use the same chunks and citation format.

CHUNKS:
{chunks_text}

Question: {question}

Provide a corrected, grounded answer with citations."""


# ============================================================================
# Synthesizer Agent
# ============================================================================

class SynthesizerAgent:
    """Produces grounded answers with inline citations to chunk IDs.

    Handles SynthesisRequest → SynthesisResult.
    Implements the "I don't know" discipline for out-of-corpus questions.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("SYNTHESIZER_MODEL", "gpt-4o-mini")
        self.role = AgentRole.SYNTHESIZER

    def _format_chunks(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks for the LLM prompt."""
        lines = []
        for rc in chunks:
            lines.append(
                f"[{rc.metadata.chunk_id}] (from '{rc.metadata.doc_title}'):\n"
                f"{rc.content}\n"
            )
        return "\n".join(lines)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM via API."""
        import os as _os

        api_key = _os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                import requests
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    return content.strip()
                else:
                    print(f"  [Synthesizer] API error: {response.status_code}")
                    return self._fallback_synthesize(system_prompt, user_prompt)
            except Exception as e:
                print(f"  [Synthesizer] API call failed: {e}")
                return self._fallback_synthesize(system_prompt, user_prompt)

        # Try local Ollama
        try:
            import requests as req
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = req.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1000},
                },
                timeout=60,
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            print(f"  [Synthesizer] Ollama error: {e}")

        return self._fallback_synthesize(system_prompt, user_prompt)

    def _fallback_synthesize(self, system_prompt: str, user_prompt: str) -> str:
        """Template-based fallback when no LLM is available."""
        # Extract chunks and question from the prompt
        import re

        # Extract question
        q_match = re.search(r'Question:\s*(.+?)(?:\n|$)', user_prompt, re.DOTALL)
        question = q_match.group(1).strip() if q_match else user_prompt

        # Extract chunk IDs
        chunk_ids = re.findall(r'\[(CORP-\d+_chunk\d+)\]', system_prompt)
        if not chunk_ids:
            chunk_ids = re.findall(r'\[(CORP-\d+_chunk\d+)\]', user_prompt)

        if not chunk_ids:
            return f"I don't have enough information to answer your question about '{question}'. No relevant documents were found in the knowledge base."

        # Simple template-based response
        cited_ids = ", ".join(chunk_ids[:5])
        return (
            f"Based on the available documentation, I can provide the following information "
            f"relevant to your question about '{question}'.\n\n"
            f"[{chunk_ids[0]}] The knowledge base contains information related to your query. "
            f"Please refer to the cited chunks for details.\n\n"
            f"Note: This is a template-based response. For more accurate results, "
            f"configure an LLM API key in .env."
        )

    def _extract_citations(self, answer: str, chunks: List[RetrievedChunk]) -> List[Citation]:
        """Extract citation metadata from the answer text."""
        import re
        cited_ids = set(re.findall(r'\[(CORP-\d+_chunk\d+)\]', answer))

        # Build lookup
        chunk_map = {rc.metadata.chunk_id: rc for rc in chunks}

        citations = []
        for cid in sorted(cited_ids):
            rc = chunk_map.get(cid)
            if rc:
                citations.append(Citation(
                    chunk_id=cid,
                    doc_title=rc.metadata.doc_title,
                    excerpt=rc.content[:200],
                ))

        return citations

    def handle_request(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Process a SynthesisRequest and return a SynthesisResult."""
        req = SynthesisRequest(**envelope.payload)

        chunks_text = self._format_chunks(req.chunks)
        has_chunks = len(req.chunks) > 0

        if not has_chunks:
            # No chunks - synthesize "I don't know" response
            answer = (
                f"I don't have enough information to answer your question about "
                f"'{req.question}'. No relevant documents were found in the knowledge base. "
                f"Please try a different query or contact your administrator for assistance."
            )
            result = SynthesisResult(
                question=req.question,
                answer=answer,
                citations=[],
                has_sufficient_info=False,
                model_used="none (no chunks)",
            )
            return MessageEnvelope(
                correlation_id=envelope.correlation_id,
                sender=self.role,
                recipient=AgentRole.ORCHESTRATOR,
                message_type="SynthesisResult",
                payload=result.model_dump(),
            )

        # Call LLM for synthesis
        system_prompt = SYNTHESIS_SYSTEM_PROMPT.format(chunks_text=chunks_text)
        user_prompt = SYNTHESIS_USER_TEMPLATE.format(question=req.question)

        print(f"  [Synthesizer] Generating answer for: {req.question[:80]}...")
        answer = self._call_llm(system_prompt, user_prompt)

        # Check for "I don't know" signals
        has_sufficient = not (
            "I don't have enough information" in answer
            or "I cannot answer this question" in answer
        )

        # Extract citations
        citations = self._extract_citations(answer, req.chunks)

        result = SynthesisResult(
            question=req.question,
            answer=answer,
            citations=citations,
            has_sufficient_info=has_sufficient,
            model_used=self.model_name,
        )

        return MessageEnvelope(
            correlation_id=envelope.correlation_id,
            sender=self.role,
            recipient=AgentRole.ORCHESTRATOR,
            message_type="SynthesisResult",
            payload=result.model_dump(),
        )

    def regenerate(self, envelope: MessageEnvelope, critique: str, chunks: List[RetrievedChunk]) -> MessageEnvelope:
        """Regenerate answer based on safety reviewer critique."""
        req = SynthesisRequest(**envelope.payload)

        chunks_text = self._format_chunks(chunks)
        system_prompt = REGENERATE_PROMPT.format(
            critique=critique,
            chunks_text=chunks_text,
            question=req.question,
        )
        user_prompt = "Please provide a corrected answer with citations."

        print(f"  [Synthesizer] Regenerating answer based on critique...")
        answer = self._call_llm(system_prompt, user_prompt)

        citations = self._extract_citations(answer, chunks)

        result = SynthesisResult(
            question=req.question,
            answer=answer,
            citations=citations,
            has_sufficient_info=True,
            model_used=self.model_name,
        )

        return MessageEnvelope(
            correlation_id=envelope.correlation_id,
            sender=self.role,
            recipient=AgentRole.ORCHESTRATOR,
            message_type="SynthesisResult",
            payload=result.model_dump(),
        )