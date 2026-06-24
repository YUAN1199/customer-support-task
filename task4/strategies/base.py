"""Base Strategy interface for the Agentic Reasoning Lab.

Every reasoning strategy must implement this interface so the eval harness
can run them identically and compare results apples-to-apples.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TraceEvent:
    """A single structured event within a trace."""

    timestamp: str  # ISO-8601
    strategy: str
    problem_id: str
    step_type: str  # e.g. "llm_call", "tool_call", "plan_step", "branch_eval", "final_answer"
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    token_usage: Dict[str, int] = field(default_factory=dict)  # {"input": N, "output": M}
    latency_ms: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Full execution trace for a single problem under one strategy."""

    trace_id: str
    problem_id: str
    strategy: str
    problem_text: str
    ground_truth: str
    final_answer: str
    is_correct: bool
    events: List[TraceEvent] = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: TraceEvent):
        self.events.append(event)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "problem_id": self.problem_id,
            "strategy": self.strategy,
            "problem_text": self.problem_text,
            "ground_truth": self.ground_truth,
            "final_answer": self.final_answer,
            "is_correct": self.is_correct,
            "total_latency_ms": self.total_latency_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "extra": self.extra,
            "events": [
                {
                    "timestamp": e.timestamp,
                    "strategy": e.strategy,
                    "problem_id": e.problem_id,
                    "step_type": e.step_type,
                    "inputs": e.inputs,
                    "outputs": e.outputs,
                    "token_usage": e.token_usage,
                    "latency_ms": e.latency_ms,
                    "meta": e.meta,
                }
                for e in self.events
            ],
        }


class Strategy(ABC):
    """Abstract base for a reasoning strategy.

    Subclasses must implement solve(problem, problem_id) -> Trace.
    """

    name: str = "base"

    @abstractmethod
    def solve(self, problem: str, problem_id: str = "") -> Trace:
        """Solve a single problem and return a structured trace.

        Args:
            problem: The problem text.
            problem_id: Unique identifier for the problem (matches golden set).

        Returns:
            A Trace object with all events, final answer, and metadata.
        """
        ...

    def __repr__(self) -> str:
        return f"<Strategy:{self.name}>"