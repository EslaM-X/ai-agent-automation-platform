"""Observability.

Every workflow run is recorded in an audit log. The default implementation is
in-memory; a production deployment swaps in structured logging / a database by
implementing the same interface.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from core import WorkflowRun


@dataclass
class AuditEntry:
    timestamp: float
    workflow_id: str
    step: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": round(self.timestamp, 3),
            "workflow_id": self.workflow_id,
            "step": self.step,
            "data": self.data,
        }


class AuditLog:
    """Append-only audit log for workflow runs."""

    def __init__(self):
        self._entries: List[AuditEntry] = []

    def record(self, workflow_id: str, step: str, **data) -> None:
        self._entries.append(AuditEntry(time.time(), workflow_id, step, data))

    def for_workflow(self, workflow_id: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.workflow_id == workflow_id]

    def export(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def export_json(self) -> str:
        return json.dumps(self.export(), indent=2)

    def observe(self, run: WorkflowRun) -> None:
        for step in run.steps:
            self.record(run.id, step["step"], **step["data"])
