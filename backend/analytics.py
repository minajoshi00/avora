"""
AVORA Analytics & Telemetry System

Privacy-respecting analytics and usage tracking.
All data collection is optional and respects user privacy settings.
"""

from __future__ import annotations

import json
import platform
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class AnalyticsManager:
    """Manages analytics and telemetry data."""
    
    def __init__(self, app_data_dir: Path, app_version: str):
        self.app_data_dir = app_data_dir
        self.app_version = app_version
        self.analytics_file = app_data_dir / "analytics.json"
        
        # Privacy settings
        self.enabled = False
        self.anonymous_usage_data = False
        self.update_checks = True
        
        # User ID (anonymous)
        self.user_id = self._get_or_create_user_id()
        
        # Load settings
        self._load_settings()
    
    def _get_or_create_user_id(self) -> str:
        """Get or create an anonymous user ID."""
        user_id_file = self.app_data_dir / ".user_id"
        
        try:
            if user_id_file.exists():
                return user_id_file.read_text().strip()
            else:
                user_id = str(uuid.uuid4())
                user_id_file.write_text(user_id)
                return user_id
        except Exception:
            return str(uuid.uuid4())
    
    def _load_settings(self):
        """Load analytics settings."""
        try:
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.enabled = data.get('enabled', False)
                    self.anonymous_usage_data = data.get('anonymous_usage_data', False)
                    self.update_checks = data.get('update_checks', True)
        except Exception:
            pass
    
    def _save_settings(self):
        """Save analytics settings."""
        try:
            self.app_data_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'enabled': self.enabled,
                'anonymous_usage_data': self.anonymous_usage_data,
                'update_checks': self.update_checks,
            }
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ANALYTICS] Failed to save settings: {e}")
    
    def update_settings(self, enabled: bool, anonymous_usage: bool, update_checks: bool):
        """Update analytics settings."""
        self.enabled = enabled
        self.anonymous_usage_data = anonymous_usage
        self.update_checks = update_checks
        self._save_settings()
    
    def get_system_info(self) -> Dict:
        """Get anonymous system information."""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'app_version': self.app_version,
        }
    
    def track_event(self, event_name: str, properties: Dict = None):
        """
        Track an analytics event.
        Only tracks if analytics is enabled.
        """
        if not self.enabled or not self.anonymous_usage_data:
            return
        
        try:
            event = {
                'event': event_name,
                'user_id': self.user_id,
                'timestamp': datetime.now().isoformat(),
                'properties': properties or {},
            }
            
            # In production, this would send to an analytics service
            # For now, just log it
            print(f"[ANALYTICS] {event_name}: {properties}")
            
        except Exception as e:
            print(f"[ANALYTICS] Failed to track event: {e}")
    
    def track_app_launch(self):
        """Track app launch."""
        self.track_event('app_launch', self.get_system_info())
    
    def track_feature_usage(self, feature_name: str):
        """Track feature usage."""
        self.track_event('feature_used', {
            'feature': feature_name,
        })
    
    def track_error(self, error_type: str, error_message: str):
        """Track errors (anonymous)."""
        self.track_event('error', {
            'error_type': error_type,
            'error_message': error_message[:200],  # Limit length
        })
    
    def track_performance(self, metric_name: str, value: float):
        """Track performance metrics."""
        self.track_event('performance', {
            'metric': metric_name,
            'value': value,
        })
    
    def should_check_updates(self) -> bool:
        """Check if update checking is enabled."""
        return self.enabled and self.update_checks
    
    def track_update_check(self, update_available: bool, latest_version: str = None):
        """Track update check."""
        self.track_event('update_check', {
            'update_available': update_available,
            'latest_version': latest_version,
        })


# Global instance
_analytics_manager: Optional[AnalyticsManager] = None


def init_analytics(app_data_dir: Path, app_version: str) -> AnalyticsManager:
    """Initialize the analytics manager."""
    global _analytics_manager
    _analytics_manager = AnalyticsManager(app_data_dir, app_version)
    return _analytics_manager


def get_analytics() -> Optional[AnalyticsManager]:
    """Get the global analytics manager instance."""
    return _analytics_manager