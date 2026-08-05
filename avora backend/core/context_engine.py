"""
============================================================
AVORA Context Engine
============================================================

Continuously collects desktop context without blocking the UI.

Provides a single, clean API for other modules to access
comprehensive system and user state information.

Context Types:
- System: CPU, memory, battery, network
- Desktop: Files, folders, processes
- User: Time, location, preferences
- Environment: Displays, audio, connections
"""

import os
import re
import time
import socket
import logging
import threading
import subprocess
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from app_database import get_database

logger = logging.getLogger("ContextEngine")


@dataclass
class SystemContext:
    """System-level context information."""
    cpu_usage: float = 0.0
    memory_total_mb: float = 0.0
    memory_used_mb: float = 0.0
    memory_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    battery_level: Optional[int] = None
    is_battery_powered: bool = False
    is_charging: Optional[bool] = None
    wifi_connected: bool = False
    wifi_ssid: Optional[str] = None
    external_ip: Optional[str] = None


@dataclass
class DesktopContext:
    """Desktop and file system context."""
    active_window_title: Optional[str] = None
    active_process_name: Optional[str] = None
    running_processes: List[str] = field(default_factory=list)
    desktop_files: List[Dict[str, str]] = field(default_factory=list)
    recently_modified: List[str] = field(default_factory=list)
    downloads_count: int = 0
    clipboard_text: Optional[str] = None
    clipboard_type: Optional[str] = None


@dataclass
class UserContext:
    """User-specific context information."""
    time_of_day: int = field(default_factory=lambda: datetime.now().hour)
    day_of_week: int = field(default_factory=lambda: datetime.now().weekday())
    is_weekend: bool = field(default_factory=lambda: datetime.now().weekday() >= 5)
    local_ip: Optional[str] = None
    hostname: Optional[str] = None
    first_boot_time: Optional[float] = None
    session_duration: float = 0.0
    idle_minutes: float = 0.0


@dataclass
class EnvironmentContext:
    """Environment and peripheral context."""
    displays: List[Dict[str, Any]] = field(default_factory=list)
    audio_devices: List[str] = field(default_factory=list)
    headphones_connected: bool = False
    active_audio_device: Optional[str] = None
    has_multiple_users: bool = False
    lock_screen: bool = False


