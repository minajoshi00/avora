# ============================================================
# system.py
# AI Friend - Advanced System Management Skill
# ============================================================

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from ..settings import get_setting


# ============================================================
# CONSTANTS
# ============================================================

WINDOWS = "Windows"

BYTES_IN_GB = 1024 ** 3


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _setting(
    name,
    default
):

    try:

        return get_setting(

            name,

            default

        )

    except Exception:

        return default


def _is_windows():

    return platform.system() == WINDOWS


def _format_gb(

    value

):

    return round(

        value / BYTES_IN_GB,

        2

    )


def _error_message(

    action,

    error

):

    if _setting(

        "system.show_detailed_errors",

        True

    ):

        return (

            f"Brooo, I couldn't {action} 😭\n"

            f"{error}"

        )


    return (

        f"Brooo, I couldn't {action} 😭"

    )


def _run_command(

    command,

    timeout=10

):

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

                0

            )

        )


        return (

            result.returncode == 0,

            result.stdout.strip(),

            result.stderr.strip()

        )


    except Exception as error:

        return (

            False,

            "",

            str(error)

        )


# ============================================================
# CPU INFORMATION
# ============================================================

def get_cpu_info():

    try:

        cpu_name = (

            platform.processor()

            or "Unknown CPU"

        )


        return (

            "🧠 CPU Information\n\n"

            f"Processor: {cpu_name}\n"

            f"System: {platform.system()}\n"

            f"Machine: {platform.machine()}"

        )


    except Exception as error:

        return _error_message(

            "get CPU information",

            error

        )


# ============================================================
# RAM INFORMATION
# ============================================================

def get_ram_info():

    try:

        import psutil


        memory = psutil.virtual_memory()


        return (

            "🧠 RAM Information\n\n"

            f"Total RAM: "

            f"{_format_gb(memory.total)} GB\n"

            f"Used RAM: "

            f"{_format_gb(memory.used)} GB\n"

            f"Available RAM: "

            f"{_format_gb(memory.available)} GB\n"

            f"Usage: "

            f"{memory.percent}%"

        )


    except ImportError:

        return (

            "Brooo, install psutil first:\n\n"

            "pip install psutil"

        )


    except Exception as error:

        return _error_message(

            "get RAM information",

            error

        )


# ============================================================
# CPU USAGE
# ============================================================

def get_cpu_usage():

    try:

        import psutil


        usage = psutil.cpu_percent(

            interval=1

        )


        return (

            "⚙️ CPU Usage\n\n"

            f"Current CPU usage: "

            f"{usage}%"

        )


    except ImportError:

        return (

            "Brooo, install psutil first:\n\n"

            "pip install psutil"

        )


    except Exception as error:

        return _error_message(

            "check CPU usage",

            error

        )


# ============================================================
# GPU INFORMATION
# ============================================================

def get_gpu_info():

    try:

        if not _is_windows():

            return (

                "🎮 GPU Information\n\n"

                "GPU detection is currently "

                "configured for Windows."

            )


        # ----------------------------------------------------
        # PRIMARY METHOD: POWERSHELL
        # ----------------------------------------------------

        powershell_command = [

            "powershell",

            "-NoProfile",

            "-ExecutionPolicy",

            "Bypass",

            "-Command",

            (

                "Get-CimInstance "

                "Win32_VideoController | "

                "Select-Object -ExpandProperty Name"

            )

        ]


        success, output, _ = _run_command(

            powershell_command

        )


        gpu_names = []


        if success and output:

            for line in output.splitlines():

                line = line.strip()


                if (

                    line

                    and line not in gpu_names

                ):

                    gpu_names.append(

                        line

                    )


        # ----------------------------------------------------
        # FALLBACK: WMIC
        # ----------------------------------------------------

        if not gpu_names:

            success, output, _ = _run_command(

                [

                    "wmic",

                    "path",

                    "win32_VideoController",

                    "get",

                    "Name"

                ]

            )


            if success and output:

                for line in output.splitlines():

                    line = line.strip()


                    if not line:

                        continue


                    if line.lower() == "name":

                        continue


                    if line not in gpu_names:

                        gpu_names.append(

                            line

                        )


        if not gpu_names:

            return (

                "🎮 GPU Information\n\n"

                "I couldn't detect your graphics processor."

            )


        return (

            "🎮 GPU Information\n\n"

            + "\n".join(

                (

                    f"Graphics Processor: "

                    f"{gpu}"

                )

                for gpu in gpu_names

            )

        )


    except Exception as error:

        return _error_message(

            "get GPU information",

            error

        )


