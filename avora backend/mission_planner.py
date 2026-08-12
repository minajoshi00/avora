"""
========================================================================
AVORA MISSIONS - Mission Planner
========================================================================

Natural language planning engine that converts user goals into
structured Missions with Milestones and Tasks.

Architecture:
  User Input → NLU → Mission Structure → AI Enhancement → Final Plan

Features:
  - Rule-based pattern matching for common goals
  - AI-assisted breakdown for complex goals
  - Category detection (project, learning, work, personal)
  - Priority estimation
  - Deadline suggestion
  - Milestone generation
  - Task breakdown

Integration:
  - Uses existing AI providers (Gemini/Groq)
  - Creates missions via MissionTracker
  - Generates actionable steps

Example:
    from mission_planner import get_mission_planner
    
    planner = get_mission_planner()
    mission = planner.plan_mission("I want to build a website")
    # Returns: Mission with 5-8 milestones and 15-20 tasks
"""

from __future__ import annotations

import re
import time
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from settings import get_setting
from mission_tracker import (
    get_mission_tracker,
    Mission,
    Milestone,
    Task,
)

# =========================================================================
# PLANNER CONFIGURATION
# =========================================================================

# Patterns for common goal types
_GOAL_PATTERNS = {
    "website": {
        "keywords": ["website", "web site", "site", "webpage", "web app"],
        "category": "project",
        "milestones": [
            ("Planning & Design", "Define requirements and design the site structure"),
            ("Learn Basics", "Learn HTML, CSS, and JavaScript fundamentals"),
            ("Setup Project", "Set up development environment and project structure"),
            ("Build Homepage", "Create the main landing page"),
            ("Build Core Pages", "Build About, Contact, and other essential pages"),
            ("Add Interactivity", "Add JavaScript functionality and animations"),
            ("Testing", "Test across browsers and devices"),
            ("Deployment", "Deploy to hosting and configure domain"),
        ],
    },
    "python": {
        "keywords": ["python", "learn python", "python programming"],
        "category": "learning",
        "milestones": [
            ("Setup & Basics", "Install Python and learn basic syntax"),
            ("Variables & Data Types", "Master strings, numbers, lists, dictionaries"),
            ("Control Flow", "Learn if/else, loops, and logical operators"),
            ("Functions", "Write reusable functions and understand scope"),
            ("File I/O", "Read and write files, handle errors"),
            ("Object-Oriented Programming", "Classes, objects, inheritance, polymorphism"),
            ("Libraries & Modules", "Learn pip, virtual environments, and popular libraries"),
            ("Build Project", "Create a complete Python project"),
        ],
    },
    "app": {
        "keywords": ["app", "application", "mobile app", "desktop app"],
        "category": "project",
        "milestones": [
            ("Planning", "Define app features and target platform"),
            ("Design", "Create UI/UX mockups and wireframes"),
            ("Setup", "Set up development environment and tools"),
            ("Core Features", "Implement main functionality"),
            ("UI Implementation", "Build user interface screens"),
            ("Testing", "Test on target platforms"),
            ("Polish & Optimization", "Optimize performance and fix bugs"),
            ("Release", "Prepare for app store/desktop release"),
        ],
    },
    "business": {
        "keywords": ["business", "startup", "company", "launch business"],
        "category": "business",
        "milestones": [
            ("Market Research", "Research target market and competitors"),
            ("Business Plan", "Create business plan and financial projections"),
            ("Legal Setup", "Register business and handle legal requirements"),
            ("Branding", "Create brand identity, logo, and messaging"),
            ("MVP Development", "Build minimum viable product"),
            ("Marketing Strategy", "Develop marketing and growth strategy"),
            ("Launch Preparation", "Prepare for launch day"),
            ("Launch & Iterate", "Launch and gather feedback"),
        ],
    },
    "exam": {
        "keywords": ["exam", "test", "prepare for exam", "study for test"],
        "category": "learning",
        "milestones": [
            ("Assessment", "Assess current knowledge and identify gaps"),
            ("Study Plan", "Create structured study schedule"),
            ("Core Topics", "Study fundamental concepts"),
            ("Practice Problems", "Solve practice questions and problems"),
            ("Review Weak Areas", "Focus on difficult topics"),
            ("Mock Tests", "Take practice exams under timed conditions"),
            ("Final Review", "Review all material one last time"),
            ("Exam Day", "Take the exam with confidence"),
        ],
    },
    "video": {
        "keywords": ["video", "youtube", "content", "create videos"],
        "category": "creative",
        "milestones": [
            ("Planning", "Define content type and target audience"),
            ("Setup Equipment", "Get camera, microphone, and lighting"),
            ("Learn Editing", "Learn video editing software"),
            ("Create First Video", "Produce and upload first video"),
            ("Optimize Content", "Improve titles, thumbnails, descriptions"),
            ("Build Library", "Create 10+ videos consistently"),
            ("Grow Audience", "Implement growth strategies"),
            ("Monetize", "Set up monetization and sponsorships"),
        ],
    },
}

