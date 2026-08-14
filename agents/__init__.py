"""Specialized agents.

Agents are thin, testable units: they take a prompt + context, call a provider,
and return a result. They have no opinion about orchestration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core import AgentResult, AgentRole, Task


class Provider(ABC):
    """Minimal LLM interface so the platform works with any backend."""

    @abstractmethod
    def complete(self, system: str, user: str, temperature: float = 0.2) -> str: ...


class Agent(ABC):
    role: AgentRole

    @abstractmethod
    def run(self, task: Task) -> AgentResult:
        """Execute the task and return a validated result."""


class _TemplateAgent(Agent):
    """Shared skeleton: build prompt -> call provider -> basic validation."""

    role: AgentRole

    def __init__(self, provider: Provider):
        self.provider = provider

    def _system(self) -> str:
        raise NotImplementedError

    def _validate(self, output: str) -> tuple[bool, list[str]]:
        stripped = output.strip()
        if not stripped:
            return False, ["empty output"]
        return True, []

    def run(self, task: Task) -> AgentResult:
        output = self.provider.complete(self._system(), task.prompt)
        passed, notes = self._validate(output)
        return AgentResult(
            task_id=task.id,
            role=self.role,
            output=output,
            passed_validation=passed,
            validation_notes=notes,
            metadata={"provider": self.provider.__class__.__name__},
        )


class ResearchAgent(_TemplateAgent):
    role = AgentRole.RESEARCH

    def _system(self) -> str:
        return (
            "You are a research agent. Gather facts, cite sources, and return "
            "concise findings. Never invent data."
        )


class ContentAgent(_TemplateAgent):
    role = AgentRole.CONTENT

    def _system(self) -> str:
        return (
            "You are a content agent. Turn inputs into clear, structured "
            "content. Keep the audience in mind."
        )


class QAAgent(_TemplateAgent):
    role = AgentRole.QA

    def _system(self) -> str:
        return "You are a QA agent. Check for errors, omissions, and risks. Report issues."


class AnalyticsAgent(_TemplateAgent):
    role = AgentRole.ANALYTICS

    def _system(self) -> str:
        return (
            "You are an analytics agent. Summarize numbers, trends, and "
            "anomalies. Be precise."
        )


def build_agent(role: AgentRole, provider: Provider) -> Agent:
    factory = {
        AgentRole.RESEARCH: ResearchAgent,
        AgentRole.CONTENT: ContentAgent,
        AgentRole.QA: QAAgent,
        AgentRole.ANALYTICS: AnalyticsAgent,
    }
    return factory[role](provider)
