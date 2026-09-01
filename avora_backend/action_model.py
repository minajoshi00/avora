# ============================================================
# ACTION MODEL — AVORA AGENT MODE
# ============================================================
# Validated action representation used by the Agent Orchestrator.
# Passes validation before execution. Never replaces ActionPlanner
# or Skill Registry — integrates with them.
# ============================================================

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, Optional


class RiskLevel(Enum):
    """Risk classification for actions — determines confirmation requirements."""
    LOW = auto()       # open application, open website, search, read file
    MEDIUM = auto()    # move files, rename files, send messages, change settings
    HIGH = auto()      # delete files, financial transactions, account changes, irreversible actions


class ActionType(Enum):
    """Structured action types the agent can execute."""
    # Application actions
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    ACTIVATE_APPLICATION = "activate_application"

    # URL / Browser actions
    OPEN_URL = "open_url"
    NAVIGATE_TO = "navigate_to"
    SEARCH_WEB = "search_web"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"

    # File / System actions
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    WRITE_FILE = "write_file"
    MOVE_FILE = "move_file"
    RENAME_FILE = "rename_file"
    CREATE_FOLDER = "create_folder"
    DELETE_FILE = "delete_file"
    LIST_DIRECTORY = "list_directory"

    # Interaction actions
    CLICK = "click"
    TYPE = "type"
    KEY_PRESS = "key_press"
    KEY_COMBINATION = "key_combination"

    # System actions
    SEND_MESSAGE = "send_message"
    CHANGE_SETTING = "change_setting"
    GET_PROCESS_LIST = "get_process_list"
    GET_ACTIVE_WINDOW = "get_active_window"

    # Observation actions
    INSPECT_SCREEN = "inspect_screen"
    GET_SCREENSHOT = "getscreenshot"
    GET_PROCESS_STATE = "get_process_state"


# -----------------------------------------------------------------
# Action model
# -----------------------------------------------------------------

