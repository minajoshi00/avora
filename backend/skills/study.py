"""
============================================================
study.py
AI Friend - Interactive Study & Tutoring Skill
============================================================
Supports:
- Learn Mode (intelligent step-by-step tutor)
- Explain Mode (concept & formula symbol breakdown)
- Practice Mode (practice questions & evaluation)
- Quiz Mode (interactive multi-question quiz)
- Revision Mode (structured summary notes)
- Exam Mode (mock exam preparation)
"""

from __future__ import annotations
from typing import Optional


def detect_study_mode(message: str) -> Optional[str]:
    """Identify specialized study mode from user message."""
    if not message:
        return None

    lower = str(message).strip().lower()

    if any(k in lower for k in ["quiz me", "test me", "take a quiz", "quiz mode"]):
        return "quiz"

    if any(k in lower for k in ["practice mode", "practice questions", "give me practice", "practice problem"]):
        return "practice"

    if any(k in lower for k in ["revision mode", "revision notes", "summary notes", "quick revision", "full notes", "complete notes"]):
        return "revision"

    if any(k in lower for k in ["exam mode", "prepare me for exam", "mock exam", "exam practice"]):
        return "exam"

    if any(k in lower for k in ["explain mode", "explain this", "what is", "define"]):
        return "explain"

    if any(k in lower for k in ["teach me", "learn mode", "help me learn", "help me study", "studying"]):
        return "learn"

    return None


def get_study_mode_prompt_instructions(mode: str, topic: str) -> str:
    """Return explicit instruction prompt context for the selected study mode."""
    topic_str = topic or "the subject"

    if mode == "quiz":
        return (
            f"\n[STUDY SKILL: QUIZ MODE]\n"
            f"Topic: {topic_str}\n"
            "Instructions:\n"
            "1. Present 1 clear question to test the student's knowledge.\n"
            "2. Ask the student for their answer before revealing full solutions.\n"
            "3. Provide encouraging feedback and score evaluation.\n"
        )
    elif mode == "practice":
        return (
            f"\n[STUDY SKILL: PRACTICE MODE]\n"
            f"Topic: {topic_str}\n"
            "Instructions:\n"
            "1. Provide a practical problem/exercise.\n"
            "2. Ask the student to solve it step-by-step.\n"
            "3. Offer hints if needed and explain the complete solution clearly.\n"
        )
    elif mode == "revision":
        return (
            f"\n[TEACHING MODE: FULL REVISION NOTES]\n"
            f"Topic: {topic_str}\n"
            "You must provide a comprehensive, well-structured revision document:\n"
            "1. Start with a brief overview of the topic.\n"
            "2. Break content into clear sections with bold headings.\n"
            "3. Explain every formula by defining each symbol and showing a simple worked example.\n"
            "4. Include key definitions, diagram descriptions, and important facts.\n"
            "5. Add top exam tips and common mistakes to avoid at the end.\n"
            "Make it easy to read and study from, like a textbook summary.\n"
        )
    elif mode == "exam":
        return (
            f"\n[STUDY SKILL: EXAM MODE]\n"
            f"Topic: {topic_str}\n"
            "Instructions:\n"
            "1. Provide high-yield exam questions (Conceptual & Numerical).\n"
            "2. Include marking scheme guidelines and complete model answers.\n"
        )
    elif mode == "explain":
        return (
            f"\n[TEACHING MODE: ENHANCED TUTOR]\n"
            f"Topic: {topic_str}\n"
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
        )
    else:  # learn mode
        return (
            f"\n[TEACHING MODE: ENHANCED TUTOR]\n"
            f"Topic: {topic_str}\n"
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
        )
