"""
============================================================
AVORA Core Module — INTERNAL / EXPERIMENTAL
============================================================

Core system components for the AVORA AI desktop companion.

Active runtime paths (verified wired):
- context_engine + context_provider: via ai_logic.get_context()
- companion_intelligence + activity_monitor + screen_awareness: via main.py

Internal/experimental (not wired to main ai_logic pipeline;
do NOT claim as active user-facing features without integration):
- intelligence_engine / avora_intelligence: alternative pipeline (duplicates ai_logic)
- health_monitor / recovery_manager / provider_abstraction: diagnostic helpers
Keep these internal until explicitly integrated and tested.
"""

from core.intelligence_engine import (
    IntelligenceEngine,
    get_intelligence_engine,
    IntentType,
    UserRequest,
    DetectedIntent,
    TaskContext,
    TaskPlan,
    TaskResult,
    TaskEntity,
    TaskAction,
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
    "TaskContext",
    "TaskPlan",
    "TaskResult",
    "TaskEntity",
    "TaskAction",
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