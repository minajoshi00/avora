from .skill_base import SKILL_REGISTRY, get_enabled_skills, BaseSkill

# Auto-load BaseSkill implementations so SKILL_REGISTRY is populated
# on first import without requiring explicit side-effect imports elsewhere.
try:
    from . import browser_skill  # noqa: F401
except Exception:
    pass
try:
    from . import launcher_skill  # noqa: F401
except Exception:
    pass
try:
    from . import system_skill  # noqa: F401
except Exception:
    pass

__all__ = ["SKILL_REGISTRY", "get_enabled_skills", "BaseSkill"]
