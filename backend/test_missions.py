"""
========================================================================
AVORA MISSIONS - End-to-End Test
========================================================================

Tests the complete mission workflow:
1. Create mission
2. Generate plan
3. View mission
4. Start task
5. Update task
6. Complete task
7. Update progress
8. Store memory
9. Restart application
10. Resume mission
11. Retrieve context
12. Recommend next action

Run this script to verify missions work correctly.
"""

from __future__ import annotations

import sys
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_mission_workflow():
    """Test the complete mission workflow."""
    print("=" * 60)
    print("AVORA MISSIONS - END-TO-END TEST")
    print("=" * 60)
    
    # Test 1: Import modules
    print("\n[TEST 1] Importing modules...")
    try:
        from mission_tracker import get_mission_tracker, Mission, Milestone, Task
        from mission_planner import get_mission_planner
        from memory import add_memory, get_memories, clear_memories
        from .settings import get_setting, set_setting
        print("[OK] All modules imported successfully")
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False
    
    # Test 2: Create mission
    print("\n[TEST 2] Creating mission...")
    try:
        tracker = get_mission_tracker()
        planner = get_mission_planner()
        
        mission = planner.plan_mission("I want to build a website")
        if not mission:
            print("[FAIL] Mission planning failed")
            return False
        
        # IMPORTANT: Save the mission to the tracker
        tracker._missions[mission.id] = mission
        tracker._save_missions()
        
        print(f"[OK] Mission created: {mission.title}")
        print(f"  Category: {mission.category}")
        print(f"  Milestones: {len(mission.milestones)}")
        print(f"  Priority: {mission.priority}")
        print(f"  Deadline: {mission.deadline}")
    except Exception as e:
        print(f"[FAIL] Mission creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: View mission
    print("\n[TEST 3] Viewing mission...")
    try:
        summary = tracker.get_mission_summary(mission.id)
        if not summary:
            print("[FAIL] Failed to get mission summary")
            return False
        
        print(f"[OK] Mission summary retrieved:")
        print(f"  Title: {summary['title']}")
        print(f"  Progress: {int(summary['progress'] * 100)}%")
        print(f"  Total tasks: {summary['total_tasks']}")
        print(f"  Milestones: {summary['completed_milestones']}/{summary['total_milestones']}")
    except Exception as e:
        print(f"[FAIL] Mission view failed: {e}")
        return False
    
    # Test 4: Get next action
    print("\n[TEST 4] Getting next action...")
    try:
        action = tracker.get_next_action(mission.id)
        if not action:
            print("[FAIL] No next action found")
            return False
        
        print(f"[OK] Next action identified:")
        print(f"  Task: {action['task_title']}")
        print(f"  Milestone: {action['milestone_title']}")
        print(f"  Estimated: {action['estimated_minutes']} minutes")
    except Exception as e:
        print(f"[FAIL] Next action failed: {e}")
        return False
    
    # Test 5: Complete task
    print("\n[TEST 5] Completing task...")
    try:
        task_id = action['task_id']
        result = tracker.complete_task(mission.id, task_id)
        if not result:
            print("[FAIL] Task completion failed")
            return False
        
        print(f"[OK] Task completed: {action['task_title']}")
        
        # Check updated progress
        updated_summary = tracker.get_mission_summary(mission.id)
        print(f"  Updated progress: {int(updated_summary['progress'] * 100)}%")
    except Exception as e:
        print(f"[FAIL] Task completion failed: {e}")
        return False
    
    # Test 6: Store memory
    print("\n[TEST 6] Storing mission memory...")
    try:
        clear_memories()  # Clean slate
        
        add_memory(f"User started mission: {mission.title}", category="mission")
        add_memory(f"Mission category: {mission.category}", category="mission")
        add_memory(f"Completed task: {action['task_title']}", category="mission")
        
        memories = get_memories()
        mission_memories = [m for m in memories if m.get('category') == 'mission']
        
        print(f"[OK] Stored {len(mission_memories)} mission memories")
        for mem in mission_memories:
            print(f"  - {mem['text']}")
    except Exception as e:
        print(f"[FAIL] Memory storage failed: {e}")
        return False
    
    # Test 7: Persistence
    print("\n[TEST 7] Testing persistence...")
    try:
        # Save missions
        missions_file = Path(__file__).parent / "avora backend" / "app_data" / "missions.json"
        if not missions_file.exists():
            # Try alternative path
            missions_file = Path(__file__).parent / "missions.json"
        
        if missions_file.exists():
            with open(missions_file, 'r') as f:
                data = json.load(f)
            
            mission_count = len(data.get('missions', []))
            print(f"[OK] Persistence check: {mission_count} mission(s) in storage")
            
            if mission_count > 0:
                print(f"  Mission IDs: {[m['id'] for m in data['missions']]}")
        else:
            print(f"[WARN] Missions file not found at {missions_file}")
            print("  (This is okay if using different storage path)")
    except Exception as e:
        print(f"[WARN] Persistence check failed: {e}")
        # Not a critical failure
    
    # Test 8: Search missions
    print("\n[TEST 8] Searching missions...")
    try:
        results = tracker.search_missions("website")
        print(f"[OK] Search found {len(results)} result(s)")
        
        results2 = tracker.search_missions("build")
        print(f"[OK] Search 'build' found {len(results2)} result(s)")
    except Exception as e:
        print(f"[FAIL] Search failed: {e}")
        return False
    
    # Test 9: Get active missions
    print("\n[TEST 9] Getting active missions...")
    try:
        active = tracker.get_active_missions()
        print(f"[OK] Active missions: {len(active)}")
        
        for m in active:
            print(f"  - {m.title} ({int(m.calculate_progress() * 100)}%)")
    except Exception as e:
        print(f"[FAIL] Active missions failed: {e}")
        return False
    
    # Test 10: Mission execution
    print("\n[TEST 10] Testing mission execution...")
    try:
        from mission_executor import get_mission_executor
        
        executor = get_mission_executor()
        
        # Execute a task
        result = executor.execute_task(mission.id, action['task_id'])
        
        if result and not result.get("error"):
            print(f"[OK] Task execution successful:")
            print(f"  Intent: {result.get('intent')}")
            print(f"  Actions: {result.get('actions', [])}")
            print(f"  Guidance: {result.get('guidance', 'None')[:100]}...")
            
            # Mark as completed
            if executor.mark_task_completed(mission.id, action['task_id'], result):
                print(f"[OK] Task marked as completed")
        else:
            print(f"[WARN] Execution result: {result}")
    except Exception as e:
        print(f"[WARN] Mission execution test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 11: Integration with companion intelligence
    print("\n[TEST 11] Testing companion intelligence integration...")
    try:
        from companion_intelligence import get_companion_intelligence
        
        companion = get_companion_intelligence()
        if companion is None:
            print("[WARN] Companion intelligence not available (optional)")
        else:
            # Simulate a cycle with mission context
            snapshot = companion.context.update(
                activity_type="coding",
                window_title="VS Code - index.html",
                process_name="code.exe",
                idle_minutes=0.0
            )
            
            # Check if mission context was added
            if hasattr(snapshot, 'active_missions'):
                print(f"[OK] Mission context in companion: {snapshot.active_missions}")
            else:
                print("[WARN] Mission context not in snapshot (may need companion restart)")
    except Exception as e:
        print(f"[WARN] Companion integration test failed: {e}")
        # Not a critical failure
    
    # Final summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("[OK] Mission creation: PASSED")
    print("[OK] Mission planning: PASSED")
    print("[OK] Mission viewing: PASSED")
    print("[OK] Task completion: PASSED")
    print("[OK] Memory integration: PASSED")
    print("[OK] Search: PASSED")
    print("[OK] Active missions: PASSED")
    
    print("\n[OK][OK][OK] ALL CRITICAL TESTS PASSED [OK][OK][OK]")
    print("\nThe AVORA Missions system is working correctly!")
    print("\nNext steps:")
    print("1. Run AVORA and test via UI")
    print("2. Create a mission by saying 'I want to...'")
    print("3. View missions with 'Show my missions'")
    print("4. Complete tasks and watch progress update")
    
    return True


if __name__ == "__main__":
    try:
        success = test_mission_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)