# ============================================================
# STORAGE INFORMATION
# ============================================================

def get_storage_info():

    try:

        disk = shutil.disk_usage(

            os.path.expanduser(

                "~"

            )

        )


        return (

            "💾 Storage Information\n\n"

            f"Total: "

            f"{_format_gb(disk.total)} GB\n"

            f"Used: "

            f"{_format_gb(disk.total - disk.free)} GB\n"

            f"Free: "

            f"{_format_gb(disk.free)} GB"

        )


    except Exception as error:

        return _error_message(

            "check storage",

            error

        )


# ============================================================
# BATTERY STATUS
# ============================================================

def get_battery_status():

    try:

        import psutil


        battery = (

            psutil.sensors_battery()

        )


        if battery is None:

            return (

                "Brooo, I couldn't detect "

                "a battery 🔋"

            )


        if battery.power_plugged:

            status = (

                "Plugged in and charging 🔌"

            )

        else:

            status = (

                "Running on battery 🔋"

            )


        return (

            "🔋 Battery Status\n\n"

            f"Battery: "

            f"{battery.percent}%\n"

            f"Status: "

            f"{status}"

        )


    except ImportError:

        return (

            "Brooo, install psutil first:\n\n"

            "pip install psutil"

        )


    except Exception as error:

        return _error_message(

            "check battery status",

            error

        )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():

    try:

        return (

            "💻 System Information\n\n"

            f"Operating System: "

            f"{platform.system()}\n"

            f"Version: "

            f"{platform.version()}\n"

            f"Release: "

            f"{platform.release()}\n"

            f"Machine: "

            f"{platform.machine()}\n"

            f"Processor: "

            f"{platform.processor() or 'Unknown'}"

        )


    except Exception as error:

        return _error_message(

            "get system information",

            error

        )


# ============================================================
# CURRENT TIME
# ============================================================

def get_current_time():

    now = datetime.now()


    return (

        "🕒 Current Time\n\n"

        f"{now.strftime('%I:%M:%S %p')}\n\n"

        f"📅 Date: "

        f"{now.strftime('%A, %B %d, %Y')}"

    )


# ============================================================
# SCREENSHOT
# ============================================================

def take_screenshot(

    filename=None

):

    if not _setting(

        "system.allow_screenshots",

        True

    ):

        return (

            "📸 Screenshot access is disabled "

            "in Settings."

        )


    try:

        import pyautogui


        directory = _setting(

            "system.screenshot_directory",

            "screenshots"

        )


        directory = Path(

            directory

        )


        directory.mkdir(

            parents=True,

            exist_ok=True

        )


        if filename is None:

            timestamp = (

                datetime.now().strftime(

                    "%Y%m%d_%H%M%S"

                )

            )


            filename = (

                f"screenshot_{timestamp}.png"

            )


        filepath = (

            directory / filename

        )


        screenshot = (

            pyautogui.screenshot()

        )


        screenshot.save(

            filepath

        )


        return (

            "📸 Screenshot saved successfully!\n\n"

            f"Location: "

            f"{filepath.resolve()}"

        )


    except ImportError:

        return (

            "Brooo, install pyautogui first:\n\n"

            "pip install pyautogui"

        )


    except Exception as error:

        return _error_message(

            "take a screenshot",

            error

        )


# ============================================================
# LOCK COMPUTER
# ============================================================

def lock_computer():

    if not _setting(

        "system.allow_power_actions",

        True

    ):

        return (

            "🔒 Power actions are "

            "disabled in Settings."

        )


    try:

        if not _is_windows():

            return (

                "Brooo, computer locking is "

                "currently configured for "

                "Windows only."

            )


        success, _, _ = _run_command(

            [

                "rundll32.exe",

                "user32.dll,LockWorkStation"

            ]

        )


        return (

            "🔒 Computer locked successfully."

            if success

            else

            "Brooo, I couldn't lock "

            "the computer 😭"

        )


    except Exception as error:

        return _error_message(

            "lock the computer",

            error

        )


# ============================================================
# SHUTDOWN COMPUTER
# ============================================================

