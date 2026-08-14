"""Tool permissions.

Agents declare the roles they perform; a ToolPolicy decides whether a role
may run inside a workflow. The default policy is deny-by-default for unknown
roles: every new role must be explicitly granted before it can be dispatched,
which keeps the platform conservative about what an agent is allowed to do.
"""

from __future__ import annotations

from core import AgentRole


class ToolPolicy:
    """Decides whether a role may be dispatched in a run.

    `roles` is an explicit allowlist of AgentRole values. A role that is not
    listed is denied. Granting a role is additive; revoking is explicit.
    """

    def __init__(self, roles: set[AgentRole] | None = None):
        self._roles: set[AgentRole] = set(roles or ())

    def grant(self, role: AgentRole) -> None:
        self._roles.add(role)

    def deny(self, role: AgentRole) -> None:
        self._roles.discard(role)

    def allows(self, role: AgentRole) -> bool:
        return role in self._roles

    def allowed_roles(self) -> list[str]:
        return sorted(r.value for r in self._roles)


# The shipped platform roles are granted by default; a custom role added
# later is denied until explicitly granted by a ToolPolicy override.
DEFAULT_POLICY = ToolPolicy(
    {AgentRole.RESEARCH, AgentRole.CONTENT, AgentRole.QA, AgentRole.ANALYTICS}
)
