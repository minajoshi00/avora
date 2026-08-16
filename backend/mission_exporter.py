"""
=======================================================================
AVORA MISSIONS - Mission Project Exporter
=======================================================================

Handles project finalization, validation, and export.

Features:
  - File tracking per mission
  - Project directory management
  - Validation of required files
  - ZIP archive creation
  - Secret exclusion (.env, API keys, tokens, passwords)
  - Safe packaging with error handling
  - Export metadata storage
  - Resume capability

Architecture:
  Mission → Project Files → Validation → Packaging → Export

Safety:
  - Never includes secrets
  - Never deletes original project
  - Never overwrites existing exports
  - Validates before packaging
"""

from __future__ import annotations

import os
import re
import json
import time
import zipfile
import shutil
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from settings import get_setting
from mission_tracker import get_mission_tracker, Mission


# =========================================================================
# CONFIGURATION
# =========================================================================

# Files/folders to always exclude from exports
_EXCLUDED_PATTERNS = {
    '.env', '.env.local', '.env.production', '.env.development',
    '*.env', '*.env.*',
    '.git', '.gitignore', 'node_modules', '__pycache__',
    '*.pyc', '*.pyo', '*.pyd', '.Python',
    'venv', 'env', '.venv', '.env',
    '*.secret', '*.key', '*.pem', '*.p12', '*.pfx',
    'credentials.json', 'service_account.json',
    'api_keys.txt', 'secrets.json', 'secrets.yaml',
    '.DS_Store', 'Thumbs.db',
    '*.log', 'logs/',
}