def shutdown_computer(

    delay=0

):

    if not _setting(

        "system.allow_power_actions",

        True

    ):

        return (

            "⏻ Power actions are "

            "disabled in Settings."

        )


    try:

        if not _is_windows():

            return (

                "Brooo, shutdown is currently "

                "configured for Windows only."

            )


        success, _, _ = _run_command(

            [

                "shutdown",

                "/s",

                "/t",

                str(

                    int(

                        delay

                    )

                )

            ]

        )


        return (

            "⏻ Computer shutdown initiated."

            if success

            else

            "Brooo, shutdown could "

            "not be started."

        )


    except Exception as error:

        return _error_message(

            "shut down the computer",

            error

        )


# ============================================================
# RESTART COMPUTER
# ============================================================

def restart_computer(

    delay=0

):

    if not _setting(

        "system.allow_power_actions",

        True

    ):

        return (

            "🔄 Power actions are "

            "disabled in Settings."

        )


    try:

        if not _is_windows():

            return (

                "Brooo, restart is currently "

                "configured for Windows only."

            )


        success, _, _ = _run_command(

            [

                "shutdown",

                "/r",

                "/t",

                str(

                    int(

                        delay

                    )

                )

            ]

        )


        return (

            "🔄 Computer restart initiated."

            if success

            else

            "Brooo, restart could "

            "not be started."

        )


    except Exception as error:

        return _error_message(

            "restart the computer",

            error

        )


# ============================================================
# CANCEL SHUTDOWN OR RESTART
# ============================================================

def cancel_shutdown():

    if not _setting(

        "system.allow_power_actions",

        True

    ):

        return (

            "⏹️ Power actions are "

            "disabled in Settings."

        )


    try:

        if not _is_windows():

            return (

                "Brooo, this feature is "

                "currently configured "

                "for Windows only."

            )


        success, _, _ = _run_command(

            [

                "shutdown",

                "/a"

            ]

        )


        return (

            "✅ Scheduled shutdown or "

            "restart cancelled."

            if success

            else

            "ℹ️ No scheduled shutdown "

            "was found."

        )


    except Exception as error:

        return _error_message(

            "cancel the scheduled action",

            error

        )


# ============================================================
# OPEN WINDOWS SETTINGS
# ============================================================

def open_settings():

    if not _setting(

        "system.allow_open_settings",

        True

    ):

        return (

            "⚙️ Opening system settings "

            "is disabled in Settings."

        )


    try:

        if not _is_windows():

            return (

                "Brooo, this feature is "

                "currently configured "

                "for Windows."

            )


        subprocess.Popen(

            [

                "explorer.exe",

                "ms-settings:"

            ],

            creationflags=getattr(

                subprocess,

                "CREATE_NO_WINDOW",

                0

            )

        )


        return (

            "⚙️ Opening Windows Settings."

        )


    except Exception as error:

        return _error_message(

            "open Windows Settings",

            error

        )


# ============================================================
# FULL SYSTEM STATUS
# ============================================================

def get_full_system_status():

    try:

        import psutil


        cpu = psutil.cpu_percent(

            interval=1

        )


        memory = (

            psutil.virtual_memory()

        )


        disk = shutil.disk_usage(

            os.path.expanduser(

                "~"

            )

        )


        result = (

            "💻 SYSTEM STATUS\n\n"

            f"⚙️ CPU Usage: "

            f"{cpu}%\n"

            f"🧠 RAM: "

            f"{_format_gb(memory.used)} / "

            f"{_format_gb(memory.total)} GB "

            f"({memory.percent}%)\n"

            f"💾 Free Storage: "

            f"{_format_gb(disk.free)} GB\n"

            f"🖥️ OS: "

            f"{platform.system()} "

            f"{platform.release()}"

        )


        battery = (

            psutil.sensors_battery()

        )


        if battery:

            result += (

                f"\n🔋 Battery: "

                f"{battery.percent}%"

            )


        return result


    except ImportError:

        return (

            "Brooo, install psutil first:\n\n"

            "pip install psutil"

        )


    except Exception as error:

        return _error_message(

            "get full system status",

            error

        )


# ============================================================
# FULL SYSTEM SPECIFICATIONS
# ============================================================

def get_full_system_information():

    return (

        get_system_info()

        + "\n\n"

        + get_cpu_info()

        + "\n\n"

        + get_ram_info()

        + "\n\n"

        + get_gpu_info()

        + "\n\n"

        + get_storage_info()

    )