class ContextEngine:
    """
    Continuously collects and provides desktop context.
    
    Uses background workers to avoid blocking the UI.
    Caches results for fast retrieval.
    """
    
    def __init__(self, update_interval: float = 5.0):
        self._update_interval = update_interval
        self._lock = threading.RLock()
        
        self._system: SystemContext = SystemContext()
        self._desktop: DesktopContext = DesktopContext()
        self._user: UserContext = UserContext()
        self._environment: EnvironmentContext = EnvironmentContext()
        
        self._last_update: float = 0
        self._update_timestamps = {
            "system": 0,
            "desktop": 0,
            "user": 0,
            "environment": 0,
        }
        
        self._cache_ttl = 3.0
        
        self._collectors = {
            "system": self._collect_system,
            "desktop": self._collect_desktop,
            "user": self._collect_user,
            "environment": self._collect_environment,
        }
        
        self._running = False
        self._worker: Optional[threading.Thread] = None
        
        self._start_time = time.time()
        
        self._db = get_database()
        
        logger.debug("Context Engine initialized")
    
    def start(self):
        """Start the background context collection."""
        if self._running:
            return
        
        with self._lock:
            self._running = True
            self._worker = threading.Thread(
                target=self._background_update,
                daemon=True,
                name="ContextEngine"
            )
            self._worker.start()
            logger.info("Context Engine started")
    
    def stop(self):
        """Stop the background context collection."""
        self._running = False
        if self._worker:
            self._worker.join(timeout=1.0)
        logger.info("Context Engine stopped")
    
    def _background_update(self):
        """Background thread for periodic updates."""
        while self._running:
            try:
                self._update_all_contexts()
            except Exception as e:
                logger.debug(f"Context update error: {e}")
            
            time.sleep(self._update_interval)
    
    def _update_all_contexts(self):
        """Update all context types."""
        now = time.time()
        
        if now - self._update_timestamps["system"] > self._cache_ttl:
            try:
                self._system = self._collect_system()
                self._update_timestamps["system"] = now
            except Exception as e:
                logger.debug(f"System context error: {e}")
        
        if now - self._update_timestamps["desktop"] > self._cache_ttl:
            try:
                self._desktop = self._collect_desktop()
                self._update_timestamps["desktop"] = now
            except Exception as e:
                logger.debug(f"Desktop context error: {e}")
        
        if now - self._update_timestamps["user"] > self._cache_ttl:
            try:
                self._user = self._collect_user()
                self._update_timestamps["user"] = now
            except Exception as e:
                logger.debug(f"User context error: {e}")
        
        if now - self._update_timestamps["environment"] > self._cache_ttl:
            try:
                self._environment = self._collect_environment()
                self._update_timestamps["environment"] = now
            except Exception as e:
                logger.debug(f"Environment context error: {e}")
        
        self._last_update = now
    
    def _collect_system(self) -> SystemContext:
        """Collect system-level information."""
        ctx = SystemContext()
        
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=0.1)
            ctx.cpu_usage = cpu
            
            mem = psutil.virtual_memory()
            ctx.memory_total_mb = mem.total / (1024 * 1024)
            ctx.memory_used_mb = mem.used / (1024 * 1024)
            ctx.memory_usage_percent = mem.percent
            
            ctx.battery_level = mem.battery if hasattr(mem, 'battery') and mem.battery else None
            
            if hasattr(psutil, 'sensors_battery') and psutil.sensors_battery():
                bat = psutil.sensors_battery()
                if bat:
                    ctx.battery_level = bat.percent
                    ctx.is_battery_powered = bat.power_plugged
                    ctx.is_charging = bat.power_plugged
            
            if os.name == 'nt':
                try:
                    net = psutil.net_if_addrs()
                    for iface, addrs in net.items():
                        for addr in addrs:
                            if addr.family == socket.AF_INET:
                                ctx.wifi_connected = True
                                break
                except Exception:
                    pass
                    
        except ImportError:
            pass
        
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, shell=False
            )
            if result.returncode == 0:
                ctx.wifi_connected = "Established" in result.stdout or "LISTENING" in result.stdout
        except Exception:
            pass
        
        ctx.local_ip = self._get_local_ip()
        
        return ctx
    
    def _collect_desktop(self) -> DesktopContext:
        """Collect desktop and file system context."""
        ctx = DesktopContext()
        
        ctx.local_ip = self._get_local_ip()
        
        if os.name == 'nt':
            try:
                import psutil
                
                active_win = subprocess.run(
                    ["powershell", "Get-Process | Sort-Object -Property MainWindowHandle | Select-Object -First 1 -ExpandProperty ProcessName"],
                    capture_output=True, text=True, shell=False
                )
                if active_win.returncode == 0:
                    ctx.active_process_name = active_win.stdout.strip()
                
                try:
                    import psutil
                    for proc in list(psutil.process_iter(['name', 'pid']))[:10]:
                        try:
                            if proc.info['pid']:
                                ctx.running_processes.append(proc.info['name'])
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception:
                    pass
                
            except Exception:
                pass
        
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            try:
                ctx.downloads_count = len(list(downloads.glob("*")))
            except Exception:
                pass
        
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            try:
                items = list(desktop.iterdir())[:20]
                for item in items:
                    if item.is_file():
                        mtime = item.stat().st_mtime
                        if mtime > time.time() - 3600:
                            ctx.recent_modified.append(str(item))
                        ctx.desktop_files.append({
                            "name": item.name,
                            "path": str(item),
                            "modified": mtime,
                        })
            except Exception:
                pass
        
        return ctx
    
    def _collect_user(self) -> UserContext:
        """Collect user-specific context."""
        ctx = UserContext()
        
        now = datetime.now()
        ctx.time_of_day = now.hour
        ctx.day_of_week = now.weekday()
        ctx.is_weekend = ctx.day_of_week >= 5
        
        ctx.hostname = socket.gethostname() if socket else None
        ctx.local_ip = self._get_local_ip()
        
        ctx.session_duration = time.time() - self._start_time
        
        ctx.idle_minutes = self._get_idle_time()
        
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'login' in proc.info['name'].lower():
                    ctx.first_boot_time = self._start_time
                    break
        except Exception:
            pass
        
        return ctx
    
    def _collect_environment(self) -> EnvironmentContext:
        """Collect environment context."""
        ctx = EnvironmentContext()
        
        try:
            import psutil
            
            gpus = psutil.gpu_devices() if hasattr(psutil, 'gpu_devices') else []
            if gpus:
                ctx.displays.append({
                    "primary": True,
                    "resolution": "unknown",
                })
            
            for i in range(2):
                ctx.displays.append({
                    "index": i,
                    "primary": i == 0,
                })
        except Exception:
            ctx.displays = [{"index": 0, "primary": True}]
        
        audio_devs = []
        try:
            result = subprocess.run(
                ["powershell", "Get-CimInstance -ClassName Win32_SoundDevice | Select-Object Name"],
                capture_output=True, text=True, shell=False
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        audio_devs.append(line.strip())
        except Exception:
            pass
        ctx.audio_devices = audio_devs[:5]
        
        ctx.headphones_connected = len(audio_devs) > 0
        
        return ctx
    
    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address."""
        try:
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True, text=True, shell=False
            )
            for line in result.stdout.split("\n"):
                if "IPv4 Address" in line or "IPv4" in line:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None
    
    def _get_idle_time(self) -> float:
        """Get user idle time in minutes."""
        try:
            import ctypes
            from ctypes import wintypes
            
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]
            
            GetLastInputInfo = ctypes.windll.kernel32.GetLastInputInfo
            GetLastInputInfo.restype = wintypes.BOOL
            
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            
            if GetLastInputInfo(ctypes.byref(lii)):
                milliseconds = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return milliseconds / 60000.0
        except Exception:
            pass
        
        return 0.0
    
    def get_context(self, types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get current context information.
        
        Args:
            types: List of context types to include. 
                   If None, returns all context types.
        
        Returns:
            Dictionary with requested context
        """
        now = time.time()
        
        if types is None or "system" in types:
            if now - self._update_timestamps["system"] > self._cache_ttl:
                self._system = self._collect_system()
                self._update_timestamps["system"] = now
        
        if types is None or "desktop" in types:
            if now - self._update_timestamps["desktop"] > self._cache_ttl:
                self._desktop = self._collect_desktop()
                self._update_timestamps["desktop"] = now
        
        if types is None or "user" in types:
            if now - self._update_timestamps["user"] > self._cache_ttl:
                self._user = self._collect_user()
                self._update_timestamps["user"] = now
        
        if types is None or "environment" in types:
            if now - self._update_timestamps["environment"] > self._cache_ttl:
                self._environment = self._collect_environment()
                self._update_timestamps["environment"] = now
        
        result = {}
        
        if types is None or "system" in types:
            result["system"] = self._system.__dict__
        if types is None or "desktop" in types:
            result["desktop"] = self._desktop.__dict__
        if types is None or "user" in types:
            result["user"] = self._user.__dict__
        if types is None or "environment" in types:
            result["environment"] = self._environment.__dict__
        
        result["timestamp"] = now
        result["last_update"] = self._last_update
        
        return result
    
    def get_active_app(self) -> Optional[str]:
        """Get the name of the currently active application."""
        return self._desktop.active_process_name
    
    def is_idle(self, threshold_minutes: float = 5.0) -> bool:
        """Check if user has been idle for the specified threshold."""
        return self._user.idle_minutes >= threshold_minutes
    
    def is_battery_low(self, threshold: int = 20) -> bool:
        """Check if battery level is below threshold."""
        if self._system.battery_level is None:
            return False
        return self._system.battery_level <= threshold
    
    def is_wifi_connected(self) -> bool:
        """Check if Wi-Fi is connected."""
        return self._system.wifi_connected
    
    def get_current_hour(self) -> int:
        """Get current hour of day."""
        return self._user.time_of_day


_engine = None

def get_context_engine() -> ContextEngine:
    """Get the singleton context engine."""
    global _engine
    if _engine is None:
        _engine = ContextEngine()
        _engine.start()
    return _engine


__all__ = [
    "ContextEngine",
    "get_context_engine",
    "SystemContext",
    "DesktopContext",
    "UserContext",
    "EnvironmentContext",
]