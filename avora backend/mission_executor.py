"""
========================================================================
AVORA MISSIONS - Mission Executor
========================================================================

Connects missions to AVORA's existing capabilities to actively help
users accomplish tasks.

Architecture:
  Task → Intent Detection → Capability Mapping → Execution → Result → Progress Update

Design Principles:
  - Reuse existing AVORA systems (AI, automation, files, browser)
  - No duplicate capabilities
  - Safe execution with confirmations for risky actions
  - Context-aware assistance

Example Flow:
  User: "Let's work on the homepage"
  → Detects: wants to work on current mission task
  → Maps to: create_file, open_editor, provide_guidance
  → Executes: Creates file, opens VS Code, gives instructions
  → Updates: Marks task in_progress, saves context
  → Remembers: User is working on homepage HTML
"""

from __future__ import annotations

import time
import threading
from typing import Optional, Dict, Any, List
from enum import Enum

from settings import get_setting
from mission_tracker import get_mission_tracker, Mission, Task

# =========================================================================
# EXECUTION INTENTS
# =========================================================================

class ExecutionIntent(Enum):
    """Types of task execution AVORA can perform."""
    GUIDANCE = "guidance"              # Provide instructions/advice
    CREATE_FILE = "create_file"        # Create a file
    OPEN_FILE = "open_file"           # Open existing file
    OPEN_APP = "open_app"             # Launch application
    OPEN_WEBSITE = "open_website"     # Open URL in browser
    SEARCH_WEB = "search_web"         # Google search
    WRITE_CODE = "write_code"         # Generate code snippet
    EXPLAIN_CONCEPT = "explain"       # Teach/explain something
    SET_TIMER = "set_timer"           # Focus timer
    TAKE_NOTES = "take_notes"         # Save notes/memories
    ASK_QUESTION = "ask_question"     # General question
    UNKNOWN = "unknown"               # Needs clarification

# =========================================================================
# EXECUTION CONTEXT
# =========================================================================

class ExecutionContext:
    """Context for task execution."""
    def __init__(self, mission: Mission, task: Task):
        self.mission = mission
        self.task = task
        self.started_at = time.time()
        self.actions_performed = []
        self.files_created = []
        self.files_opened = []
        self.notes = []
        self.result = None
        self.success = False
        self.user_feedback = None

# =========================================================================
# MISSION EXECUTOR
# =========================================================================

