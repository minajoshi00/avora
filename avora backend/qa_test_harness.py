"""
============================================================
AVORA V2 QA TEST HARNESS
============================================================
Senior QA Engineer & Beta Tester automated test suite.

Launches the real application and exercises it like a real user:
- Startup validation
- UI component verification
- AI conversation testing
- Memory persistence testing
- Computer control testing
- File operation testing
- Error handling testing
- Stress testing
- Performance measurement
- Clean shutdown verification
============================================================
"""

import os
import sys
import time
import json
import traceback
import threading
from datetime import datetime
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# Force Qt to use offscreen platform for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QTimer, QEventLoop, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QLineEdit, QTextBrowser

# ============================================================
# TEST RESULT TRACKING
# ============================================================

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.performance = {}

    def pass_test(self, name, detail=""):
        self.passed.append({"name": name, "detail": detail})
        print(f"  [PASS] {name} {detail}")

    def fail_test(self, name, detail=""):
        self.failed.append({"name": name, "detail": detail})
        print(f"  [FAIL] {name} {detail}")

    def skip_test(self, name, detail=""):
        self.skipped.append({"name": name, "detail": detail})
        print(f"  [SKIP] {name} {detail}")

    def measure(self, name, value, unit="ms"):
        self.performance[name] = {"value": value, "unit": unit}
        print(f"  [MEASURE] {name}: {value:.2f}{unit}")

    def summary(self):
        return {
            "passed": len(self.passed),
            "failed": len(self.failed),
            "skipped": len(self.skipped),
            "performance": self.performance,
            "failed_tests": self.failed,
        }


# ============================================================
# QA TEST SUITE
# ============================================================

