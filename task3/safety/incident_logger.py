"""Structured incident logger for safety guardrail decisions."""

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict


@dataclass
class IncidentLog:
    """Structured incident log entry."""
    timestamp: str
    rule_triggered: str
    stage: str  # "input" or "output"
    user_input: str
    redacted_input: str = ""
    decision: str = ""  # "pass", "reject", "redact", "regenerate"
    details: Dict[str, Any] = field(default_factory=dict)
    incident_id: str = ""

    def __post_init__(self):
        if not self.incident_id:
            import uuid
            self.incident_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class IncidentLogger:
    """JSONL-based incident logger."""

    def __init__(self, log_path: str = "logs/incidents.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, incident: IncidentLog):
        """Append an incident log entry as JSONL."""
        entry = asdict(incident)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_recent(self, n: int = 20) -> list:
        """Read the most recent n incidents."""
        if not os.path.exists(self.log_path):
            return []
        lines = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        for line in all_lines[-n:]:
            try:
                lines.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
        return lines