"""
============================================================
AVORA Agent Layer
============================================================

The agent layer turns AVORA from a chat responder into a
computer operator: it understands a goal, gathers context,
plans, asks for permission when needed, executes real tools,
verifies the outcome, recovers from failures, and reports
honestly what happened.

Design rules (see ARCHITECTURE.md):
- Additive: nothing here replaces existing AVORA subsystems.
  Existing skills/* modules are wrapped as tools, not rewritten.
- Honest: a tool result is never synthesized. If something did
  not run, the result says so.
- Safe: every mutating tool passes through PermissionManager.

Public API is intentionally small so ai_logic can integrate
with a single import.
"""

from agent.tools import (
    Tool,
    ToolResult,
    ToolRegistry,
    RiskLevel,
    get_registry,
)
from agent.permissions import (
    PermissionManager,
    PermissionDecision,
    Scope,
    get_permission_manager,
)

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "RiskLevel",
    "get_registry",
    "PermissionManager",
    "PermissionDecision",
    "Scope",
    "get_permission_manager",
]
