"""
============================================================
AVORA Core Module
============================================================

Core system components for the AVORA AI desktop companion.

Modules:
- intelligence_engine: Main request processing pipeline
- context_engine: Desktop context collection
- memory_engine: Multi-tier memory management
- reasoning_engine: Understanding and planning
- action_planner: Multi-step action planning
- health_monitor: System health monitoring
- recovery_manager: Crash recovery system
"""

from core.intelligence_engine import (
    IntelligenceEngine,
    get_intelligence_engine,
    IntentType,
    UserRequest,
    DetectedIntent,
    ContextSnapshot,
    ActionPlan,
    ExecutionResult,
)

from core.context_engine import (
    ContextEngine,
    get_context_engine,
    SystemContext,
    DesktopContext,
    UserContext,
    EnvironmentContext,
)

from core.health_monitor import (
    HealthMonitor,
    HealthStatus,
    get_health_monitor,
    get_health_status,
)

from core.recovery_manager import (
    RecoveryManager,
    RecoveryRecord,
    get_recovery_manager,
)

__all__ = [
    "IntelligenceEngine",
    "get_intelligence_engine",
    "IntentType",
    "UserRequest",
    "DetectedIntent",
    "ContextSnapshot",
    "ActionPlan",
    "ExecutionResult",
    "ContextEngine",
    "get_context_engine",
    "SystemContext",
    "DesktopContext",
    "UserContext",
    "EnvironmentContext",
    "HealthMonitor",
    "HealthStatus",
    "get_health_monitor",
    "get_health_status",
    "RecoveryManager",
    "RecoveryRecord",
    "get_recovery_manager",
]