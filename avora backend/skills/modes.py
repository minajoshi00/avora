"""
========================================================================
modes.py
NOVA - Intelligent Mode System
========================================================================
Supports automatic and manual mode selection for different
interaction contexts.

Modes:
- Chat: General conversation
- Study: Learning and tutoring
- Coding: Programming help
- Research: Deep information gathering
- Creative: Creative writing, ideas
- Planning: Task and project planning
- Computer: System/computer assistant tasks
========================================================================
"""

from typing import Optional

# Mode definitions
MODES = {
    "chat": {
        "name": "Chat",
        "icon": "💬",
        "description": "General conversation",
        "prompt_instruction": "",
    },
    "study": {
        "name": "Study",
        "icon": "📚",
        "description": "Learning and tutoring",
        "prompt_instruction": (
            "\n[TEACHING MODE: ENHANCED TUTOR]\n"
            "You are now acting as an intelligent, patient tutor. Follow this exact flow:\n"
            "1. FIRST: Restate the student's question in your own words to confirm understanding.\n"
            "   Example: 'So basically, you're asking how...'\n"
            "2. CONCEPT BREAKDOWN: Split the topic into 2-4 digestible parts. Explain each part clearly.\n"
            "3. STEP-BY-STEP: If applicable, walk through the solution or process in numbered steps with reasoning.\n"
            "4. EXAMPLES: Provide ONE simple example and ONE practical real-world example.\n"
            "5. COMMON PITFALLS: Warn about 1-2 typical mistakes students make with this topic.\n"
            "6. NATURAL FOLLOW-UP: End with ONE supportive follow-up question to check understanding.\n"
            "   Example: 'Does that make sense so far, or should I break down step 2 more?'\n"
            "Use simple, clear language. Be encouraging but precise. Never skip steps.\n"
            "Keep a natural, warm tone - like a smart friend helping out, not a textbook.\n"
        ),
    },
    "coding": {
        "name": "Coding",
        "icon": "💻",
        "description": "Programming help",
        "prompt_instruction": (
            "\n[MODE: CODING]\n"
            "Provide clean, working code examples. Explain the logic step by step. "
            "Include comments in code. Suggest best practices and potential pitfalls. "
            "Focus on practical, runnable solutions."
        ),
    },
    "research": {
        "name": "Research",
        "icon": "🔍",
        "description": "Deep information gathering",
        "prompt_instruction": (
            "\n[MODE: RESEARCH]\n"
            "Provide thorough, well-structured information. "
            "Include key facts, data points, and sources where applicable. "
            "Organize information with clear headings and bullet points. "
            "Be objective and balanced in presenting information."
        ),
    },
    "creative": {
        "name": "Creative",
        "icon": "🎨",
        "description": "Creative writing and ideas",
        "prompt_instruction": (
            "\n[MODE: CREATIVE]\n"
            "Be imaginative and expressive. Use vivid language and creative ideas. "
            "Think outside the box while remaining coherent and engaging. "
            "Encourage brainstorming and creative exploration."
        ),
    },
    "planning": {
        "name": "Planning",
        "icon": "📋",
        "description": "Task and project planning",
        "prompt_instruction": (
            "\n[MODE: PLANNING]\n"
            "Help organize tasks, set priorities, and create actionable plans. "
            "Break down complex projects into manageable steps. "
            "Suggest timelines, resources, and milestones. "
            "Be practical and structured."
        ),
    },
    "computer": {
        "name": "Computer",
        "icon": "🖥️",
        "description": "System and computer tasks",
        "prompt_instruction": (
            "\n[MODE: COMPUTER ASSISTANT]\n"
            "Focus on executing computer tasks efficiently. "
            "Be precise with commands and file paths. "
            "Always confirm before destructive actions. "
            "Provide clear feedback on what was done."
        ),
    },
}

# Keywords for auto-detection
_MODE_KEYWORDS = {
    "study": [
        "teach me", "explain", "help me learn", "help me study",
        "i am studying", "studying for", "study ", "learn ",
        "what is", "how does", "class ", "grade ", "chapter",
        "lesson", "tutor", "homework", "assignment",
    ],
    "coding": [
        "code", "programming", "python", "javascript", "function",
        "debug", "error", "syntax", "algorithm", "api",
        "write a", "create a program", "fix this", "refactor",
    ],
    "research": [
        "research", "tell me about", "information on", "history of",
        "analysis", "compare", "difference between", "overview",
        "summary of", "details about",
    ],
    "creative": [
        "write a story", "poem", "creative", "imagine", "brainstorm",
        "idea", "design", "art", "music", "invent",
    ],
    "planning": [
        "plan", "organize", "schedule", "project plan", "roadmap",
        "timeline", "milestone", "task list", "to-do", "prioritize",
    ],
    "computer": [
        "open ", "launch ", "start ", "run ", "shutdown", "restart",
        "file", "folder", "gmail", "email", "screenshot",
        "system", "settings", "battery", "ram", "cpu",
    ],
}


def detect_mode(message: str) -> str:
    """Auto-detect the best mode based on user message."""
    if not message:
        return "chat"

    lower = message.lower().strip()

    # Check for explicit mode switch
    for mode_id in MODES:
        if mode_id == "chat":
            continue
        if f"/{mode_id}" in lower or f"#{mode_id}" in lower:
            return mode_id

    # Score each mode
    scores = {mode_id: 0 for mode_id in MODES}

    for mode_id, keywords in _MODE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lower:
                scores[mode_id] += 1

    # Get the best match
    best_mode = "chat"
    best_score = 0

    for mode_id, score in scores.items():
        if score > best_score:
            best_score = score
            best_mode = mode_id

    return best_mode


def get_mode_instruction(mode: str) -> str:
    """Get the prompt instruction for a given mode."""
    mode_data = MODES.get(mode, MODES["chat"])
    return mode_data.get("prompt_instruction", "")


def get_mode_info(mode: str) -> dict:
    """Get full mode information."""
    return MODES.get(mode, MODES["chat"])


def get_all_modes() -> dict:
    """Get all available modes."""
    return dict(MODES)