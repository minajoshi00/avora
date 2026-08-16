"""
====================================================================
                    WINDOWS SETTINGS SKILL
====================================================================

Universal Windows Settings and System Control Engine.

This skill allows the AI Friend to understand natural-language requests
and find the correct Windows location, utility, command, or action.

Supported:
    • Modern Windows Settings (ms-settings:)
    • Control Panel (.cpl)
    • Microsoft Management Console (.msc)
    • Windows utilities
    • Administrative tools
    • Common system commands
    • PowerShell actions
    • Installed application discovery
    • Application uninstall discovery
    • Windows settings search
    • Risk classification
    • Confirmation handling
    • Capability discovery

IMPORTANT:
    This module is intentionally conservative with dangerous actions.
    It does not blindly delete files, modify the registry, disable
    security protections, or perform destructive operations.

====================================================================
"""

from __future__ import annotations

import os
import re
import json
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows environments
    winreg = None


# ====================================================================
# CONFIGURATION
# ====================================================================

WINDOWS_ONLY = os.name == "nt"


# ====================================================================
# RESULT HELPERS
# ====================================================================

def success(message: str, **kwargs) -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        **kwargs,
    }


def failure(message: str, **kwargs) -> Dict[str, Any]:
    return {
        "success": False,
        "message": message,
        **kwargs,
    }


# ====================================================================
# RISK LEVELS
# ====================================================================