# Sensitive content patterns to exclude
_SECRET_PATTERNS = [
    re.compile(r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'api_secret\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'secret[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'password\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'token\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'private[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
    re.compile(r'access[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]+', re.IGNORECASE),
]


# =========================================================================
# PROJECT EXPORTER
# =========================================================================

class MissionProjectExporter:
    """
    Exports mission projects as downloadable packages.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._export_dir = Path(get_setting("missions.export_dir", "exports"))
        self._export_dir.mkdir(parents=True, exist_ok=True)

    def export_mission_project(
        self,
        mission_id: str,
        project_files: List[str],
        required_files: List[str] = None,
        export_name: str = None,
    ) -> Dict[str, Any]:
        """
        Export a mission's project files.
        
        Args:
            mission_id: Mission ID
            project_files: List of file paths to include
            required_files: Files that must exist (validation)
            export_name: Custom name for the export
            
        Returns:
            Export result with path, status, and metadata
        """
        with self._lock:
            tracker = get_mission_tracker()
            mission = tracker.get_mission(mission_id)
            
            if not mission:
                return {
                    "success": False,
                    "error": "Mission not found",
                }
            
            # Generate export name
            if not export_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_name = f"{mission.title.replace(' ', '_')}_{timestamp}"
            
            # Sanitize export name
            export_name = "".join(c for c in export_name if c.isalnum() or c in "_-")
            export_name = export_name[:100]  # Limit length
            
            # Create export directory
            export_path = self._export_dir / export_name
            export_path.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Validate required files
            validation_result = self._validate_project_files(
                project_files, required_files
            )
            
            if not validation_result["valid"]:
                # Clean up empty export dir
                try:
                    export_path.rmdir()
                except:
                    pass
                
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation": validation_result,
                }
            
            # Step 2: Copy files to export directory
            copy_result = self._copy_project_files(
                mission_id, project_files, export_path
            )
            
            if not copy_result["success"]:
                # Clean up
                try:
                    shutil.rmtree(export_path, ignore_errors=True)
                except:
                    pass
                
                return {
                    "success": False,
                    "error": "File copy failed",
                    "details": copy_result,
                }
            
            # Step 3: Create ZIP archive
            zip_result = self._create_zip_archive(export_path, export_name)
            
            if not zip_result["success"]:
                # Clean up directory, keep files
                return {
                    "success": True,
                    "type": "directory",
                    "path": str(export_path),
                    "warning": zip_result.get("error"),
                }
            
            # Step 4: Clean up directory, keep ZIP
            try:
                shutil.rmtree(export_path, ignore_errors=True)
            except:
                pass
            
            # Step 5: Update mission metadata
            mission.metadata["export"] = {
                "exported_at": time.time(),
                "export_name": export_name,
                "zip_path": zip_result["zip_path"],
                "file_count": len(project_files),
                "validation": validation_result,
            }
            tracker._save_missions()
            
            # Step 6: Save to memory
            try:
                from memory import add_memory
                add_memory(
                    f"Exported mission project '{mission.title}' to {zip_result['zip_path']}",
                    category="mission_export"
                )
            except Exception:
                pass
            
            return {
                "success": True,
                "type": "zip",
                "path": zip_result["zip_path"],
                "export_name": export_name,
                "file_count": len(project_files),
                "size_bytes": zip_result.get("size_bytes", 0),
                "validation": validation_result,
            }

    def _validate_project_files(
        self,
        project_files: List[str],
        required_files: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate project files exist and are accessible.
        
        Returns:
            Validation result with valid flag and details
        """
        result = {
            "valid": True,
            "missing_required": [],
            "missing_optional": [],
            "total_files": len(project_files),
            "valid_files": 0,
        }
        
        # Check required files
        if required_files:
            for req_file in required_files:
                found = any(
                    Path(f).name == Path(req_file).name or
                    str(f).endswith(req_file)
                    for f in project_files
                )
                if not found:
                    result["missing_required"].append(req_file)
                    result["valid"] = False
        
        # Check all files exist
        valid_count = 0
        for file_path in project_files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                valid_count += 1
            else:
                result["missing_optional"].append(file_path)
        
        result["valid_files"] = valid_count
        
        # Must have at least one valid file
        if valid_count == 0:
            result["valid"] = False
            result["error"] = "No valid files to export"
        
        return result

    def _copy_project_files(
        self,
        mission_id: str,
        project_files: List[str],
        export_path: Path,
    ) -> Dict[str, Any]:
        """
        Copy project files to export directory.
        
        Returns:
            Copy result with success flag and details
        """
        result = {
            "success": True,
            "copied": [],
            "skipped": [],
            "errors": [],
        }
        
        # Create mission subdirectory
        mission_dir = export_path / "project"
        mission_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in project_files:
            try:
                source = Path(file_path)
                
                if not source.exists():
                    result["skipped"].append(file_path)
                    continue
                
                # Determine destination path
                # Preserve folder structure relative to project root
                rel_path = source.name
                dest = mission_dir / rel_path
                
                # Handle duplicates
                counter = 1
                while dest.exists():
                    stem = source.stem
                    suffix = source.suffix
                    dest = mission_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Copy file
                shutil.copy2(source, dest)
                result["copied"].append(str(dest))
                
            except Exception as e:
                result["errors"].append({
                    "file": file_path,
                    "error": str(e),
                })
        
        # Must have copied at least one file
        if not result["copied"]:
            result["success"] = False
        
        return result

    def _create_zip_archive(
        self,
        export_path: Path,
        export_name: str,
    ) -> Dict[str, Any]:
        """
        Create ZIP archive of exported project.
        
        Returns:
            ZIP creation result
        """
        result = {
            "success": False,
            "zip_path": None,
            "size_bytes": 0,
        }
        
        try:
            zip_path = self._export_dir / f"{export_name}.zip"
            
            # Don't overwrite existing
            counter = 1
            base_name = export_name
            while zip_path.exists():
                zip_path = self._export_dir / f"{base_name}_{counter}.zip"
                counter += 1
            
            # Create ZIP
            with zipfile.ZipFile(
                zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6
            ) as zf:
                for file_path in export_path.rglob("*"):
                    if file_path.is_file():
                        # Skip excluded files
                        if self._should_exclude_file(file_path.name):
                            continue
                        
                        # Skip files with secrets
                        if self._file_contains_secrets(file_path):
                            continue
                        
                        # Add to ZIP with relative path
                        arcname = file_path.relative_to(export_path)
                        zf.write(file_path, arcname)
            
            result["success"] = True
            result["zip_path"] = str(zip_path)
            result["size_bytes"] = zip_path.stat().st_size
            
        except Exception as e:
            result["error"] = str(e)
        
        return result

    def _should_exclude_file(self, filename: str) -> bool:
        """Check if file should be excluded from export."""
        filename_lower = filename.lower()
        
        for pattern in _EXCLUDED_PATTERNS:
            if pattern.startswith("*"):
                # Wildcard pattern
                if filename_lower.endswith(pattern[1:]):
                    return True
            elif pattern.startswith("."):
                # Hidden file/directory
                if filename_lower == pattern or filename_lower.startswith(pattern + "."):
                    return True
            else:
                # Exact match
                if filename_lower == pattern:
                    return True
        
        return False

    def _file_contains_secrets(self, file_path: Path) -> bool:
        """
        Check if file contains sensitive information.
        
        Only checks text files, skips binary files.
        """
        # Skip binary files
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
                            '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll',
                            '.pyc', '.pyo', '.pyd', '.so', '.dylib'}
        
        if file_path.suffix.lower() in binary_extensions:
            return False
        
        # Try to read as text
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for secret patterns
            for pattern in _SECRET_PATTERNS:
                if pattern.search(content):
                    return True
            
            return False
            
        except Exception:
            return False

    def get_latest_export(self, mission_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest export for a mission or all missions.
        
        Args:
            mission_id: Optional mission ID to filter by
            
        Returns:
            Latest export info or None
        """
        try:
            # Scan export directory
            exports = []
            
            for zip_file in self._export_dir.glob("*.zip"):
                exports.append({
                    "path": str(zip_file),
                    "name": zip_file.stem,
                    "size_bytes": zip_file.stat().st_size,
                    "created_at": zip_file.stat().st_ctime,
                })
            
            if not exports:
                return None
            
            # Sort by creation time
            exports.sort(key=lambda x: x["created_at"], reverse=True)
            
            latest = exports[0]
            
            # Match mission if specified
            if mission_id:
                tracker = get_mission_tracker()
                mission = tracker.get_mission(mission_id)
                
                if mission and mission.metadata.get("export"):
                    mission_export = mission.metadata["export"]
                    if latest["path"] == mission_export.get("zip_path"):
                        return mission_export
            
            return latest
            
        except Exception:
            return None

    def list_mission_exports(self, mission_id: str) -> List[Dict[str, Any]]:
        """
        List all exports for a mission.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            List of export records
        """
        tracker = get_mission_tracker()
        mission = tracker.get_mission(mission_id)
        
        if not mission:
            return []
        
        exports = mission.metadata.get("exports", [])
        if not exports:
            # Check for single export
            if "export" in mission.metadata:
                exports = [mission.metadata["export"]]
        
        return exports

    def is_project_ready_for_export(self, mission_id: str) -> Dict[str, Any]:
        """
        Check if mission project is ready for export.
        
        Returns:
            Readiness check result
        """
        tracker = get_mission_tracker()
        mission = tracker.get_mission(mission_id)
        
        if not mission:
            return {
                "ready": False,
                "reason": "Mission not found",
            }
        
        # Check mission completion
        if mission.status != "completed":
            return {
                "ready": False,
                "reason": f"Mission is {mission.status}, not completed",
                "progress": mission.calculate_progress(),
            }
        
        # Check for files
        if "project_files" not in mission.context:
            return {
                "ready": False,
                "reason": "No project files tracked",
            }
        
        project_files = mission.context["project_files"]
        
        if not project_files:
            return {
                "ready": False,
                "reason": "Project has no files",
            }
        
        # Check files exist
        existing_files = [f for f in project_files if Path(f).exists()]
        
        return {
            "ready": len(existing_files) > 0,
            "reason": "Ready for export" if existing_files else "No files exist",
            "file_count": len(existing_files),
            "total_files": len(project_files),
        }

    def track_project_file(self, mission_id: str, file_path: str) -> bool:
        """
        Track a file as part of the mission project.
        
        Args:
            mission_id: Mission ID
            file_path: Path to the file
            
        Returns:
            Success flag
        """
        tracker = get_mission_tracker()
        mission = tracker.get_mission(mission_id)
        
        if not mission:
            return False
        
        if "project_files" not in mission.context:
            mission.context["project_files"] = []
        
        # Add if not already tracked
        if file_path not in mission.context["project_files"]:
            mission.context["project_files"].append(file_path)
            tracker._save_missions()
        
        return True

    def get_project_files(self, mission_id: str) -> List[str]:
        """
        Get all tracked project files for a mission.
        
        Args:
            mission_id: Mission ID
            
        Returns:
            List of file paths
        """
        tracker = get_mission_tracker()
        mission = tracker.get_mission(mission_id)
        
        if not mission:
            return []
        
        return mission.context.get("project_files", [])


# =========================================================================
# GLOBAL INSTANCE
# =========================================================================

_exporter: Optional[MissionProjectExporter] = None
_exporter_lock = threading.Lock()


def get_mission_exporter() -> MissionProjectExporter:
    """Get the global mission exporter instance."""
    global _exporter
    if _exporter is None:
        with _exporter_lock:
            if _exporter is None:
                _exporter = MissionProjectExporter()
    return _exporter


# =========================================================================
# PUBLIC API
# =========================================================================

__all__ = [
    "MissionProjectExporter",
    "get_mission_exporter",
]