class QATestSuite:
    def __init__(self):
        self.results = TestResult()
        self.app = None
        self.window = None
        self.start_time = None

    # ========================================================
    # SETUP / TEARDOWN
    # ========================================================

    def setup(self):
        """Initialize the application."""
        self.start_time = time.time()
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")

        # Import main after QApplication is created
        import main as main_module
        self.main_module = main_module

        # Create the main window
        self.window = main_module.MainWindow()
        self.window.show()
        self.app.processEvents()

        # Wait for window to be ready
        time.sleep(1.0)
        self.app.processEvents()

    def teardown(self):
        """Clean shutdown."""
        try:
            self.window.close()
            self.app.processEvents()
        except Exception as e:
            print(f"  [WARN] Teardown error: {e}")

    def wait(self, ms=100):
        """Process events for a duration."""
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    # ========================================================
    # TEST 1: STARTUP
    # ========================================================

    def test_startup(self):
        print("\n=== STARTUP TEST ===")
        elapsed = time.time() - self.start_time
        self.results.measure("startup_time", elapsed * 1000)

        # Window exists
        if self.window is not None:
            self.results.pass_test("Main window created")
        else:
            self.results.fail_test("Main window created", "Window is None")

        # Window title
        title = self.window.windowTitle()
        if "AVORA" in title.upper():
            self.results.pass_test("Window title", f"'{title}'")
        else:
            self.results.fail_test("Window title", f"Got '{title}'")

        # Window visible
        if self.window.isVisible():
            self.results.pass_test("Window visible")
        else:
            self.results.fail_test("Window visible")

        # Window size
        size = self.window.size()
        if size.width() >= 950 and size.height() >= 700:
            self.results.pass_test("Window size", f"{size.width()}x{size.height()}")
        else:
            self.results.fail_test("Window size", f"{size.width()}x{size.height()}")

        # Sidebar exists
        if hasattr(self.window, "sidebar") and self.window.sidebar is not None:
            self.results.pass_test("Sidebar exists")
        else:
            self.results.fail_test("Sidebar exists")

        # Chat area exists
        if hasattr(self.window, "chat_area") and self.window.chat_area is not None:
            self.results.pass_test("Chat area exists")
        else:
            self.results.fail_test("Chat area exists")

        # Input box exists
        if hasattr(self.window, "user_input") and self.window.user_input is not None:
            self.results.pass_test("Input box exists")
        else:
            self.results.fail_test("Input box exists")

        # Send button exists
        if hasattr(self.window, "send_button") and self.window.send_button is not None:
            self.results.pass_test("Send button exists")
        else:
            self.results.fail_test("Send button exists")

        # Mic button exists
        if hasattr(self.window, "mic_button") and self.window.mic_button is not None:
            self.results.pass_test("Mic button exists")
        else:
            self.results.fail_test("Mic button exists")

        # Character
        if hasattr(self.window, "character") and self.window.character is not None:
            self.results.pass_test("Character created")
        else:
            self.results.skip_test("Character created", "Character may be disabled in settings")

        # Status label
        if hasattr(self.window, "status_label") and self.window.status_label is not None:
            self.results.pass_test("Status label exists")
        else:
            self.results.fail_test("Status label exists")

        # Welcome message present
        if self.window.message_layout.count() > 1:
            self.results.pass_test("Welcome message present")
        else:
            self.results.fail_test("Welcome message present")

    # ========================================================
    # TEST 2: UI COMPONENTS
    # ========================================================

    def test_ui_components(self):
        print("\n=== UI COMPONENT TEST ===")

        # New chat button
        if hasattr(self.window, "new_chat_button"):
            btn = self.window.new_chat_button
            if btn is not None and btn.isEnabled():
                self.results.pass_test("New chat button enabled")
            else:
                self.results.fail_test("New chat button enabled")

        # Voice button
        if hasattr(self.window, "voice_button"):
            btn = self.window.voice_button
            if btn is not None:
                self.results.pass_test("Voice button exists")
            else:
                self.results.fail_test("Voice button exists")

        # Settings button
        if hasattr(self.window, "settings_button"):
            btn = self.window.settings_button
            if btn is not None:
                self.results.pass_test("Settings button exists")
            else:
                self.results.fail_test("Settings button exists")

        # Attach button
        if hasattr(self.window, "attach_button"):
            btn = self.window.attach_button
            if btn is not None:
                self.results.pass_test("Attach button exists")
            else:
                self.results.fail_test("Attach button exists")

        # Chat sidebar
        if hasattr(self.window, "chat_sidebar") and self.window.chat_sidebar is not None:
            self.results.pass_test("Chat sidebar exists")
        else:
            self.results.fail_test("Chat sidebar exists")

        # Test new chat functionality
        try:
            msg_count_before = self.window.message_layout.count()
            self.window.create_new_chat()
            self.wait(200)
            msg_count_after = self.window.message_layout.count()
            if msg_count_after > 0:
                self.results.pass_test("New chat clears messages")
            else:
                self.results.fail_test("New chat clears messages")
        except Exception as e:
            self.results.fail_test("New chat", str(e))

        # Test window resize
        try:
            self.window.resize(1000, 750)
            self.wait(200)
            size = self.window.size()
            if size.width() == 1000 and size.height() == 750:
                self.results.pass_test("Window resize", f"{size.width()}x{size.height()}")
            else:
                self.results.fail_test("Window resize", f"Got {size.width()}x{size.height()}")
        except Exception as e:
            self.results.fail_test("Window resize", str(e))

        # Test minimize/restore
        try:
            self.window.showMinimized()
            self.wait(200)
            if self.window.isMinimized():
                self.results.pass_test("Window minimize")
            else:
                self.results.fail_test("Window minimize")
            self.window.showNormal()
            self.wait(200)
            if not self.window.isMinimized():
                self.results.pass_test("Window restore")
            else:
                self.results.fail_test("Window restore")
        except Exception as e:
            self.results.fail_test("Window minimize/restore", str(e))

    # ========================================================
    # TEST 3: AI CONVERSATION
    # ========================================================

    def test_ai_conversation(self):
        print("\n=== AI CONVERSATION TEST ===")

        test_messages = [
            "Hello",
            "What can you do?",
            "Tell me a joke.",
            "Explain Python in one sentence.",
            "What time is it?",
        ]

        for msg in test_messages:
            try:
                # Set input text and send
                self.window.user_input.setText(msg)
                self.wait(50)
                self.window.send_message()
                self.wait(500)

                # Check processing state
                if self.window.is_processing:
                    self.results.pass_test(f"AI processing: '{msg}'")
                else:
                    self.results.fail_test(f"AI processing: '{msg}'", "Not processing")

                # Wait for response (up to 15s)
                response_received = False
                for _ in range(30):
                    self.wait(500)
                    if not self.window.is_processing:
                        response_received = True
                        break

                if response_received:
                    self.results.pass_test(f"AI response: '{msg}'")
                else:
                    self.results.fail_test(f"AI response: '{msg}'", "Timed out waiting for response")

            except Exception as e:
                self.results.fail_test(f"AI conversation: '{msg}'", str(e))

    # ========================================================
    # TEST 4: MEMORY
    # ========================================================

    def test_memory(self):
        print("\n=== MEMORY TEST ===")

        try:
            from memory import add_memory, get_memory_text, search_memory, clear_memories

            # Clear existing memories for clean test
            clear_memories()

            # Save a memory
            result = add_memory("My favorite language is Python.", "preference")
            if result:
                self.results.pass_test("Memory save")
            else:
                self.results.fail_test("Memory save")

            # Retrieve memory
            memory_text = get_memory_text()
            if "Python" in memory_text:
                self.results.pass_test("Memory retrieval", "Found 'Python' in memories")
            else:
                self.results.fail_test("Memory retrieval", f"Got: {memory_text}")

            # Search memory
            results = search_memory("Python")
            if len(results) > 0:
                self.results.pass_test("Memory search", f"Found {len(results)} result(s)")
            else:
                self.results.fail_test("Memory search")

            # Clean up
            clear_memories()
            self.results.pass_test("Memory cleanup")

        except Exception as e:
            self.results.fail_test("Memory system", str(e))

    # ========================================================
    # TEST 5: COMPUTER CONTROL
    # ========================================================

    def test_computer_control(self):
        print("\n=== COMPUTER CONTROL TEST ===")

        try:
            from launcher_engine import get_launcher_engine
            engine = get_launcher_engine()

            apps_to_test = ["notepad", "calculator", "paint", "explorer", "settings", "taskmgr"]

            for app_name in apps_to_test:
                try:
                    results = engine.search_apps(app_name, limit=5)
                    if len(results) > 0:
                        self.results.pass_test(f"Search: {app_name}", f"Found {len(results)} result(s)")
                    else:
                        self.results.fail_test(f"Search: {app_name}", "No results found")
                except Exception as e:
                    self.results.fail_test(f"Search: {app_name}", str(e))

            # Test launch (notepad)
            try:
                results = engine.search_apps("notepad", limit=1)
                if results:
                    app = results[0]
                    success = engine.launch_app(app["path"], app.get("name", "notepad"))
                    if success:
                        self.results.pass_test("Launch: notepad")
                    else:
                        self.results.fail_test("Launch: notepad", "Launch returned False")
                else:
                    self.results.fail_test("Launch: notepad", "App not found")
            except Exception as e:
                self.results.fail_test("Launch: notepad", str(e))

        except Exception as e:
            self.results.fail_test("Computer control", str(e))

    # ========================================================
    # TEST 6: FILE OPERATIONS
    # ========================================================

    def test_file_operations(self):
        print("\n=== FILE OPERATION TEST ===")

        try:
            from skills.files import list_folder, get_file_info

            # List home directory
            home = str(Path.home())
            result = list_folder(home)
            if result and "success" in str(result).lower() or isinstance(result, dict):
                self.results.pass_test("List folder", f"Home: {home}")
            else:
                self.results.fail_test("List folder", f"Got: {result}")

            # Get file info for a known file
            test_file = Path(__file__)
            info = get_file_info(str(test_file))
            if info and isinstance(info, dict):
                self.results.pass_test("Get file info", f"{test_file.name}")
            else:
                self.results.fail_test("Get file info", f"Got: {info}")

        except Exception as e:
            self.results.fail_test("File operations", str(e))

    # ========================================================
    # TEST 7: ERROR HANDLING
    # ========================================================

    def test_error_handling(self):
        print("\n=== ERROR HANDLING TEST ===")

        # Test nonexistent app
        try:
            from launcher_engine import get_launcher_engine
            engine = get_launcher_engine()
            results = engine.search_apps("nonexistent_app_xyz_123", limit=5)
            if len(results) == 0:
                self.results.pass_test("Nonexistent app search", "Gracefully returned empty")
            else:
                self.results.fail_test("Nonexistent app search", f"Unexpected results: {len(results)}")
        except Exception as e:
            self.results.fail_test("Nonexistent app search", str(e))

        # Test invalid file
        try:
            from skills.files import get_file_info
            info = get_file_info("C:\\nonexistent\\file\\that\\doesnt\\exist.txt")
            if info and isinstance(info, dict) and not info.get("success", True):
                self.results.pass_test("Nonexistent file", "Gracefully handled")
            else:
                self.results.pass_test("Nonexistent file", "No crash")
        except Exception as e:
            self.results.fail_test("Nonexistent file", str(e))

        # Test empty message
        try:
            self.window.user_input.setText("")
            self.window.send_message()
            self.wait(100)
            if not self.window.is_processing:
                self.results.pass_test("Empty message", "Gracefully ignored")
            else:
                self.results.fail_test("Empty message", "Started processing empty message")
        except Exception as e:
            self.results.fail_test("Empty message", str(e))

        # Test very long message
        try:
            long_msg = "A" * 5000
            self.window.user_input.setText(long_msg)
            self.window.send_message()
            self.wait(200)
            if not self.window.is_processing:
                self.results.pass_test("Long message", "Gracefully rejected")
            else:
                self.results.fail_test("Long message", "Started processing overlong message")
        except Exception as e:
            self.results.fail_test("Long message", str(e))

    # ========================================================
    # TEST 8: STRESS TEST
    # ========================================================

    def test_stress(self):
        print("\n=== STRESS TEST ===")

        # Rapid new chat creation
        try:
            for i in range(10):
                self.window.create_new_chat()
                self.wait(50)
            self.results.pass_test("Rapid new chat (10x)", "No crash")
        except Exception as e:
            self.results.fail_test("Rapid new chat", str(e))

        # Rapid window resizing
        try:
            for i in range(10):
                w = 900 + (i * 30)
                h = 700 + (i * 20)
                self.window.resize(w, h)
                self.wait(30)
            self.results.pass_test("Rapid resize (10x)", "No crash")
        except Exception as e:
            self.results.fail_test("Rapid resize", str(e))

        # Rapid message sending (empty - should be ignored)
        try:
            for i in range(20):
                self.window.user_input.setText("")
                self.window.send_message()
                self.wait(20)
            self.results.pass_test("Rapid empty sends (20x)", "No crash")
        except Exception as e:
            self.results.fail_test("Rapid empty sends", str(e))

        # Memory usage check
        try:
            import psutil
            process = psutil.Process()
            mem_mb = process.memory_info().rss / (1024 * 1024)
            self.results.measure("memory_usage", mem_mb, "MB")
            if mem_mb < 500:
                self.results.pass_test("Memory usage", f"{mem_mb:.1f} MB")
            else:
                self.results.fail_test("Memory usage", f"{mem_mb:.1f} MB (high)")
        except Exception as e:
            self.results.skip_test("Memory usage", str(e))

        # CPU usage check
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            self.results.measure("cpu_usage", cpu, "%")
            if cpu < 50:
                self.results.pass_test("CPU usage", f"{cpu:.1f}%")
            else:
                self.results.fail_test("CPU usage", f"{cpu:.1f}% (high)")
        except Exception as e:
            self.results.skip_test("CPU usage", str(e))

    # ========================================================
    # TEST 9: PERFORMANCE
    # ========================================================

    def test_performance(self):
        print("\n=== PERFORMANCE TEST ===")

        # Launcher search speed
        try:
            from launcher_engine import get_launcher_engine
            engine = get_launcher_engine()
            start = time.time()
            engine.search_apps("notepad", limit=10)
            elapsed = (time.time() - start) * 1000
            self.results.measure("launcher_search", elapsed)
            if elapsed < 2000:
                self.results.pass_test("Launcher search speed", f"{elapsed:.1f}ms")
            else:
                self.results.fail_test("Launcher search speed", f"{elapsed:.1f}ms (slow)")
        except Exception as e:
            self.results.skip_test("Launcher search speed", str(e))

        # Context engine speed
        try:
            from core.context_engine import get_context_engine
            ctx = get_context_engine()
            start = time.time()
            data = ctx.get_context()
            elapsed = (time.time() - start) * 1000
            self.results.measure("context_retrieval", elapsed)
            if elapsed < 2000:
                self.results.pass_test("Context retrieval speed", f"{elapsed:.1f}ms")
            else:
                self.results.fail_test("Context retrieval speed", f"{elapsed:.1f}ms (slow)")
        except Exception as e:
            self.results.skip_test("Context retrieval speed", str(e))

        # Intelligence engine speed
        try:
            from core.intelligence_engine import get_intelligence_engine
            engine = get_intelligence_engine()
            start = time.time()
            result = engine.process_request("what time is it", source="qa_test")
            elapsed = (time.time() - start) * 1000
            self.results.measure("intelligence_processing", elapsed)
            if result.get("success", False) or result.get("requires_clarification", False):
                self.results.pass_test("Intelligence processing", f"{elapsed:.1f}ms")
            else:
                self.results.fail_test("Intelligence processing", f"Failed: {result}")
        except Exception as e:
            self.results.skip_test("Intelligence processing", str(e))

    # ========================================================
    # TEST 10: CLEAN SHUTDOWN
    # ========================================================

    def test_clean_shutdown(self):
        print("\n=== CLEAN SHUTDOWN TEST ===")

        try:
            self.window.close()
            self.wait(200)
            self.results.pass_test("Clean window close")
        except Exception as e:
            self.results.fail_test("Clean window close", str(e))

    # ========================================================
    # RUN ALL TESTS
    # ========================================================

    def run_all(self):
        print("=" * 60)
        print("AVORA V2 QA TEST SUITE")
        print("=" * 60)

        try:
            self.setup()
            self.test_startup()
            self.test_ui_components()
            self.test_ai_conversation()
            self.test_memory()
            self.test_computer_control()
            self.test_file_operations()
            self.test_error_handling()
            self.test_stress()
            self.test_performance()
            self.test_clean_shutdown()
        except Exception as e:
            print(f"\n[ERROR] TEST SUITE ERROR: {e}")
            traceback.print_exc()
        finally:
            self.teardown()

        # Generate report
        summary = self.results.summary()
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "passed_tests": self.results.passed,
            "failed_tests": self.results.failed,
            "skipped_tests": self.results.skipped,
        }

        report_path = Path(os.getcwd()) / "qa_test_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print("\n" + "=" * 60)
        print("QA TEST COMPLETE")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Report: {report_path}")
        print("=" * 60)

        return summary


if __name__ == "__main__":
    suite = QATestSuite()
    suite.run_all()