# Generic fallback milestones for unknown categories
_GENERIC_MILESTONES = [
    ("Planning", "Define goals and requirements"),
    ("Research", "Gather information and resources"),
    ("Setup", "Prepare tools and environment"),
    ("First Steps", "Begin initial implementation"),
    ("Development", "Complete core work"),
    ("Testing & Review", "Validate quality and correctness"),
    ("Refinement", "Polish and improve"),
    ("Completion", "Finalize and deliver"),
]


# =========================================================================
# MISSION PLANNER
# =========================================================================

class MissionPlanner:
    """
    Converts natural language goals into structured missions.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._ai_available = self._check_ai_available()

    def _check_ai_available(self) -> bool:
        """Check if AI providers are available for enhanced planning."""
        try:
            from ai_logic import gemini, groq
            return gemini is not None or groq is not None
        except ImportError:
            return False

    def plan_mission(
        self,
        user_input: str,
        use_ai: bool = True,
    ) -> Optional[Mission]:
        """
        Plan a mission from natural language input.
        
        Args:
            user_input: Natural language goal from user
            use_ai: Whether to use AI for enhanced breakdown
            
        Returns:
            Mission object with milestones and tasks, or None if unclear
        """
        if not user_input or not user_input.strip():
            return None

        with self._lock:
            # 1. Extract goal information
            goal_info = self._extract_goal_info(user_input)
            
            # 2. Detect category
            category = self._detect_category(user_input)
            
            # 3. Create base mission
            mission = Mission(
                title=goal_info["title"],
                description=goal_info["description"],
                category=category,
            )
            
            # 4. Generate milestones
            if use_ai and self._ai_available:
                milestones = self._ai_generate_milestones(mission, user_input)
            else:
                milestones = self._rule_based_milestones(user_input, category)
            
            # 5. Add milestones to mission
            for milestone_title, milestone_desc in milestones:
                milestone = Milestone(
                    title=milestone_title,
                    description=milestone_desc,
                )
                mission.add_milestone(milestone)
            
            # 6. Generate tasks for first few milestones
            self._generate_initial_tasks(mission)
            
            # 7. Estimate deadline
            mission.deadline = self._estimate_deadline(mission)
            
            # 8. Set priority based on keywords
            mission.priority = self._estimate_priority(user_input)
            
            return mission

    def _extract_goal_info(self, text: str) -> Dict[str, str]:
        """Extract title and description from user input."""
        text = text.strip()
        
        # Remove common prefixes
        prefixes = [
            r"^(?:i\s+)?(?:want\s+to|wanna|gonna|planning\s+to|trying\s+to|need\s+to|have\s+to)\s+",
            r"^(?:let's|lets)\s+",
            r"^(?:my\s+goal\s+is\s+to|i'?d\s+like\s+to)\s+",
            r"^(?:help\s+me\s+)?(?:build|create|make|learn|start|develop)\s+",
        ]
        
        cleaned = text.lower()
        for prefix in prefixes:
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter
        cleaned = cleaned.strip()
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # Generate title (first 50 chars)
        title = cleaned[:50] if len(cleaned) > 50 else cleaned
        if not title:
            title = text[:50]
        
        # Description is the full text
        description = text
        
        return {
            "title": title,
            "description": description,
        }

    def _detect_category(self, text: str) -> str:
        """Detect mission category from text."""
        text_lower = text.lower()
        
        # Check explicit category mentions
        if any(word in text_lower for word in ["learn", "study", "understand", "master", "course"]):
            return "learning"
        if any(word in text_lower for word in ["business", "startup", "company", "launch", "product"]):
            return "business"
        if any(word in text_lower for word in ["project", "build", "create", "make", "develop"]):
            return "project"
        if any(word in text_lower for word in ["exam", "test", "quiz", "prepare"]):
            return "learning"
        if any(word in text_lower for word in ["video", "youtube", "content", "channel"]):
            return "creative"
        if any(word in text_lower for word in ["app", "application", "software"]):
            return "project"
        if any(word in text_lower for word in ["website", "site", "web"]):
            return "project"
        
        # Check pattern-based categories
        for pattern_key, pattern_data in _GOAL_PATTERNS.items():
            if any(keyword in text_lower for keyword in pattern_data["keywords"]):
                return pattern_data["category"]
        
        return "general"

    def _rule_based_milestones(
        self,
        text: str,
        category: str,
    ) -> List[tuple[str, str]]:
        """Generate milestones using rule-based patterns."""
        text_lower = text.lower()
        
        # Check for matching pattern
        for pattern_key, pattern_data in _GOAL_PATTERNS.items():
            if any(keyword in text_lower for keyword in pattern_data["keywords"]):
                return pattern_data["milestones"]
        
        # Return generic milestones
        return _GENERIC_MILESTONES

    def _ai_generate_milestones(
        self,
        mission: Mission,
        user_input: str,
    ) -> List[tuple[str, str]]:
        """
        Use AI to generate custom milestones for complex goals.
        Falls back to rule-based if AI fails.
        """
        try:
            from ai_logic import ask_ai
            
            prompt = f"""Break down this goal into 5-7 clear milestones with brief descriptions.