class Action:
    """
    A validated, structured action representation for Agent Mode.

    Every action contains metadata required for execution, validation,
    observation, and verification. The LLM generates structured actions
    of this type — they are NOT executed arbitrarily.

    Attributes:
        action_type: The type of action (from ActionType enum).
        target: The target of the action (application name, URL, file path, etc.).
        parameters: Additional parameters needed for execution.
        expected_result: What success looks like (used by verifier).
        risk_level: RiskLevel determining confirmation requirements.
        timeout: Maximum seconds before the action is considered timed out.
        retry_policy: How many times to retry on failure.
        metadata: Optional free-form key-value dict for extra context.
    """

    def __init__(
        self,
        action_type: ActionType,
        target: str,
        *,
        parameters: Optional[Dict[str, Any]] = None,
        expected_result: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        timeout: Optional[float] = None,
        retry_policy: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.action_type = action_type
        self.target = target
        self.parameters = parameters or {}
        self.expected_result = expected_result or self._default_expected_result()
        self.risk_level = risk_level
        self.timeout = timeout or self._default_timeout()
        self.retry_policy = max(0, retry_policy)  # bounded below 0
        self.metadata = metadata or {}

    # -----------------------------------------------------------------
    # Default derivations per action type
    # -----------------------------------------------------------------

    def _default_expected_result(self) -> str:
        """Return a sensible default expected result based on action type."""
        defaults: Dict[ActionType, str] = {
            ActionType.OPEN_APPLICATION: "Application window visible",
            ActionType.OPEN_URL: "Expected page/domain loaded",
            ActionType.SEARCH_WEB: "Search results page loaded",
            ActionType.CLOSE_APPLICATION: "Application process no longer running",
            ActionType.READ_FILE: "File content read successfully",
            ActionType.CREATE_FILE: "File exists with requested content",
            ActionType.WRITE_FILE: "File exists with requested content",
            ActionType.MOVE_FILE: "Destination file exists, source removed",
            ActionType.RENAME_FILE: "Old name absent, new name exists",
            ActionType.CREATE_FOLDER: "New folder exists at path",
            ActionType.DELETE_FILE: "File no longer exists at path",
            ActionType.CLICK: "UI element activated/clicked",
            ActionType.TYPE: "Text entered into target field",
            ActionType.NAVIGATE_TO: "Target URL/page loaded",
            ActionType.SEND_MESSAGE: "Message sent confirmation visible",
            ActionType.CHANGE_SETTING: "Setting changed successfully",
        }
        return defaults.get(self.action_type, "Action completed successfully")

    def _default_timeout(self) -> float:
        """Return a sensible default timeout based on risk level."""
        defaults: Dict[RiskLevel, float] = {
            RiskLevel.LOW: 10.0,
            RiskLevel.MEDIUM: 30.0,
            RiskLevel.HIGH: 60.0,
        }
        return defaults.get(self.risk_level, 30.0)

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def is_valid(self) -> bool:
        """Return True if the action passes all validation checks."""
        if not isinstance(self.action_type, ActionType):
            return False
        if not self.target or not isinstance(self.target, str):
            return False
        if not isinstance(self.parameters, dict):
            return False
        if not isinstance(self.risk_level, RiskLevel):
            return False
        if self.timeout is not None and self.timeout <= 0:
            return False
        if self.retry_policy < 0:
            return False
        return True

    def validate_for_execution(self) -> Optional[str]:
        """
        Validate the action for execution context.

        Returns None if valid, or an error message string if invalid.
        Called by the executor before dispatching to skills.
        """
        if not self.is_valid():
            return "Action is not valid per schema"

        # HIGH risk actions require explicit confirmation context
        if self.risk_level == RiskLevel.HIGH and not self.metadata.get("explicit_confirmation"):
            return f"HIGH risk action '{self.action_type.value}' requires explicit user confirmation"

        # MEDIUM risk actions may require contextual confirmation
        if self.risk_level == RiskLevel.MEDIUM and not self.metadata.get("contextual_confirmation"):
            # Not strictly failing — just flagged for planner
            pass

        return None

    # -----------------------------------------------------------------
    # Risk-based classification helpers
    # -----------------------------------------------------------------

    def requires_confirmation(self) -> bool:
        """Return True if this action requires user confirmation."""
        if self.risk_level == RiskLevel.HIGH:
            return True
        if self.risk_level == RiskLevel.MEDIUM:
            return not self.metadata.get("auto_execute", False)
        return False  # LOW risk never requires confirmation

    def is_timeout_bound(self) -> bool:
        """Return True if the action has a finite timeout."""
        return self.timeout is not None and self.timeout > 0

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the action to a dictionary."""
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "parameters": self.parameters,
            "expected_result": self.expected_result,
            "risk_level": self.risk_level.name,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Action:
        """Deserialize an action from a dictionary."""
        action_type = ActionType(data.get("action_type", "open_url"))
        try:
            action_type = ActionType(data["action_type"])
        except (ValueError, KeyError):
            pass

        risk_level = RiskLevel[data.get("risk_level", "MEDIUM").upper()]

        return cls(
            action_type=action_type,
            target=data.get("target", ""),
            parameters=data.get("parameters", {}),
            expected_result=data.get("expected_result"),
            risk_level=risk_level,
            timeout=data.get("timeout"),
            retry_policy=data.get("retry_policy", 0),
            metadata=data.get("metadata", {}),
        )

    # -----------------------------------------------------------------
    # Convenient representations
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Action type={self.action_type.value} "
            f"target={self.target!r} "
            f"risk={self.risk_level.name} "
            f"timeout={self.timeout}s>"
        )

    def __str__(self) -> str:
        return (
            f"{self.action_type.value}("
            f"target={self.target}, "
            f"risk={self.risk_level.name}, "
            f"timeout={self.timeout}s, "
            f"retry={self.retry_policy})"
        )


# -----------------------------------------------------------------
# Convenience constructors
# -----------------------------------------------------------------

def open_application(
    target: str,
    *,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create an OPEN_APPLICATION action with sensible defaults."""
    return Action(
        action_type=ActionType.OPEN_APPLICATION,
        target=target,
        expected_result=f"Application window visible: {target}",
        risk_level=RiskLevel.LOW,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )


def open_url(
    target: str,
    *,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create an OPEN_URL action with sensible defaults."""
    return Action(
        action_type=ActionType.OPEN_URL,
        target=target,
        expected_result=f"Expected page/domain loaded: {target}",
        risk_level=RiskLevel.LOW,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )


def search_web(
    query: str,
    *,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create a SEARCH_WEB action with sensible defaults."""
    return Action(
        action_type=ActionType.SEARCH_WEB,
        target=query,
        expected_result="Search results page loaded",
        risk_level=RiskLevel.LOW,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )


def move_file(
    source: str,
    target: str,
    *,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create a MOVE_FILE action with sensible defaults."""
    return Action(
        action_type=ActionType.MOVE_FILE,
        target=target,
        parameters={"source": source},
        expected_result="Destination file exists, source removed",
        risk_level=RiskLevel.MEDIUM,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )


def click_action(
    target: str,
    *,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create a CLICK action with sensible defaults."""
    return Action(
        action_type=ActionType.CLICK,
        target=target,
        expected_result="UI element activated/clicked",
        risk_level=RiskLevel.MEDIUM,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )


def type_action(
    text: str,
    *,
    target: Optional[str] = None,
    timeout: Optional[float] = None,
    retry_policy: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Action:
    """Create a TYPE action with sensible defaults."""
    params: Dict[str, Any] = {"text": text}
    if target:
        params["target"] = target
    return Action(
        action_type=ActionType.TYPE,
        target=target or "input_field",
        parameters=params,
        expected_result="Text entered into target field",
        risk_level=RiskLevel.LOW,
        timeout=timeout,
        retry_policy=retry_policy,
        metadata=metadata,
    )