RISK_LEVELS = {
    "safe": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


# ====================================================================
# WINDOWS SETTINGS DATABASE
# ====================================================================

WINDOWS_SETTINGS = {

    # ---------------------------------------------------------------
    # SYSTEM
    # ---------------------------------------------------------------

    "system": {
        "aliases": [
            "system settings",
            "computer settings",
            "system information",
            "about my computer",
            "about this pc",
            "device information",
        ],
        "uri": "ms-settings:about",
        "risk": "safe",
    },

    "display": {
        "aliases": [
            "display settings",
            "screen settings",
            "monitor settings",
            "screen resolution",
            "display resolution",
            "scale settings",
            "scaling settings",
        ],
        "uri": "ms-settings:display",
        "risk": "safe",
    },

    "advanced_display": {
        "aliases": [
            "advanced display",
            "refresh rate",
            "monitor refresh rate",
            "display refresh rate",
            "screen refresh rate",
            "hdr settings",
        ],
        "uri": "ms-settings:display-advanced",
        "risk": "safe",
    },

    "graphics": {
        "aliases": [
            "graphics settings",
            "gpu settings",
            "graphics performance",
            "gpu performance",
        ],
        "uri": "ms-settings:display-advancedgraphics",
        "risk": "safe",
    },

    "sound": {
        "aliases": [
            "sound settings",
            "audio settings",
            "speaker settings",
            "microphone settings",
            "volume settings",
        ],
        "uri": "ms-settings:sound",
        "risk": "safe",
    },

    "volume_mixer": {
        "aliases": [
            "volume mixer",
            "app volume",
            "application volume",
            "individual app volume",
        ],
        "uri": "ms-settings:apps-volume",
        "risk": "safe",
    },

    "notifications": {
        "aliases": [
            "notifications",
            "notification settings",
            "app notifications",
            "windows notifications",
        ],
        "uri": "ms-settings:notifications",
        "risk": "safe",
    },

    "focus": {
        "aliases": [
            "focus settings",
            "focus assist",
            "do not disturb",
            "focus sessions",
        ],
        "uri": "ms-settings:quiethours",
        "risk": "safe",
    },

    "power": {
        "aliases": [
            "power settings",
            "battery settings",
            "power mode",
            "battery saver",
            "energy settings",
        ],
        "uri": "ms-settings:power",
        "risk": "safe",
    },

    "storage": {
        "aliases": [
            "storage settings",
            "disk space",
            "storage space",
            "hard drive space",
            "free space",
            "temporary files",
        ],
        "uri": "ms-settings:storagesense",
        "risk": "safe",
    },

    "storage_disks": {
        "aliases": [
            "disk management",
            "manage disks",
            "partitions",
            "hard drive partitions",
            "disk partitions",
        ],
        "command": "diskmgmt.msc",
        "risk": "medium",
    },

    "multitasking": {
        "aliases": [
            "multitasking",
            "snap windows",
            "window snapping",
            "multiple desktops",
        ],
        "uri": "ms-settings:multitasking",
        "risk": "safe",
    },

    "projecting": {
        "aliases": [
            "project screen",
            "wireless display",
            "screen projection",
            "cast screen",
        ],
        "uri": "ms-settings:project",
        "risk": "safe",
    },

    "remote_desktop": {
        "aliases": [
            "remote desktop",
            "remote access",
            "rdp settings",
        ],
        "uri": "ms-settings:remotedesktop",
        "risk": "medium",
    },

    "clipboard": {
        "aliases": [
            "clipboard settings",
            "clipboard history",
            "copy paste history",
        ],
        "uri": "ms-settings:clipboard",
        "risk": "safe",
    },

    "optional_features": {
        "aliases": [
            "optional features",
            "windows optional features",
            "windows features",
            "enable windows features",
        ],
        "uri": "ms-settings:optionalfeatures",
        "risk": "medium",
    },

    "activation": {
        "aliases": [
            "windows activation",
            "activation settings",
            "windows license",
            "product activation",
        ],
        "uri": "ms-settings:activation",
        "risk": "medium",
    },

    "troubleshoot": {
        "aliases": [
            "troubleshooting",
            "troubleshoot windows",
            "fix windows problems",
            "troubleshoot settings",
        ],
        "uri": "ms-settings:troubleshoot",
        "risk": "safe",
    },

    "recovery": {
        "aliases": [
            "recovery settings",
            "reset pc",
            "windows recovery",
            "recovery options",
        ],
        "uri": "ms-settings:recovery",
        "risk": "high",
    },

    "system_info": {
        "aliases": [
            "system information",
            "computer information",
            "hardware information",
            "pc specifications",
            "computer specs",
        ],
        "command": "msinfo32",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # NETWORK AND INTERNET
    # ---------------------------------------------------------------

    "network": {
        "aliases": [
            "network settings",
            "internet settings",
            "wifi settings",
            "ethernet settings",
            "network and internet",
        ],
        "uri": "ms-settings:network",
        "risk": "safe",
    },

    "wifi": {
        "aliases": [
            "wifi",
            "wi-fi",
            "wireless network",
            "wireless settings",
            "wifi networks",
        ],
        "uri": "ms-settings:network-wifi",
        "risk": "safe",
    },

    "wifi_known_networks": {
        "aliases": [
            "known wifi networks",
            "saved wifi networks",
            "saved wireless networks",
            "forget wifi network",
        ],
        "uri": "ms-settings:network-wifisettings",
        "risk": "medium",
    },

    "ethernet": {
        "aliases": [
            "ethernet",
            "wired network",
            "lan settings",
            "ethernet settings",
        ],
        "uri": "ms-settings:network-ethernet",
        "risk": "safe",
    },

    "vpn": {
        "aliases": [
            "vpn settings",
            "virtual private network",
            "vpn connections",
        ],
        "uri": "ms-settings:network-vpn",
        "risk": "medium",
    },

    "mobile_hotspot": {
        "aliases": [
            "mobile hotspot",
            "wifi hotspot",
            "internet hotspot",
            "share internet",
        ],
        "uri": "ms-settings:network-mobilehotspot",
        "risk": "medium",
    },

    "proxy": {
        "aliases": [
            "proxy settings",
            "internet proxy",
            "proxy server",
        ],
        "uri": "ms-settings:network-proxy",
        "risk": "medium",
    },

    "network_adapters": {
        "aliases": [
            "network adapters",
            "network adapter settings",
            "change adapter settings",
            "ethernet adapter",
            "wifi adapter",
            "network connections",
        ],
        "command": "ncpa.cpl",
        "risk": "medium",
    },

    "internet_properties": {
        "aliases": [
            "internet properties",
            "internet options",
            "internet explorer settings",
        ],
        "command": "inetcpl.cpl",
        "risk": "medium",
    },

    "network_reset": {
        "aliases": [
            "network reset",
            "reset network",
            "fix network",
            "reset internet settings",
        ],
        "uri": "ms-settings:network-reset",
        "risk": "high",
    },

    # ---------------------------------------------------------------
    # BLUETOOTH AND DEVICES
    # ---------------------------------------------------------------

    "bluetooth": {
        "aliases": [
            "bluetooth",
            "bluetooth settings",
            "bluetooth devices",
            "pair bluetooth",
        ],
        "uri": "ms-settings:bluetooth",
        "risk": "safe",
    },

    "printers": {
        "aliases": [
            "printers",
            "printer settings",
            "manage printers",
            "add printer",
        ],
        "uri": "ms-settings:printers",
        "risk": "medium",
    },

    "mouse": {
        "aliases": [
            "mouse settings",
            "mouse speed",
            "mouse pointer",
            "mouse properties",
        ],
        "uri": "ms-settings:mousetouchpad",
        "risk": "safe",
    },

    "keyboard": {
        "aliases": [
            "keyboard settings",
            "keyboard properties",
            "typing settings",
        ],
        "uri": "ms-settings:typing",
        "risk": "safe",
    },

    "touchpad": {
        "aliases": [
            "touchpad settings",
            "trackpad settings",
            "touchpad gestures",
        ],
        "uri": "ms-settings:devices-touchpad",
        "risk": "safe",
    },

    "usb": {
        "aliases": [
            "usb settings",
            "usb devices",
            "usb connections",
        ],
        "uri": "ms-settings:usb",
        "risk": "safe",
    },

    "autoplay": {
        "aliases": [
            "autoplay",
            "automatic media settings",
            "usb autoplay",
        ],
        "uri": "ms-settings:autoplay",
        "risk": "safe",
    },

    "device_manager": {
        "aliases": [
            "device manager",
            "hardware devices",
            "drivers",
            "manage drivers",
            "hardware manager",
            "device drivers",
        ],
        "command": "devmgmt.msc",
        "risk": "medium",
    },

    # ---------------------------------------------------------------
    # PERSONALIZATION
    # ---------------------------------------------------------------

    "personalization": {
        "aliases": [
            "personalization",
            "personalisation",
            "appearance settings",
            "customize windows",
        ],
        "uri": "ms-settings:personalization",
        "risk": "safe",
    },

    "background": {
        "aliases": [
            "wallpaper",
            "desktop background",
            "background picture",
            "change wallpaper",
        ],
        "uri": "ms-settings:personalization-background",
        "risk": "safe",
    },

    "colors": {
        "aliases": [
            "colors",
            "accent color",
            "windows colors",
            "theme colors",
        ],
        "uri": "ms-settings:colors",
        "risk": "safe",
    },

    "themes": {
        "aliases": [
            "themes",
            "windows themes",
            "theme settings",
            "change theme",
        ],
        "uri": "ms-settings:themes",
        "risk": "safe",
    },

    "lock_screen": {
        "aliases": [
            "lock screen",
            "lock screen settings",
            "lock screen wallpaper",
        ],
        "uri": "ms-settings:lockscreen",
        "risk": "safe",
    },

    "fonts": {
        "aliases": [
            "fonts",
            "font settings",
            "installed fonts",
        ],
        "uri": "ms-settings:fonts",
        "risk": "safe",
    },

    "start_menu": {
        "aliases": [
            "start menu",
            "start menu settings",
            "start settings",
        ],
        "uri": "ms-settings:personalization-start",
        "risk": "safe",
    },

    "taskbar": {
        "aliases": [
            "taskbar",
            "taskbar settings",
            "taskbar behavior",
        ],
        "uri": "ms-settings:taskbar",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # APPS
    # ---------------------------------------------------------------

    "installed_apps": {
        "aliases": [
            "installed apps",
            "installed programs",
            "applications",
            "manage applications",
            "apps list",
        ],
        "uri": "ms-settings:appsfeatures",
        "risk": "safe",
    },

    "default_apps": {
        "aliases": [
            "default apps",
            "default browser",
            "default application",
            "file associations",
        ],
        "uri": "ms-settings:defaultapps",
        "risk": "medium",
    },

    "startup_apps": {
        "aliases": [
            "startup apps",
            "startup programs",
            "programs that start with windows",
            "boot applications",
        ],
        "uri": "ms-settings:startupapps",
        "risk": "medium",
    },

    "app_features": {
        "aliases": [
            "programs and features",
            "uninstall programs",
            "remove programs",
            "uninstall application",
            "software uninstall",
        ],
        "command": "appwiz.cpl",
        "risk": "high",
    },

    "optional_app_features": {
        "aliases": [
            "app advanced options",
            "app repair",
            "app reset",
            "app permissions",
        ],
        "uri": "ms-settings:appsfeatures-app",
        "risk": "medium",
    },

    # ---------------------------------------------------------------
    # ACCOUNTS
    # ---------------------------------------------------------------

    "accounts": {
        "aliases": [
            "account settings",
            "accounts",
            "my account settings",
        ],
        "uri": "ms-settings:accounts",
        "risk": "medium",
    },

    "your_info": {
        "aliases": [
            "my account information",
            "your info",
            "profile information",
        ],
        "uri": "ms-settings:yourinfo",
        "risk": "safe",
    },

    "sign_in_options": {
        "aliases": [
            "sign in options",
            "login settings",
            "windows hello",
            "password settings",
            "pin settings",
        ],
        "uri": "ms-settings:signinoptions",
        "risk": "high",
    },

    "family": {
        "aliases": [
            "family settings",
            "family safety",
            "parental controls",
        ],
        "uri": "ms-settings:family-group",
        "risk": "medium",
    },

    "email_accounts": {
        "aliases": [
            "email accounts",
            "mail accounts",
            "accounts used by apps",
        ],
        "uri": "ms-settings:emailandaccounts",
        "risk": "medium",
    },

    # ---------------------------------------------------------------
    # TIME AND LANGUAGE
    # ---------------------------------------------------------------

    "date_time": {
        "aliases": [
            "date and time",
            "time settings",
            "clock settings",
            "change time",
            "change date",
        ],
        "uri": "ms-settings:dateandtime",
        "risk": "medium",
    },

    "language": {
        "aliases": [
            "language settings",
            "windows language",
            "display language",
        ],
        "uri": "ms-settings:regionlanguage",
        "risk": "medium",
    },

    "keyboard_language": {
        "aliases": [
            "keyboard language",
            "input language",
            "keyboard layout",
        ],
        "uri": "ms-settings:regionlanguage",
        "risk": "medium",
    },

    "speech": {
        "aliases": [
            "speech settings",
            "voice recognition",
            "speech language",
        ],
        "uri": "ms-settings:speech",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # GAMING
    # ---------------------------------------------------------------

    "gaming": {
        "aliases": [
            "gaming settings",
            "game settings",
            "windows gaming",
        ],
        "uri": "ms-settings:gaming",
        "risk": "safe",
    },

    "game_bar": {
        "aliases": [
            "game bar",
            "xbox game bar",
            "gaming overlay",
        ],
        "uri": "ms-settings:gaming-gamebar",
        "risk": "safe",
    },

    "game_mode": {
        "aliases": [
            "game mode",
            "gaming performance mode",
        ],
        "uri": "ms-settings:gaming-gamemode",
        "risk": "safe",
    },

    "captures": {
        "aliases": [
            "game recording",
            "screen recording",
            "game captures",
            "recording settings",
        ],
        "uri": "ms-settings:gaming-gamedvr",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # PRIVACY AND SECURITY
    # ---------------------------------------------------------------

    "privacy": {
        "aliases": [
            "privacy settings",
            "privacy",
            "windows privacy",
        ],
        "uri": "ms-settings:privacy",
        "risk": "medium",
    },

    "location_privacy": {
        "aliases": [
            "location privacy",
            "location services",
            "location settings",
        ],
        "uri": "ms-settings:privacy-location",
        "risk": "medium",
    },

    "camera_privacy": {
        "aliases": [
            "camera privacy",
            "camera permissions",
            "camera access",
        ],
        "uri": "ms-settings:privacy-webcam",
        "risk": "medium",
    },

    "microphone_privacy": {
        "aliases": [
            "microphone privacy",
            "microphone permissions",
            "microphone access",
        ],
        "uri": "ms-settings:privacy-microphone",
        "risk": "medium",
    },

    "notifications_privacy": {
        "aliases": [
            "notification privacy",
            "notification permissions",
        ],
        "uri": "ms-settings:privacy-notifications",
        "risk": "medium",
    },

    "windows_security": {
        "aliases": [
            "windows security",
            "security settings",
            "defender",
            "windows defender",
        ],
        "uri": "ms-settings:windowsdefender",
        "risk": "high",
    },

    "windows_update": {
        "aliases": [
            "windows update",
            "update windows",
            "system updates",
            "check for updates",
        ],
        "uri": "ms-settings:windowsupdate",
        "risk": "medium",
    },

    "windows_update_history": {
        "aliases": [
            "update history",
            "windows update history",
            "installed updates",
        ],
        "uri": "ms-settings:windowsupdate-history",
        "risk": "safe",
    },

    "firewall": {
        "aliases": [
            "firewall",
            "windows firewall",
            "firewall settings",
        ],
        "command": "firewall.cpl",
        "risk": "high",
    },

    "advanced_firewall": {
        "aliases": [
            "advanced firewall",
            "firewall rules",
            "inbound firewall rules",
            "outbound firewall rules",
        ],
        "command": "wf.msc",
        "risk": "critical",
    },

    # ---------------------------------------------------------------
    # CONTROL PANEL
    # ---------------------------------------------------------------

    "control_panel": {
        "aliases": [
            "control panel",
            "open control panel",
        ],
        "command": "control",
        "risk": "safe",
    },

    "mouse_properties": {
        "aliases": [
            "mouse properties",
            "advanced mouse settings",
        ],
        "command": "main.cpl",
        "risk": "safe",
    },

    "sound_control_panel": {
        "aliases": [
            "classic sound settings",
            "sound control panel",
            "old sound settings",
        ],
        "command": "mmsys.cpl",
        "risk": "safe",
    },

    "power_options": {
        "aliases": [
            "power options",
            "power plans",
            "advanced power settings",
        ],
        "command": "powercfg.cpl",
        "risk": "medium",
    },

    "system_properties": {
        "aliases": [
            "system properties",
            "advanced system settings",
            "environment variables",
            "computer name settings",
        ],
        "command": "sysdm.cpl",
        "risk": "high",
    },

    "date_time_control": {
        "aliases": [
            "classic date time settings",
            "date time control panel",
        ],
        "command": "timedate.cpl",
        "risk": "medium",
    },

    "fonts_control": {
        "aliases": [
            "classic fonts",
            "font control panel",
        ],
        "command": "control fonts",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # MMC ADMINISTRATIVE TOOLS
    # ---------------------------------------------------------------

    "services": {
        "aliases": [
            "services",
            "windows services",
            "background services",
            "manage services",
            "start service",
            "stop service",
        ],
        "command": "services.msc",
        "risk": "high",
    },

    "event_viewer": {
        "aliases": [
            "event viewer",
            "windows logs",
            "system logs",
            "application logs",
            "event logs",
        ],
        "command": "eventvwr.msc",
        "risk": "safe",
    },

    "task_scheduler": {
        "aliases": [
            "task scheduler",
            "scheduled tasks",
            "automatic tasks",
            "scheduled programs",
        ],
        "command": "taskschd.msc",
        "risk": "high",
    },

    "computer_management": {
        "aliases": [
            "computer management",
            "manage computer",
            "computer administration",
        ],
        "command": "compmgmt.msc",
        "risk": "high",
    },

    "performance_monitor": {
        "aliases": [
            "performance monitor",
            "system performance",
            "performance monitoring",
        ],
        "command": "perfmon.msc",
        "risk": "safe",
    },

    "resource_monitor": {
        "aliases": [
            "resource monitor",
            "system resources",
            "cpu memory disk network monitor",
        ],
        "command": "resmon",
        "risk": "safe",
    },

    "local_security_policy": {
        "aliases": [
            "local security policy",
            "security policy",
            "local security settings",
        ],
        "command": "secpol.msc",
        "risk": "critical",
    },

    "group_policy": {
        "aliases": [
            "group policy",
            "local group policy",
            "group policy editor",
        ],
        "command": "gpedit.msc",
        "risk": "critical",
    },

    "local_users_groups": {
        "aliases": [
            "local users",
            "local groups",
            "user management",
            "local user accounts",
        ],
        "command": "lusrmgr.msc",
        "risk": "critical",
    },

    "disk_management": {
        "aliases": [
            "disk management",
            "manage disks",
            "partition manager",
            "disk partitions",
        ],
        "command": "diskmgmt.msc",
        "risk": "critical",
    },

    # ---------------------------------------------------------------
    # SYSTEM UTILITIES
    # ---------------------------------------------------------------

    "task_manager": {
        "aliases": [
            "task manager",
            "running processes",
            "process manager",
            "cpu usage",
            "memory usage",
        ],
        "command": "taskmgr",
        "risk": "medium",
    },

    "registry_editor": {
        "aliases": [
            "registry editor",
            "windows registry",
            "regedit",
        ],
        "command": "regedit",
        "risk": "critical",
    },

    "command_prompt": {
        "aliases": [
            "command prompt",
            "cmd",
            "terminal",
        ],
        "command": "cmd",
        "risk": "medium",
    },

    "powershell": {
        "aliases": [
            "powershell",
            "open powershell",
            "powershell terminal",
        ],
        "command": "powershell",
        "risk": "high",
    },

    "windows_terminal": {
        "aliases": [
            "windows terminal",
            "terminal app",
        ],
        "command": "wt",
        "risk": "medium",
    },

    "file_explorer": {
        "aliases": [
            "file explorer",
            "windows explorer",
            "explorer",
            "browse files",
        ],
        "command": "explorer",
        "risk": "safe",
    },

    "system_configuration": {
        "aliases": [
            "system configuration",
            "msconfig",
            "boot configuration",
            "startup configuration",
        ],
        "command": "msconfig",
        "risk": "high",
    },

    "system_restore": {
        "aliases": [
            "system restore",
            "restore point",
            "system protection",
        ],
        "command": "rstrui",
        "risk": "high",
    },

    "disk_cleanup": {
        "aliases": [
            "disk cleanup",
            "clean temporary files",
            "clean disk",
        ],
        "command": "cleanmgr",
        "risk": "medium",
    },

    "character_map": {
        "aliases": [
            "character map",
            "special characters",
            "unicode characters",
        ],
        "command": "charmap",
        "risk": "safe",
    },

    "snipping_tool": {
        "aliases": [
            "snipping tool",
            "screenshot tool",
            "screen capture",
        ],
        "command": "snippingtool",
        "risk": "safe",
    },

    "remote_assistance": {
        "aliases": [
            "remote assistance",
            "windows remote assistance",
        ],
        "command": "msra",
        "risk": "high",
    },

    "memory_diagnostic": {
        "aliases": [
            "memory diagnostic",
            "ram test",
            "test ram",
            "windows memory diagnostic",
        ],
        "command": "mdsched.exe",
        "risk": "medium",
    },

    "directx_diagnostic": {
        "aliases": [
            "directx diagnostic",
            "dxdiag",
            "graphics diagnostic",
        ],
        "command": "dxdiag",
        "risk": "safe",
    },

    # ---------------------------------------------------------------
    # POWER AND SHUTDOWN
    # ---------------------------------------------------------------

    "shutdown": {
        "aliases": [
            "shutdown computer",
            "turn off computer",
            "shut down pc",
        ],
        "action": "shutdown",
        "risk": "high",
    },

    "restart": {
        "aliases": [
            "restart computer",
            "reboot computer",
            "restart pc",
        ],
        "action": "restart",
        "risk": "high",
    },

    "sleep": {
        "aliases": [
            "sleep computer",
            "put pc to sleep",
            "sleep mode",
        ],
        "action": "sleep",
        "risk": "medium",
    },

    "lock": {
        "aliases": [
            "lock computer",
            "lock pc",
            "lock windows",
        ],
        "action": "lock",
        "risk": "low",
    },

    # ---------------------------------------------------------------
    # INFORMATION
    # ---------------------------------------------------------------

    "ip_information": {
        "aliases": [
            "my ip address",
            "ip address",
            "network information",
            "show ip",
        ],
        "action": "ipconfig",
        "risk": "safe",
    },

    "system_information_command": {
        "aliases": [
            "system information command",
            "computer details",
            "system details",
        ],
        "action": "systeminfo",
        "risk": "safe",
    },

    "running_processes": {
        "aliases": [
            "running processes",
            "process list",
            "what is running",
        ],
        "action": "tasklist",
        "risk": "safe",
    },

    "network_configuration": {
        "aliases": [
            "network configuration",
            "network config",
            "ip configuration",
        ],
        "action": "ipconfig",
        "risk": "safe",
    },
}


# ====================================================================
# WINDOWS COMMAND DATABASE
# ====================================================================

WINDOWS_COMMANDS = {
    "ipconfig": ["ipconfig", "/all"],
    "systeminfo": ["systeminfo"],
    "tasklist": ["tasklist"],
    "whoami": ["whoami"],
    "hostname": ["hostname"],
    "ver": ["cmd", "/c", "ver"],
    "powercfg": ["powercfg", "/getactivescheme"],
}


# ====================================================================
# NORMALIZATION
# ====================================================================

def normalize_text(text: str) -> str:
    """
    Normalize user input for matching.
    """

    if not text:
        return ""

    text = text.lower().strip()

    replacements = {
        "wi fi": "wifi",
        "wi-fi": "wifi",
        "wi-fi": "wifi",
        "personalisation": "personalization",
        "programme": "program",
        "programmes": "programs",
        "applications": "apps",
        "computer": "pc",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text


# ====================================================================
# CAPABILITY SEARCH
# ====================================================================

def search_capabilities(
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search all known Windows capabilities using natural language.
    """

    query = normalize_text(query)

    if not query:
        return []

    query_words = set(query.split())
    results = []

    for capability_id, capability in WINDOWS_SETTINGS.items():

        aliases = capability.get("aliases", [])

        best_score = 0
        best_alias = ""

        for alias in aliases:

            alias_normalized = normalize_text(alias)
            alias_words = set(alias_normalized.split())

            score = 0

            if query == alias_normalized:
                score += 100

            if alias_normalized in query:
                score += 50

            if query in alias_normalized:
                score += 40

            common_words = query_words.intersection(alias_words)
            score += len(common_words) * 10

            if score > best_score:
                best_score = score
                best_alias = alias

        if best_score > 0:

            results.append({
                "id": capability_id,
                "score": best_score,
                "matched_alias": best_alias,
                "data": capability,
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:limit]


# ====================================================================
# FIND BEST CAPABILITY
# ====================================================================

def find_capability(
    query: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the best matching Windows capability.
    """

    results = search_capabilities(query, limit=1)

    if not results:
        return None

    return results[0]


# ====================================================================
# OPEN WINDOWS URI
# ====================================================================

def open_windows_uri(uri: str) -> Dict[str, Any]:
    """
    Open a modern Windows Settings URI.
    """

    if not WINDOWS_ONLY:
        return failure(
            "Windows Settings are only available on Windows."
        )

    if not uri:
        return failure("No Windows URI provided.")

    try:

        os.startfile(uri)

        return success(
            f"Opened Windows Settings: {uri}",
            uri=uri,
        )

    except Exception as exc:

        return failure(
            f"Could not open Windows Settings: {exc}",
            uri=uri,
        )


# ====================================================================
# OPEN WINDOWS COMMAND
# ====================================================================

def open_windows_command(command: str) -> Dict[str, Any]:
    """
    Open a Windows executable, .cpl, .msc, or utility.

    This uses shell execution because Windows utilities such as:
        ncpa.cpl
        services.msc
        devmgmt.msc
        control
        msconfig
    are shell-associated Windows tools.
    """

    if not WINDOWS_ONLY:
        return failure(
            "Windows commands are only available on Windows."
        )

    if not command:
        return failure("No Windows command provided.")

    try:

        subprocess.Popen(
            command,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        return success(
            f"Opened Windows tool: {command}",
            command=command,
        )

    except Exception as exc:

        return failure(
            f"Could not open Windows tool: {exc}",
            command=command,
        )


# ====================================================================
# RUN SAFE INFORMATION COMMAND
# ====================================================================

def run_information_command(
    command_name: str,
) -> Dict[str, Any]:
    """
    Run a predefined information-only Windows command.

    Only commands in WINDOWS_COMMANDS can be executed here.
    """

    if not WINDOWS_ONLY:
        return failure(
            "This command is only available on Windows."
        )

    command = WINDOWS_COMMANDS.get(command_name)

    if not command:
        return failure(
            f"Unknown information command: {command_name}"
        )

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        output = result.stdout.strip()

        if result.stderr:
            output += "\n" + result.stderr.strip()

        return success(
            output or "Command completed.",
            command=command_name,
            output=output,
        )

    except Exception as exc:

        return failure(
            f"Could not run command: {exc}",
            command=command_name,
        )


# ====================================================================
# POWER ACTIONS
# ====================================================================

def shutdown_windows(
    confirm: bool = False,
) -> Dict[str, Any]:

    if not confirm:
        return failure(
            "Shutdown requires confirmation.",
            requires_confirmation=True,
            action="shutdown",
        )

    try:

        subprocess.Popen(
            ["shutdown", "/s", "/t", "0"],
            shell=False,
        )

        return success(
            "Windows shutdown initiated."
        )

    except Exception as exc:

        return failure(
            f"Could not shut down Windows: {exc}"
        )


def restart_windows(
    confirm: bool = False,
) -> Dict[str, Any]:

    if not confirm:
        return failure(
            "Restart requires confirmation.",
            requires_confirmation=True,
            action="restart",
        )

    try:

        subprocess.Popen(
            ["shutdown", "/r", "/t", "0"],
            shell=False,
        )

        return success(
            "Windows restart initiated."
        )

    except Exception as exc:

        return failure(
            f"Could not restart Windows: {exc}"
        )


def lock_windows() -> Dict[str, Any]:

    if not WINDOWS_ONLY:
        return failure(
            "This action is only available on Windows."
        )

    try:

        subprocess.Popen(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            shell=False,
        )

        return success(
            "Windows has been locked."
        )

    except Exception as exc:

        return failure(
            f"Could not lock Windows: {exc}"
        )


def sleep_windows() -> Dict[str, Any]:

    if not WINDOWS_ONLY:
        return failure(
            "This action is only available on Windows."
        )

    try:

        subprocess.Popen(
            [
                "rundll32.exe",
                "powrprof.dll,SetSuspendState",
                "0",
                "1",
                "0",
            ],
            shell=False,
        )

        return success(
            "Sleep mode initiated."
        )

    except Exception as exc:

        return failure(
            f"Could not put Windows to sleep: {exc}"
        )


# ====================================================================
# INSTALLED APPLICATION DISCOVERY
# ====================================================================

UNINSTALL_REGISTRY_PATHS = [
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
    (
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
    (
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ),
]


def get_installed_applications() -> List[Dict[str, Any]]:
    """
    Discover installed applications from Windows Registry.

    This is used for searching applications and finding uninstall
    information. It does not uninstall anything automatically.
    """

    if not WINDOWS_ONLY:
        return []

    applications = []

    for root, path in UNINSTALL_REGISTRY_PATHS:

        try:

            with winreg.OpenKey(root, path) as registry_key:

                count = winreg.QueryInfoKey(registry_key)[0]

                for index in range(count):

                    try:

                        subkey_name = winreg.EnumKey(
                            registry_key,
                            index,
                        )

                        with winreg.OpenKey(
                            registry_key,
                            subkey_name,
                        ) as subkey:

                            try:
                                name = winreg.QueryValueEx(
                                    subkey,
                                    "DisplayName",
                                )[0]
                            except FileNotFoundError:
                                continue

                            if not name:
                                continue

                            def read_value(value_name: str) -> str:

                                try:
                                    return str(
                                        winreg.QueryValueEx(
                                            subkey,
                                            value_name,
                                        )[0]
                                    )
                                except Exception:
                                    return ""

                            applications.append({
                                "name": name,
                                "version": read_value(
                                    "DisplayVersion"
                                ),
                                "publisher": read_value(
                                    "Publisher"
                                ),
                                "install_location": read_value(
                                    "InstallLocation"
                                ),
                                "uninstall_string": read_value(
                                    "UninstallString"
                                ),
                            })

                    except Exception:
                        continue

        except Exception:
            continue

    unique_apps = {}

    for app in applications:

        name = app.get("name", "").strip().lower()

        if name and name not in unique_apps:
            unique_apps[name] = app

    return sorted(
        unique_apps.values(),
        key=lambda app: app["name"].lower(),
    )


def search_installed_applications(
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:

    query = normalize_text(query)

    if not query:
        return []

    applications = get_installed_applications()

    results = []

    for app in applications:

        name = normalize_text(
            app.get("name", "")
        )

        publisher = normalize_text(
            app.get("publisher", "")
        )

        score = 0

        if query == name:
            score += 100

        if query in name:
            score += 70

        if name in query:
            score += 50

        if query in publisher:
            score += 20

        if score > 0:

            results.append({
                "score": score,
                "application": app,
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:limit]


# ====================================================================
# APPLICATION UNINSTALL
# ====================================================================

def uninstall_application(
    application_name: str,
    confirm: bool = False,
) -> Dict[str, Any]:

    if not application_name:

        return failure(
            "Please specify the application to uninstall."
        )

    matches = search_installed_applications(
        application_name,
        limit=5,
    )

    if not matches:

        return failure(
            f"Could not find an installed application matching "
            f"'{application_name}'."
        )

    best_match = matches[0]["application"]

    if not confirm:

        return success(
            f"I found '{best_match['name']}'. "
            f"Please confirm that you want to uninstall it.",
            requires_confirmation=True,
            action="uninstall",
            application=best_match,
            matches=matches,
        )

    uninstall_string = best_match.get(
        "uninstall_string",
        "",
    )

    if not uninstall_string:

        return failure(
            f"No uninstall command was found for "
            f"'{best_match['name']}'."
        )

    try:

        subprocess.Popen(
            uninstall_string,
            shell=True,
        )

        return success(
            f"Started the uninstaller for "
            f"'{best_match['name']}'.",
            application=best_match,
        )

    except Exception as exc:

        return failure(
            f"Could not start uninstaller: {exc}"
        )


# ====================================================================
# SYSTEM CAPABILITY DISCOVERY
# ====================================================================

def discover_windows_capabilities() -> Dict[str, Any]:
    """
    Detect available Windows tools on the current computer.
    """

    if not WINDOWS_ONLY:
        return {
            "platform": platform.system(),
            "windows": False,
            "available_tools": [],
        }

    available_tools = []

    for capability_id, capability in WINDOWS_SETTINGS.items():

        command = capability.get("command")

        if not command:
            available_tools.append(capability_id)
            continue

        executable = command.split()[0]

        if (
            executable.endswith(".cpl")
            or executable.endswith(".msc")
        ):

            available_tools.append(capability_id)
            continue

        if shutil.which(executable):

            available_tools.append(capability_id)

    return {
        "platform": platform.system(),
        "windows": True,
        "version": platform.version(),
        "release": platform.release(),
        "available_tools": available_tools,
        "count": len(available_tools),
    }


# ====================================================================
# RISK CHECKING
# ====================================================================

def requires_confirmation(
    capability: Dict[str, Any],
) -> bool:

    risk = capability.get(
        "risk",
        "medium",
    )

    return risk in {
        "high",
        "critical",
    }


# ====================================================================
# EXECUTE CAPABILITY
# ====================================================================

def execute_capability(
    capability_id: str,
    confirm: bool = False,
) -> Dict[str, Any]:

    capability = WINDOWS_SETTINGS.get(
        capability_id
    )

    if not capability:

        return failure(
            f"Unknown Windows capability: {capability_id}"
        )

    risk = capability.get(
        "risk",
        "medium",
    )

    if (
        risk in {"high", "critical"}
        and not confirm
    ):

        return failure(
            f"This action requires confirmation because "
            f"its risk level is '{risk}'.",
            requires_confirmation=True,
            capability=capability_id,
            risk=risk,
        )

    if "uri" in capability:

        return open_windows_uri(
            capability["uri"]
        )

    if "command" in capability:

        return open_windows_command(
            capability["command"]
        )

    action = capability.get("action")

    if action == "shutdown":

        return shutdown_windows(
            confirm=confirm
        )

    if action == "restart":

        return restart_windows(
            confirm=confirm
        )

    if action == "sleep":

        return sleep_windows()

    if action == "lock":

        return lock_windows()

    if action in WINDOWS_COMMANDS:

        return run_information_command(
            action
        )

    return failure(
        f"No execution handler exists for "
        f"'{capability_id}'."
    )


# ====================================================================
# NATURAL LANGUAGE REQUEST HANDLER
# ====================================================================

def handle_windows_request(
    request: str,
    confirm: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for AI Friend.

    Example:

        handle_windows_request(
            "open network adapter settings"
        )

    Example:

        handle_windows_request(
            "show me my IP address"
        )

    Example:

        handle_windows_request(
            "uninstall Opera",
            confirm=False
        )
    """

    if not request:

        return failure(
            "No Windows request was provided."
        )

    request_normalized = normalize_text(
        request
    )

    # ---------------------------------------------------------------
    # APPLICATION UNINSTALL
    # ---------------------------------------------------------------

    uninstall_patterns = [
        r"uninstall (.+)",
        r"remove program (.+)",
        r"remove app (.+)",
        r"delete application (.+)",
    ]

    for pattern in uninstall_patterns:

        match = re.search(
            pattern,
            request_normalized,
        )

        if match:

            application_name = (
                match.group(1)
                .strip()
            )

            return uninstall_application(
                application_name,
                confirm=confirm,
            )

    # ---------------------------------------------------------------
    # SPECIAL POWER ACTIONS
    # ---------------------------------------------------------------

    if any(
        phrase in request_normalized
        for phrase in [
            "shut down",
            "shutdown",
            "turn off computer",
            "turn off pc",
        ]
    ):

        return shutdown_windows(
            confirm=confirm
        )

    if any(
        phrase in request_normalized
        for phrase in [
            "restart computer",
            "restart pc",
            "reboot computer",
            "reboot pc",
        ]
    ):

        return restart_windows(
            confirm=confirm
        )

    if any(
        phrase in request_normalized
        for phrase in [
            "lock computer",
            "lock pc",
            "lock windows",
        ]
    ):

        return lock_windows()

    # ---------------------------------------------------------------
    # SPECIAL INFORMATION REQUESTS
    # ---------------------------------------------------------------

    if any(
        phrase in request_normalized
        for phrase in [
            "my ip",
            "ip address",
            "network information",
        ]
    ):

        return run_information_command(
            "ipconfig"
        )

    if any(
        phrase in request_normalized
        for phrase in [
            "system information",
            "system info",
            "computer specs",
            "pc specs",
        ]
    ):

        return run_information_command(
            "systeminfo"
        )

    # ---------------------------------------------------------------
    # SEARCH WINDOWS CAPABILITIES
    # ---------------------------------------------------------------

    capability = find_capability(
        request_normalized
    )

    if not capability:

        return failure(
            "I could not find a matching Windows setting "
            "or system capability.",
            requires_clarification=True,
            suggestions=[
                "Try describing what you want to change.",
                "Example: 'open network adapter settings'.",
                "Example: 'manage Windows services'.",
                "Example: 'change display settings'.",
            ],
        )

    return execute_capability(
        capability["id"],
        confirm=confirm,
    )


# ====================================================================
# SIMPLE PUBLIC API
# ====================================================================

def open_setting(
    setting_name: str,
) -> Dict[str, Any]:

    capability = find_capability(
        setting_name
    )

    if not capability:

        return failure(
            f"Setting not found: {setting_name}"
        )

    return execute_capability(
        capability["id"],
        confirm=True,
    )


def get_setting_info(
    setting_name: str,
) -> Optional[Dict[str, Any]]:

    capability = find_capability(
        setting_name
    )

    if not capability:

        return None

    return {
        "id": capability["id"],
        "score": capability["score"],
        "matched_alias": capability["matched_alias"],
        **capability["data"],
    }


# ====================================================================
# TESTING
# ====================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("WINDOWS SETTINGS SKILL TEST")
    print("=" * 70)

    print("\nSystem:")
    print(discover_windows_capabilities())

    print("\nSearch:")
    print(search_capabilities(
        "where can I change my wifi adapter settings"
    ))

    print("\nInformation:")
    print(run_information_command(
        "ipconfig"
    ))

    print("\nInstalled applications:")
    apps = get_installed_applications()

    for app in apps[:10]:
        print(
            f"- {app['name']} "
            f"{app.get('version', '')}"
        )

    print("\n" + "=" * 70)