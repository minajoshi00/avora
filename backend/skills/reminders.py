import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from ..app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH

TASKS_FILE = APP_DATA_DIR / "reminders.json"
_lock = threading.RLock()
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_tasks():
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_tasks(tasks):
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, "w", encoding="utf-8") as handle:
            json.dump(tasks, handle, indent=2)
        return True
    except Exception:
        return False


def create_timer(text: str, minutes: int):
    if minutes <= 0:
        return "Please provide a positive duration."
    with _lock:
        tasks = _load_tasks()
        task = {
            "id": len(tasks) + 1,
            "text": str(text or "Timer").strip(),
            "minutes": int(minutes),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        tasks.append(task)
        _save_tasks(tasks)
        return f"Timer created for {minutes} minute(s): {task['text']}"


def list_timers():
    with _lock:
        tasks = _load_tasks()
        return [f"{item['id']}. {item['text']} ({item['minutes']} min)" for item in tasks]


def cancel_timer(text: str):
    with _lock:
        tasks = _load_tasks()
        if not tasks:
            return "You don't have any timers to cancel."
        task_id = None
        try:
            task_id = int(str(text).split()[-1])
        except ValueError:
            task_id = None
        if task_id is None:
            tasks.pop(0)
        else:
            tasks = [task for task in tasks if task.get("id") != task_id]
        _save_tasks(tasks)
        return "Timer cancelled."
