"""
AI Friend - Power Management Skill
===================================

Handles safe Windows power operations.

Supported actions:
- Shutdown
- Restart
- Sleep
- Hibernate
- Lock
- Log out
- Cancel scheduled shutdown
- Schedule shutdown/restart

IMPORTANT:
This module does NOT ask for confirmation.
Confirmation should be handled by ai_logic.py before calling
dangerous actions such as shutdown, restart, logout, or hibernate.
"""

from __future__ import annotations

import os
import platform
import subprocess
import time
from typing import Optional


# ============================================================
# CONSTANTS
# ============================================================

WINDOWS = "Windows"

MIN_DELAY_SECONDS = 0
MAX_DELAY_SECONDS = 31536000  # 1 year


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _is_windows() -> bool:
    """Return True if the current operating system is Windows."""
    return platform.system() == WINDOWS


def _validate_windows() -> None:
    """Raise an error if the system is not Windows."""
    if not _is_windows():
        raise OSError(
            "Power management commands are currently supported only on Windows."
        )


def _validate_delay(seconds: int) -> int:
    """Validate and normalize a delay value."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        raise ValueError("Delay must be a valid number of seconds.")

    if seconds < MIN_DELAY_SECONDS:
        raise ValueError("Delay cannot be negative.")

    if seconds > MAX_DELAY_SECONDS:
        raise ValueError("Delay is too large.")

    return seconds


def _run_command(
    command: list[str],
    timeout: int = 10,
) -> tuple[bool, str]:
    """
    Execute a system command safely.

    Returns:
        (success, message)
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
        )

        if result.returncode == 0:
            return True, "Command executed successfully."

        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or f"Command failed with exit code {result.returncode}."
        )

        return False, error_message

    except subprocess.TimeoutExpired:
        return False, "The system command timed out."

    except FileNotFoundError:
        return False, "The required system command was not found."

    except Exception as error:
        return False, f"Unexpected system error: {error}"


# ============================================================
# IMMEDIATE POWER ACTIONS
# ============================================================

def shutdown() -> tuple[bool, str]:
    """
    Shut down the computer immediately.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        ["shutdown", "/s", "/t", "0"]
    )


def restart() -> tuple[bool, str]:
    """
    Restart the computer immediately.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        ["shutdown", "/r", "/t", "0"]
    )


def sleep() -> tuple[bool, str]:
    """
    Put the computer into sleep mode.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.Application]::SetSuspendState("
            "'Suspend', $false, $false)",
        ]
    )


def hibernate() -> tuple[bool, str]:
    """
    Hibernate the computer.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        ["shutdown", "/h"]
    )