class MissionExecutor:
    """
    Executes mission tasks using AVORA's existing capabilities.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._active_executions: Dict[str, ExecutionContext] = {}
        self._execution_history: List[Dict] = []

    def execute_task(self, mission_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Execute a mission task with full AVORA assistance.
        
        Returns execution result with:
        - intent: what AVORA detected
        - actions: what AVORA did
        - guidance: what AVORA recommends
        - context: execution context
        """
        with self._lock:
            tracker = get_mission_tracker()
            mission = tracker.get_mission(mission_id)
            if not mission:
                return {"error": "Mission not found"}
            
            # Find the task
            task = None
            for milestone in mission.milestones:
                for t in milestone.tasks:
                    if t.id == task_id:
                        task = t
                        break
                if task:
                    break
            
            if not task:
                return {"error": "Task not found"}
            
            # Create execution context
            context = ExecutionContext(mission, task)
            execution_id = f"{mission_id}_{task_id}_{int(time.time())}"
            self._active_executions[execution_id] = context
            
            try:
                # Step 1: Detect intent
                intent = self._detect_intent(task, mission)
                context.actions_performed.append(f"Detected intent: {intent.value}")
                
                # Step 2: Execute based on intent
                result = self._execute_intent(intent, task, mission, context)
                
                # Step 3: Update task status
                task.status = "in_progress"
                tracker._save_missions()
                
                # Step 4: Generate guidance
                guidance = self._generate_guidance(intent, task, mission, result)
                
                # Step 5: Save to memory
                self._save_execution_memory(mission, task, intent, result)
                
                context.result = result
                context.success = True
                
                # Store in history
                self._execution_history.append({
                    "execution_id": execution_id,
                    "mission_id": mission_id,
                    "task_id": task_id,
                    "intent": intent.value,
                    "timestamp": time.time(),
                    "success": True,
                })
                
                return {
                    "execution_id": execution_id,
                    "intent": intent.value,
                    "actions": context.actions_performed,
                    "result": result,
                    "guidance": guidance,
                    "context": {
                        "mission_title": mission.title,
                        "task_title": task.title,
                        "milestone": self._get_current_milestone(mission).title if self._get_current_milestone(mission) else None,
                    }
                }
                
            except Exception as e:
                context.success = False
                context.result = {"error": str(e)}
                return {
                    "execution_id": execution_id,
                    "intent": "error",
                    "error": str(e),
                    "guidance": "I encountered an error. Let's try a different approach.",
                }
            finally:
                # Clean up active execution after delay
                threading.Timer(300.0, lambda: self._active_executions.pop(execution_id, None)).start()

    def _detect_intent(self, task: Task, mission: Mission) -> ExecutionIntent:
        """
        Detect what the user wants to do based on task title and description.
        Uses keyword matching and context.
        """
        title_lower = task.title.lower()
        desc_lower = task.description.lower()
        combined = f"{title_lower} {desc_lower}"
        
        # File operations
        if any(word in combined for word in ["create", "build", "write", "make", "develop"]):
            if any(word in combined for word in ["file", "page", "website", "app", "document"]):
                return ExecutionIntent.CREATE_FILE
        
        # Code-related
        if any(word in combined for word in ["code", "program", "implement", "function", "script"]):
            return ExecutionIntent.WRITE_CODE
        
        # Learning/explanation
        if any(word in combined for word in ["learn", "understand", "study", "explain", "concept"]):
            return ExecutionIntent.EXPLAIN_CONCEPT
        
        # Research
        if any(word in combined for word in ["research", "find", "search", "look up", "investigate"]):
            return ExecutionIntent.SEARCH_WEB
        
        # Setup/installation
        if any(word in combined for word in ["setup", "install", "configure", "initialize"]):
            if any(word in combined for word in ["app", "tool", "software", "environment"]):
                return ExecutionIntent.OPEN_APP
            return ExecutionIntent.GUIDANCE
        
        # Testing
        if any(word in combined for word in ["test", "verify", "check", "validate"]):
            return ExecutionIntent.GUIDANCE
        
        # Default: provide guidance
        return ExecutionIntent.GUIDANCE

    def _execute_intent(self, intent: ExecutionIntent, task: Task, mission: Mission, context: ExecutionContext) -> Dict[str, Any]:
        """Execute the detected intent using AVORA's capabilities."""
        
        if intent == ExecutionIntent.GUIDANCE:
            return self._execute_guidance(task, mission)
        
        elif intent == ExecutionIntent.CREATE_FILE:
            return self._execute_create_file(task, mission, context)
        
        elif intent == ExecutionIntent.WRITE_CODE:
            return self._execute_write_code(task, mission, context)
        
        elif intent == ExecutionIntent.EXPLAIN_CONCEPT:
            return self._execute_explain(task, mission)
        
        elif intent == ExecutionIntent.SEARCH_WEB:
            return self._execute_search(task, mission)
        
        elif intent == ExecutionIntent.OPEN_APP:
            return self._execute_open_app(task, mission)
        
        else:
            return {"message": "I can help you with this task. What would you like to do first?"}

    def _execute_guidance(self, task: Task, mission: Mission) -> Dict[str, Any]:
        """Provide step-by-step guidance for a task."""
        return {
            "type": "guidance",
            "message": f"Let's work on: {task.title}",
            "steps": [
                f"1. Understand what '{task.title}' involves",
                f"2. Break it down into smaller steps",
                f"3. Start with the first step",
                "4. Ask for help if you get stuck",
            ],
            "next_step": "Ready to begin. Say 'start' when you're ready, or ask me to clarify anything.",
        }

    def _execute_create_file(self, task: Task, mission: Mission, context: ExecutionContext) -> Dict[str, Any]:
        """Create a file for the task."""
        try:
            # Determine file path based on mission and task
            filename = self._suggest_filename(task, mission)
            
            # Use existing AVORA file creation
            from skills.files import create_file
            
            # Generate initial content based on task
            content = self._generate_file_content(task, mission)
            
            result = create_file(filename, content)
            
            context.files_created.append(filename)
            context.actions_performed.append(f"Created file: {filename}")
            
            # Track file in mission project
            try:
                from mission_exporter import get_mission_exporter
                exporter = get_mission_exporter()
                exporter.track_project_file(mission.id, filename)
            except Exception:
                pass
            
            return {
                "type": "file_created",
                "file_path": filename,
                "message": f"I've created {filename} for you.",
                "next_step": f"Would you like me to open it in your editor?",
                "open_file_intent": True,
                "file_path_to_open": filename,
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"I couldn't create the file automatically: {e}",
                "guidance": f"Let me guide you through creating it manually instead.",
            }

    def _execute_write_code(self, task: Task, mission: Mission, context: ExecutionContext) -> Dict[str, Any]:
        """Generate code for the task using AVORA's AI."""
        try:
            from ai_logic import ask_ai
            
            prompt = f"""Generate code for this task:

Task: {task.title}
Description: {task.description}
Mission: {mission.title}

Provide:
1. Complete, working code
2. Brief explanation of what it does
3. How to use it

Code should be production-ready with comments."""

            code = ask_ai(prompt)
            
            context.actions_performed.append("Generated code using AI")
            
            return {
                "type": "code_generated",
                "code": code,
                "message": f"I've written the code for {task.title}",
                "next_step": "Would you like me to save this to a file?",
                "save_intent": True,
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Code generation failed: {e}",
                "guidance": "Let's try a different approach.",
            }

    def _execute_explain(self, task: Task, mission: Mission) -> Dict[str, Any]:
        """Explain a concept using AVORA's teaching mode."""
        try:
            from ai_logic import ask_ai
            
            prompt = f"""Explain this concept/task in simple terms:

Topic: {task.title}
Context: {task.description}
Mission Goal: {mission.title}

Teaching style:
- Start with a simple analogy
- Break into 2-3 key points
- Give a practical example
- End with a check question"""

            explanation = ask_ai(prompt)
            
            return {
                "type": "explanation",
                "explanation": explanation,
                "message": f"Here's what you need to know about {task.title}:",
                "next_step": "Does that make sense? Ready to try it?",
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Explanation failed: {e}",
            }

    def _execute_search(self, task: Task, mission: Mission) -> Dict[str, Any]:
        """Search the web for information."""
        try:
            from ai_logic import search_google
            
            query = task.title
            result = search_google(query)
            
            return {
                "type": "search_results",
                "query": query,
                "message": f"I searched for '{query}'",
                "results": result,
                "next_step": "Would you like me to summarize what I found?",
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Search failed: {e}",
                "guidance": "Let's try a different approach.",
            }

    def _execute_open_app(self, task: Task, mission: Mission) -> Dict[str, Any]:
        """Open an application."""
        try:
            from ai_logic import open_application
            
            # Extract app name from task
            app_name = task.title.lower()
            for word in ["setup", "install", "configure", "open", "launch"]:
                app_name = app_name.replace(word, "").strip()
            
            if open_application(app_name):
                return {
                    "type": "app_opened",
                    "app": app_name,
                    "message": f"I've opened {app_name}",
                    "next_step": "What would you like to do next?",
                }
            else:
                return {
                    "type": "error",
                    "message": f"Couldn't find {app_name}",
                    "guidance": "Let's try installing it first.",
                }
        except Exception as e:
            return {
                "type": "error",
                "message": f"App launch failed: {e}",
            }

    def _generate_guidance(self, intent: ExecutionIntent, task: Task, mission: Mission, result: Dict) -> str:
        """Generate contextual guidance based on execution result."""
        if result.get("type") == "file_created":
            return f"Great! I've created the file. Now let's work on {task.title}."
        
        elif result.get("type") == "code_generated":
            return f"Here's the code. Review it and let me know if you want changes."
        
        elif result.get("type") == "explanation":
            return f"Now that you understand {task.title}, want to try implementing it?"
        
        elif result.get("type") == "search_results":
            return f"I found some resources. Want me to summarize the key points?"
        
        else:
            return f"Let's continue with {task.title}. What's your next step?"

    def _suggest_filename(self, task: Task, mission: Mission) -> str:
        """Suggest a filename based on task and mission."""
        # Extract from task title
        title = task.title.lower()
        
        # Common patterns
        if "homepage" in title or "home page" in title:
            return "index.html"
        elif "about" in title:
            return "about.html"
        elif "contact" in title:
            return "contact.html"
        elif "style" in title or "css" in title:
            return "styles.css"
        elif "script" in title or "javascript" in title:
            return "script.js"
        
        # Generic: use first few words
        words = task.title.split()[:3]
        filename = "_".join(words).lower()
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        
        return f"{filename}.txt"

    def _generate_file_content(self, task: Task, mission: Mission) -> str:
        """Generate initial file content based on task."""
        try:
            from ai_logic import ask_ai
            
            prompt = f"""Generate starter content for this file:

Task: {task.title}
Description: {task.description}
Mission: {mission.title}

Provide:
1. Basic structure/template
2. Placeholder content
3. Comments explaining sections"""

            content = ask_ai(prompt)
            return content if content else f"# {task.title}\n\nTODO: Implement this\n"
        except Exception:
            return f"# {task.title}\n\nTODO: Implement this\n"

    def _get_current_milestone(self, mission: Mission):
        """Get the current in-progress milestone."""
        for milestone in mission.milestones:
            if milestone.status == "in_progress":
                return milestone
        for milestone in mission.milestones:
            if milestone.status == "pending":
                return milestone
        return None

    def _save_execution_memory(self, mission: Mission, task: Task, intent: ExecutionIntent, result: Dict):
        """Save execution context to memory."""
        try:
            from memory import add_memory
            
            # Save key execution details
            memory_text = (
                f"Mission '{mission.title}': Working on task '{task.title}' "
                f"(intent: {intent.value})"
            )
            add_memory(memory_text, category="mission_execution")
            
            # Save specific results
            if result.get("type") == "file_created":
                add_memory(
                    f"Created file: {result.get('file_path')} for mission '{mission.title}'",
                    category="mission_files"
                )
            elif result.get("type") == "code_generated":
                add_memory(
                    f"Generated code for: {task.title}",
                    category="mission_execution"
                )
        except Exception as e:
            print(f"[EXECUTOR] Memory save error: {e}")

    def get_active_execution(self, mission_id: str, task_id: str) -> Optional[ExecutionContext]:
        """Get active execution context."""
        key = f"{mission_id}_{task_id}"
        for exec_id, context in self._active_executions.items():
            if exec_id.startswith(key):
                return context
        return None

    def get_execution_history(self, mission_id: str = None, limit: int = 10) -> List[Dict]:
        """Get execution history."""
        with self._lock:
            history = self._execution_history
            
            if mission_id:
                history = [h for h in history if h.get("mission_id") == mission_id]
            
            return history[-limit:]

    def mark_task_completed(self, mission_id: str, task_id: str, result: Dict = None) -> bool:
        """Mark a task as completed after execution."""
        with self._lock:
            tracker = get_mission_tracker()
            
            # Update task status
            if tracker.complete_task(mission_id, task_id):
                # Save execution result
                if result:
                    self._execution_history.append({
                        "mission_id": mission_id,
                        "task_id": task_id,
                        "result": result,
                        "completed_at": time.time(),
                        "success": True,
                    })
                
                # Save memory
                try:
                    from memory import add_memory
                    mission = tracker.get_mission(mission_id)
                    if mission:
                        add_memory(
                            f"Completed task in mission '{mission.title}'",
                            category="mission_progress"
                        )
                except Exception:
                    pass
                
                return True
            return False

# =========================================================================
# GLOBAL INSTANCE
# =========================================================================

_executor: Optional[MissionExecutor] = None
_executor_lock = threading.Lock()


def get_mission_executor() -> MissionExecutor:
    """Get the global mission executor instance."""
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = MissionExecutor()
    return _executor


# =========================================================================
# PUBLIC API
# =========================================================================

__all__ = [
    "MissionExecutor",
    "ExecutionContext",
    "ExecutionIntent",
    "get_mission_executor",
]