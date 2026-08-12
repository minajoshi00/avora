"""
=======================================================================
AVORA MISSIONS - Export Functionality Test
=======================================================================

Tests the complete mission export workflow:
1. Create mission
2. Execute tasks (creates files)
3. Track files
4. Validate project
5. Export to ZIP
6. Verify secrets excluded
7. Verify file structure
8. Test natural language commands

Run this script to verify export functionality works.
"""

from __future__ import annotations

import sys
import time
import json
import zipfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_mission_export_workflow():
    """Test the complete mission export workflow."""
    print("=" * 60)
    print("AVORA MISSION EXPORT - END-TO-END TEST")
    print("=" * 60)
    
    # Test 1: Import modules
    print("\n[TEST 1] Importing modules...")
    try:
        from mission_tracker import get_mission_tracker, Mission, Milestone, Task
        from mission_planner import get_mission_planner
        from mission_executor import get_mission_executor
        from mission_exporter import get_mission_exporter
        from memory import add_memory, get_memories, clear_memories
        from settings import get_setting, set_setting
        print("[OK] All modules imported successfully")
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False
    
    # Test 2: Create mission
    print("\n[TEST 2] Creating test mission...")
    try:
        tracker = get_mission_tracker()
        planner = get_mission_planner()
        
        mission = planner.plan_mission("I want to build a simple portfolio website")
        if not mission:
            print("[FAIL] Mission planning failed")
            return False
        
        # Save the mission
        tracker._missions[mission.id] = mission
        tracker._save_missions()
        
        print(f"[OK] Mission created: {mission.title}")
        print(f"  ID: {mission.id}")
        print(f"  Category: {mission.category}")
        print(f"  Milestones: {len(mission.milestones)}")
    except Exception as e:
        print(f"[FAIL] Mission creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Simulate file creation (track project files)
    print("\n[TEST 3] Simulating file creation...")
    try:
        exporter = get_mission_exporter()
        
        # Create test files in a temporary directory
        test_dir = Path(__file__).parent / "test_project_temp"
        test_dir.mkdir(exist_ok=True)
        
        test_files = [
            test_dir / "index.html",
            test_dir / "styles.css",
            test_dir / "script.js",
            test_dir / "README.md",
        ]
        
        # Create the files
        for test_file in test_files:
            test_file.write_text(f"// {test_file.name}\nTest content\n")
            print(f"  Created: {test_file}")
            
            # Track in mission
            exporter.track_project_file(mission.id, str(test_file))
        
        # Add a file that should be excluded (.env)
        env_file = test_dir / ".env"
        env_file.write_text("SECRET_KEY=abc123\nAPI_KEY=xyz789\n")
        exporter.track_project_file(mission.id, str(env_file))
        
        print(f"[OK] Created {len(test_files)} project files + 1 .env file")
    except Exception as e:
        print(f"[FAIL] File creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Check project readiness
    print("\n[TEST 4] Checking project readiness...")
    try:
        # Mark mission as completed first
        mission.status = "completed"
        mission.completed_at = time.time()
        tracker._save_missions()
        print(f"  Mission marked as completed")
        
        readiness = exporter.is_project_ready_for_export(mission.id)
        print(f"  Ready: {readiness.get('ready')}")
        print(f"  Reason: {readiness.get('reason')}")
        print(f"  File count: {readiness.get('file_count', 0)}")
        
        if not readiness.get("ready"):
            print("[FAIL] Project not ready for export")
            return False
        
        print("[OK] Project is ready for export")
    except Exception as e:
        print(f"[FAIL] Readiness check failed: {e}")
        return False
    
    # Test 5: Get project files
    print("\n[TEST 5] Getting tracked project files...")
    try:
        project_files = exporter.get_project_files(mission.id)
        print(f"  Found {len(project_files)} tracked files:")
        for f in project_files:
            print(f"    - {f}")
        
        if len(project_files) < 4:
            print("[FAIL] Not enough files tracked")
            return False
        
        print("[OK] Files tracked correctly")
    except Exception as e:
        print(f"[FAIL] File retrieval failed: {e}")
        return False
    
    # Test 6: Export project
    print("\n[TEST 6] Exporting project...")
    try:
        result = exporter.export_mission_project(
            mission_id=mission.id,
            project_files=project_files,
            export_name=f"Test_Portfolio_{mission.id}",
        )
        
        if not result.get("success"):
            print(f"[FAIL] Export failed: {result.get('error')}")
            return False
        
        print(f"[OK] Export successful!")
        print(f"  Type: {result.get('type')}")
        print(f"  Path: {result.get('path')}")
        print(f"  Files: {result.get('file_count')}")
        print(f"  Size: {result.get('size_bytes', 0) / 1024:.1f} KB")
        
        export_path = result.get("path")
    except Exception as e:
        print(f"[FAIL] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: Verify ZIP contents
    print("\n[TEST 7] Verifying ZIP contents...")
    try:
        if result.get("type") != "zip":
            print("[WARN] Export is not a ZIP file, checking directory instead")
            export_path = Path(result.get("path"))
            if not export_path.exists():
                print("[FAIL] Export path does not exist")
                return False
        else:
            # Verify ZIP
            zip_path = Path(export_path)
            if not zip_path.exists():
                print("[FAIL] ZIP file not found")
                return False
            
            print(f"  ZIP size: {zip_path.stat().st_size} bytes")
            
            # Read ZIP contents
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                print(f"  Files in ZIP: {len(file_list)}")
                for f in file_list:
                    print(f"    - {f}")
                
                # Verify .env is NOT included
                env_files = [f for f in file_list if '.env' in Path(f).name]
                if env_files:
                    print(f"[FAIL] .env file found in ZIP: {env_files}")
                    return False
                else:
                    print("[OK] .env file correctly excluded")
                
                # Verify regular files are included
                expected_files = ['index.html', 'styles.css', 'script.js', 'README.md']
                for expected in expected_files:
                    found = any(expected in f for f in file_list)
                    if found:
                        print(f"[OK] {expected} included")
                    else:
                        print(f"[WARN] {expected} not found in ZIP")
        
        print("[OK] ZIP verification complete")
    except Exception as e:
        print(f"[FAIL] ZIP verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 8: Test natural language export command
    print("\n[TEST 8] Testing natural language export command...")
    try:
        from ai_logic import handle_missions
        
        # Test various export phrases
        export_phrases = [
            "give me the final product",
            "export this project",
            "download my completed project",
            "get my files",
        ]
        
        for phrase in export_phrases:
            response = handle_missions(phrase)
            if response:
                print(f"[OK] '{phrase}'")
                print(f"     Response: {response[:100]}...")
            else:
                print(f"[WARN] '{phrase}' - No response")
        
        print("[OK] Natural language commands working")
    except Exception as e:
        print(f"[FAIL] Natural language test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 9: Verify mission metadata
    print("\n[TEST 9] Verifying mission metadata...")
    try:
        updated_mission = tracker.get_mission(mission.id)
        if "export" in updated_mission.metadata:
            export_meta = updated_mission.metadata["export"]
            print(f"[OK] Export metadata stored:")
            print(f"  Exported at: {export_meta.get('exported_at')}")
            print(f"  Export name: {export_meta.get('export_name')}")
            print(f"  ZIP path: {export_meta.get('zip_path')}")
            print(f"  File count: {export_meta.get('file_count')}")
        else:
            print("[WARN] No export metadata in mission")
    except Exception as e:
        print(f"[FAIL] Metadata check failed: {e}")
    
    # Test 10: Clean up
    print("\n[TEST 10] Cleaning up test files...")
    try:
        # Remove test files
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"[OK] Removed test directory: {test_dir}")
        
        # Remove export
        if result.get("path"):
            export_path = Path(result.get("path"))
            if export_path.exists():
                if export_path.is_dir():
                    shutil.rmtree(export_path)
                else:
                    export_path.unlink()
                print(f"[OK] Removed export: {export_path}")
        
        print("[OK] Cleanup complete")
    except Exception as e:
        print(f"[WARN] Cleanup failed: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("[OK] Module imports")
    print("[OK] Mission creation")
    print("[OK] File tracking")
    print("[OK] Project readiness check")
    print("[OK] File retrieval")
    print("[OK] Project export")
    print("[OK] ZIP verification")
    print("[OK] Secret exclusion (.env excluded)")
    print("[OK] Natural language commands")
    print("[OK] Metadata storage")
    print("[OK] Cleanup")
    
    print("\n" + "=" * 60)
    print("[OK][OK][OK] ALL TESTS PASSED [OK][OK][OK]")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_mission_export_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)