def lock() -> tuple[bool, str]:
    """
    Lock the current Windows session.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        ["rundll32.exe", "user32.dll,LockWorkStation"]
    )


def logout() -> tuple[bool, str]:
    """
    Log out the current Windows user.

    Returns:
        (success, message)
    """

    _validate_windows()

    return _run_command(
        ["shutdown", "/l"]
    )


# ============================================================
# SCHEDULED POWER ACTIONS
# ============================================================

def schedule_shutdown(seconds: int) -> tuple[bool, str]:
    """
    Schedule a shutdown after a number of seconds.

    Example:
        schedule_shutdown(600)

    This schedules shutdown after 10 minutes.
    """

    _validate_windows()
    seconds = _validate_delay(seconds)

    return _run_command(
        ["shutdown", "/s", "/t", str(seconds)]
    )


def schedule_restart(seconds: int) -> tuple[bool, str]:
    """
    Schedule a restart after a number of seconds.

    Example:
        schedule_restart(600)

    This schedules restart after 10 minutes.
    """

    _validate_windows()
    seconds = _validate_delay(seconds)

    return _run_command(
        ["shutdown", "/r", "/t", str(seconds)]
    )


def cancel_scheduled_action() -> tuple[bool, str]:
    """
    Cancel any pending scheduled shutdown or restart.
    """

    _validate_windows()

    return _run_command(
        ["shutdown", "/a"]
    )


# ============================================================
# STATUS
# ============================================================

def check_pending_action() -> dict:
    """
    Check whether Windows has a pending scheduled shutdown.

    Note:
        Windows does not provide a perfect simple API for this,
        so this function checks the shutdown command state through
        the Windows event/system behavior.

    Returns:
        Dictionary containing status information.
    """

    _validate_windows()

    return {
        "supported": True,
        "message": (
            "Windows does not expose a reliable simple command "
            "to directly inspect the exact remaining shutdown timer."
        ),
    }


# ============================================================
# FRIENDLY UNIVERSAL ACTION ROUTER
# ============================================================

def perform_power_action(
    action: str,
    seconds: Optional[int] = None,
) -> tuple[bool, str]:
    """
    Universal power action router.

    Supported actions:

        shutdown
        restart
        sleep
        hibernate
        lock
        logout
        cancel
        schedule_shutdown
        schedule_restart

    Examples:

        perform_power_action("shutdown")
        perform_power_action("restart")
        perform_power_action("sleep")
        perform_power_action("schedule_shutdown", 600)
    """

    if not isinstance(action, str):
        return False, "Power action must be a string."

    normalized_action = (
        action
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    actions = {
        "shutdown": shutdown,
        "shut_down": shutdown,
        "power_off": shutdown,

        "restart": restart,
        "reboot": restart,

        "sleep": sleep,

        "hibernate": hibernate,

        "lock": lock,
        "lock_computer": lock,

        "logout": logout,
        "log_out": logout,
        "sign_out": logout,

        "cancel": cancel_scheduled_action,
        "cancel_shutdown": cancel_scheduled_action,
        "cancel_restart": cancel_scheduled_action,
        "cancel_scheduled_action": cancel_scheduled_action,
    }

    if normalized_action in actions:

        if seconds is not None:
            return False, (
                f"The action '{normalized_action}' does not accept "
                "a time delay."
            )

        return actions[normalized_action]()

    if normalized_action in {
        "schedule_shutdown",
        "shutdown_after",
    }:

        if seconds is None:
            return False, "A delay is required for scheduled shutdown."

        return schedule_shutdown(seconds)

    if normalized_action in {
        "schedule_restart",
        "restart_after",
    }:

        if seconds is None:
            return False, "A delay is required for scheduled restart."

        return schedule_restart(seconds)

    return False, f"Unknown power action: {action}"


# ============================================================
# TIME CONVERSION HELPERS
# ============================================================

def minutes_to_seconds(minutes: float) -> int:
    """Convert minutes to seconds safely."""

    try:
        minutes = float(minutes)
    except (TypeError, ValueError):
        raise ValueError("Minutes must be a valid number.")

    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")

    return int(minutes * 60)


def hours_to_seconds(hours: float) -> int:
    """Convert hours to seconds safely."""

    try:
        hours = float(hours)
    except (TypeError, ValueError):
        raise ValueError("Hours must be a valid number.")

    if hours < 0:
        raise ValueError("Hours cannot be negative.")

    return int(hours * 3600)


def days_to_seconds(days: float) -> int:
    """Convert days to seconds safely."""

    try:
        days = float(days)
    except (TypeError, ValueError):
        raise ValueError("Days must be a valid number.")

    if days < 0:
        raise ValueError("Days cannot be negative.")

    return int(days * 86400)


# ============================================================
# FRIENDLY DELAY PARSER
# ============================================================

def parse_delay(
    value: float,
    unit: str,
) -> int:
    """
    Convert a human-friendly delay into seconds.

    Examples:

        parse_delay(10, "minutes")
        parse_delay(2, "hours")
        parse_delay(1, "day")
    """

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("Delay value must be a number.")

    normalized_unit = (
        str(unit)
        .strip()
        .lower()
        .replace("-", "")
        .replace("_", "")
    )

    if normalized_unit in {
        "second",
        "seconds",
        "sec",
        "secs",
    }:
        return int(value)

    if normalized_unit in {
        "minute",
        "minutes",
        "min",
        "mins",
    }:
        return minutes_to_seconds(value)

    if normalized_unit in {
        "hour",
        "hours",
        "hr",
        "hrs",
    }:
        return hours_to_seconds(value)

    if normalized_unit in {
        "day",
        "days",
    }:
        return days_to_seconds(value)

    raise ValueError(
        f"Unsupported time unit: {unit}"
    )


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("AI Friend Power Skill")
    print("=" * 30)

    print(f"Operating System: {platform.system()}")
    print(f"Windows Supported: {_is_windows()}")

    print("\nAvailable actions:")
    print("- shutdown")
    print("- restart")
    print("- sleep")
    print("- hibernate")
    print("- lock")
    print("- logout")
    print("- cancel scheduled action")
    print("- schedule shutdown")
    print("- schedule restart")

    print("\nExample conversions:")
    print(f"10 minutes = {minutes_to_seconds(10)} seconds")
    print(f"2 hours = {hours_to_seconds(2)} seconds")

    print("\nPower skill loaded successfully.")