Goal: {user_input}

Format each milestone as:
Milestone Title: Description

Example:
Learn Basics: Install tools and understand fundamental concepts
Build Core: Create the main functionality
Test: Validate everything works

Keep it concise and actionable."""

            response = ask_ai(prompt)
            if not response:
                return self._rule_based_milestones(user_input, mission.category)
            
            # Parse AI response
            milestones = []
            for line in response.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':', 1)
                    title = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    # Remove numbering (e.g., "1. ")
                    title = re.sub(r'^\d+\.\s*', '', title)
                    if title and len(title) < 100:
                        milestones.append((title, desc))
            
            if len(milestones) >= 3:
                return milestones
            
            # Fallback to rule-based
            return self._rule_based_milestones(user_input, mission.category)
            
        except Exception as e:
            print(f"[PLANNER] AI generation error: {e}")
            return self._rule_based_milestones(user_input, mission.category)

    def _generate_initial_tasks(self, mission: Mission) -> None:
        """
        Generate initial tasks for the first 2 milestones.
        This gives the user a starting point without overwhelming them.
        """
        if not mission.milestones:
            return
        
        # Generate tasks for first 2 milestones
        for milestone in mission.milestones[:2]:
            # Generate 2-3 tasks per milestone
            num_tasks = min(3, max(2, len(milestone.title) // 10))
            
            for i in range(num_tasks):
                task_title = self._generate_task_title(milestone.title, i, num_tasks)
                task = Task(
                    title=task_title,
                    description=f"Part of: {milestone.title}",
                    estimated_minutes=30,
                )
                milestone.tasks.append(task)

    def _generate_task_title(self, milestone_title: str, index: int, total: int) -> str:
        """Generate a task title based on milestone."""
        templates = [
            f"Research and gather resources for {milestone_title.lower()}",
            f"Complete initial setup for {milestone_title.lower()}",
            f"Implement core functionality for {milestone_title.lower()}",
        ]
        
        if index < len(templates):
            return templates[index]
        
        return f"Complete step {index + 1} of {milestone_title}"

    def _estimate_deadline(self, mission: Mission) -> Optional[float]:
        """Estimate a reasonable deadline based on mission complexity."""
        total_tasks = sum(len(m.tasks) for m in mission.milestones)
        total_minutes = total_tasks * 30  # 30 min per task average
        
        # Add buffer for learning/research
        if mission.category == "learning":
            total_minutes *= 1.5
        
        # Convert to days (assuming 2 hours per day of focused work)
        days_needed = total_minutes / 120.0
        days_needed = max(1.0, min(days_needed, 90.0))  # Cap at 90 days
        
        deadline = time.time() + (days_needed * 86400)
        return deadline

    def _estimate_priority(self, text: str) -> int:
        """Estimate priority based on urgency keywords."""
        text_lower = text.lower()
        
        high_priority = ["urgent", "asap", "immediately", "critical", "important", "deadline"]
        medium_priority = ["soon", "this week", "next week", "priority"]
        
        if any(word in text_lower for word in high_priority):
            return 4
        if any(word in text_lower for word in medium_priority):
            return 3
        
        return 2  # Default medium priority

    def enhance_mission_with_ai(
        self,
        mission: Mission,
    ) -> Mission:
        """
        Use AI to enhance an existing mission with more detailed
        milestones and tasks.
        """
        if not self._ai_available:
            return mission
        
        try:
            from ai_logic import ask_ai
            
            prompt = f"""Enhance this mission with detailed, actionable milestones and tasks.

