"""Structured trace logger for all agent runs.

Writes JSONL files to data/traces/ with one line per trace.
Also provides per-event logging during strategy execution.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from strategies.base import Trace, TraceEvent
from config import CONFIG


class Tracer:
    """Singleton tracer that writes traces to disk."""

    _instance: Optional["Tracer"] = None

    def __init__(self):
        self.traces_dir = CONFIG.traces_dir
        os.makedirs(self.traces_dir, exist_ok=True)
        self._traces: list[Trace] = []

    @classmethod
    def get(cls) -> "Tracer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _generate_trace_id(self) -> str:
        return f"trace_{uuid.uuid4().hex[:12]}_{int(datetime.now(timezone.utc).timestamp())}"

    def new_trace(
        self, problem_id: str, strategy: str, problem_text: str, ground_truth: str
    ) -> Trace:
        trace_id = self._generate_trace_id()
        trace = Trace(
            trace_id=trace_id,
            problem_id=problem_id,
            strategy=strategy,
            problem_text=problem_text,
            ground_truth=ground_truth,
            final_answer="",
            is_correct=False,
        )
        return trace

    def save_trace(self, trace: Trace):
        """Write a trace to the JSONL file."""
        self._traces.append(trace)
        filepath = os.path.join(self.traces_dir, f"{trace.strategy}.jsonl")
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")

    def load_traces(self, strategy: str = None) -> list[dict]:
        """Load all stored traces, optionally filtered by strategy."""
        traces = []
        if strategy:
            filepath = os.path.join(self.traces_dir, f"{strategy}.jsonl")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            traces.append(json.loads(line))
        else:
            for fname in os.listdir(self.traces_dir):
                if fname.endswith(".jsonl"):
                    filepath = os.path.join(self.traces_dir, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                traces.append(json.loads(line))
        return traces

    def get_trace_by_id(self, trace_id: str) -> Optional[dict]:
        """Look up a specific trace by its ID."""
        for fname in os.listdir(self.traces_dir):
            if fname.endswith(".jsonl"):
                filepath = os.path.join(self.traces_dir, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            d = json.loads(line)
                            if d.get("trace_id") == trace_id:
                                return d
        return None

    def clear(self):
        """Clear the in-memory trace list."""
        self._traces = []

    def get_all_traces(self) -> list[Trace]:
        return self._traces


def make_event(
    strategy: str,
    problem_id: str,
    step_type: str,
    inputs: dict,
    outputs: dict,
    token_usage: dict = None,
    latency_ms: float = 0.0,
    meta: dict = None,
) -> TraceEvent:
    return TraceEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        strategy=strategy,
        problem_id=problem_id,
        step_type=step_type,
        inputs=inputs,
        outputs=outputs,
        token_usage=token_usage or {},
        latency_ms=latency_ms,
        meta=meta or {},
    )