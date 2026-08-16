"""
AVORA Changelog System

Manages what's new information and changelog entries.
Stores changelog data in a structured format.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class ChangelogEntry:
    """Represents a single changelog entry."""
    
    def __init__(
        self,
        version: str,
        title: str,
        description: str,
        release_date: str,
        features: List[str],
        improvements: List[str],
        bug_fixes: List[str],
        breaking_changes: List[str] = None,
    ):
        self.version = version
        self.title = title
        self.description = description
        self.release_date = release_date
        self.features = features or []
        self.improvements = improvements or []
        self.bug_fixes = bug_fixes or []
        self.breaking_changes = breaking_changes or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'version': self.version,
            'title': self.title,
            'description': self.description,
            'release_date': self.release_date,
            'features': self.features,
            'improvements': self.improvements,
            'bug_fixes': self.bug_fixes,
            'breaking_changes': self.breaking_changes,
            'timestamp': self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> ChangelogEntry:
        """Create from dictionary."""
        return cls(
            version=data['version'],
            title=data['title'],
            description=data['description'],
            release_date=data['release_date'],
            features=data.get('features', []),
            improvements=data.get('improvements', []),
            bug_fixes=data.get('bug_fixes', []),
            breaking_changes=data.get('breaking_changes', []),
        )


class ChangelogManager:
    """Manages changelog data and history."""
    
    def __init__(self, app_data_dir: Path):
        self.app_data_dir = app_data_dir
        self.changelog_file = app_data_dir / "changelog.json"
        self.entries: List[ChangelogEntry] = []
        self.seen_versions: List[str] = []
        
        # Load existing changelog
        self._load_changelog()
    
    def _load_changelog(self):
        """Load changelog from file."""
        try:
            if self.changelog_file.exists():
                with open(self.changelog_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = [
                        ChangelogEntry.from_dict(entry) 
                        for entry in data.get('entries', [])
                    ]
                    self.seen_versions = data.get('seen_versions', [])
        except Exception as e:
            print(f"[CHANGELOG] Failed to load: {e}")
            self.entries = []
            self.seen_versions = []
    
    def _save_changelog(self):
        """Save changelog to file."""
        try:
            self.app_data_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'entries': [entry.to_dict() for entry in self.entries],
                'seen_versions': self.seen_versions,
            }
            
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CHANGELOG] Failed to save: {e}")
    
    def add_entry(self, entry: ChangelogEntry) -> bool:
        """
        Add a new changelog entry.
        Returns True if added, False if already exists.
        """
        # Check if version already exists
        if entry.version in [e.version for e in self.entries]:
            return False
        
        # Add to beginning (newest first)
        self.entries.insert(0, entry)
        
        # Mark as seen
        if entry.version not in self.seen_versions:
            self.seen_versions.append(entry.version)
        
        self._save_changelog()
        return True
    
    def get_latest_version(self) -> Optional[str]:
        """Get the latest version number."""
        if self.entries:
            return self.entries[0].version
        return None
    
    def get_entries(self, limit: int = 10) -> List[ChangelogEntry]:
        """Get recent changelog entries."""
        return self.entries[:limit]
    
    def get_entry(self, version: str) -> Optional[ChangelogEntry]:
        """Get a specific version's changelog entry."""
        for entry in self.entries:
            if entry.version == version:
                return entry
        return None
    
    def mark_version_seen(self, version: str):
        """Mark a version as seen by the user."""
        if version not in self.seen_versions:
            self.seen_versions.append(version)
            self._save_changelog()
    
    def has_unseen_changes(self, current_version: str) -> bool:
        """
        Check if there are unseen changes since the user's last version.
        Returns True if user hasn't seen the current version's changelog.
        """
        # If no entries, no changelog to show
        if not self.entries:
            return False
        
        latest = self.get_latest_version()
        
        # If user is on latest version and has seen it
        if current_version == latest and current_version in self.seen_versions:
            return False
        
        # If there's a newer version than current
        if latest and latest != current_version:
            return True
        
        # If user hasn't seen current version's changelog
        if current_version not in self.seen_versions:
            return True
        
        return False
    
    def get_changelog_text(self, version: str) -> str:
        """Get formatted changelog text for a specific version."""
        entry = self.get_entry(version)
        if not entry:
            return ""
        
        lines = [
            f"# {entry.title}",
            f"Version {entry.version} - {entry.release_date}",
            "",
            entry.description,
            "",
        ]
        
        if entry.features:
            lines.extend([
                "## New Features",
                "",
            ])
            lines.extend([f"- {feature}" for feature in entry.features])
            lines.append("")
        
        if entry.improvements:
            lines.extend([
                "## Improvements",
                "",
            ])
            lines.extend([f"- {improvement}" for improvement in entry.improvements])
            lines.append("")
        
        if entry.bug_fixes:
            lines.extend([
                "## Bug Fixes",
                "",
            ])
            lines.extend([f"- {fix}" for fix in entry.bug_fixes])
            lines.append("")
        
        if entry.breaking_changes:
            lines.extend([
                "## Breaking Changes",
                "",
            ])
            lines.extend([f"- {change}" for change in entry.breaking_changes])
            lines.append("")
        
        return "\n".join(lines)
    
    def create_default_changelog(self, current_version: str):
        """Create a default changelog entry for the current version if none exists."""
        if self.get_entry(current_version):
            return
        
        # Create a basic entry from version info
        entry = ChangelogEntry(
            version=current_version,
            title="AVORA Desktop",
            description="Welcome to AVORA! Experience a new kind of personal intelligence.",
            release_date=datetime.now().strftime("%Y-%m-%d"),
            features=[
                "Natural conversational AI with context memory",
                "Real-time adaptive intelligence engine",
                "Voice input and natural language understanding",
            ],
            improvements=[
                "Optimized response time and performance",
                "Enhanced user interface",
            ],
            bug_fixes=[
                "Initial stable release",
            ],
        )
        
        self.add_entry(entry)


# Global instance (initialized in main.py)
_changelog_manager: Optional[ChangelogManager] = None


def init_changelog(app_data_dir: Path) -> ChangelogManager:
    """Initialize the global changelog manager."""
    global _changelog_manager
    _changelog_manager = ChangelogManager(app_data_dir)
    return _changelog_manager


def get_changelog_manager() -> Optional[ChangelogManager]:
    """Get the global changelog manager instance."""
    return _changelog_manager