Mission: {mission.title}
Description: {mission.description}
Category: {mission.category}

Provide:
1. 5-8 specific milestones
2. 3-5 tasks for each milestone
3. Time estimates for each task (in minutes)

Format as JSON:
{{
  "milestones": [
    {{
      "title": "Milestone name",
      "description": "What this milestone achieves",
      "tasks": [
        {{"title": "Task name", "minutes": 30}}
      ]
    }}
  ]
}}"""

            response = ask_ai(prompt)
            if not response:
                return mission
            
            # Try to parse JSON from response
            try:
                # Extract JSON from response (might be wrapped in markdown)
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    import json
                    data = json.loads(json_match.group())
                    
                    # Clear existing and rebuild
                    mission.milestones = []
                    for m_data in data.get("milestones", []):
                        milestone = Milestone(
                            title=m_data.get("title", "Untitled"),
                            description=m_data.get("description", ""),
                        )
                        for t_data in m_data.get("tasks", []):
                            task = Task(
                                title=t_data.get("title", "Task"),
                                estimated_minutes=t_data.get("minutes", 30),
                            )
                            milestone.tasks.append(task)
                        mission.add_milestone(milestone)
            except Exception:
                # If parsing fails, keep original mission
                pass
            
            return mission
            
        except Exception as e:
            print(f"[PLANNER] AI enhancement error: {e}")
            return mission

    def suggest_next_steps(
        self,
        mission: Mission,
    ) -> List[Dict[str, Any]]:
        """
        Suggest next steps for a mission based on current progress.
        """
        suggestions = []
        
        # If no milestones, suggest creating some
        if not mission.milestones:
            suggestions.append({
                "action": "create_milestones",
                "message": "Let's break this down into milestones.",
                "priority": 1,
            })
            return suggestions
        
        # Check for incomplete milestones
        incomplete_milestones = [m for m in mission.milestones if m.status != "completed"]
        
        if not incomplete_milestones:
            suggestions.append({
                "action": "complete_mission",
                "message": "All milestones are complete! Ready to finish the mission?",
                "priority": 1,
            })
            return suggestions
        
        # Get next task
        next_action = mission.get_next_task()
        if next_action:
            suggestions.append({
                "action": "work_on_task",
                "task_id": next_action.id,
                "message": f"Continue with: {next_action.title}",
                "priority": 2,
            })
        
        # Check for milestones without tasks
        for milestone in incomplete_milestones[:2]:
            if not milestone.tasks:
                suggestions.append({
                    "action": "add_tasks",
                    "milestone_id": milestone.id,
                    "message": f"Break down '{milestone.title}' into tasks",
                    "priority": 3,
                })
        
        return suggestions


# =========================================================================
# GLOBAL INSTANCE
# =========================================================================

_planner: Optional[MissionPlanner] = None
_planner_lock = threading.Lock()


def get_mission_planner() -> MissionPlanner:
    """Get the global mission planner instance."""
    global _planner
    if _planner is None:
        with _planner_lock:
            if _planner is None:
                _planner = MissionPlanner()
    return _planner


# =========================================================================
# PUBLIC API
# =========================================================================

__all__ = [
    "MissionPlanner",
    "get_mission_planner",
]