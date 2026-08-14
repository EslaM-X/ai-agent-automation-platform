"""Core types shared across the platform.

Deterministic, provider-agnostic, and fully unit-testable without any LLM.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    RESEARCH = "research"
    CONTENT = "content"
    QA = "qa"
    ANALYTICS = "analytics"


class Status(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Message:
    """An immutable-ish message produced by an agent."""

    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "metadata": self.metadata}


@dataclass
class Task:
    """A unit of work routed to an agent."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    prompt: str = ""
    role: AgentRole = AgentRole.RESEARCH
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "role": self.role.value,
            "context": self.context,
        }


@dataclass
class AgentResult:
    """The output of a single agent run, plus validation flags."""

    task_id: str
    role: AgentRole
    output: str
    passed_validation: bool = False
    validation_notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "role": self.role.value,
            "output": self.output,
            "passed_validation": self.passed_validation,
            "validation_notes": self.validation_notes,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowRun:
    """An end-to-end record of one orchestration run (the audit trail)."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    objective: str = ""
    status: Status = Status.PENDING
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def log(self, step: str, **data) -> None:
        entry = {"step": step, "data": data}
        self.steps.append(entry)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "objective": self.objective,
            "status": self.status.value,
            "steps": self.steps,
            "error": self.error,
        }
