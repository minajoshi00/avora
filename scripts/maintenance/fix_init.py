#!/usr/bin/env python3
import sys
import re

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py"
with open(filepath, "rb") as f:
    content = f.read()

# 1. Update the setStyleSheet call to remove hardcoded gradient and use theme
# Replace the entire stylesheet block
old_stylesheet = b'''from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, qApp, QPropertyAnimation

from agent_bridge import AgentBridge

from theme import get_current_theme, apply_theme_to_app, generate_qss'''

# Actually, the imports are already there. Let me just update the init method.

# 2. Replace the hardcoded stylesheet in __init__
old_init_stylesheet = b'''self.setStyleSheet("""\n            QMainWindow {\n                background: qlineargradient(180deg, #0a0a0f, #1a1a2e);\n            }\n            * {\n                font-family: 'Segoe UI', 'Inter', sans-serif;\n            }\n        """')'''

new_init_stylesheet = b'# Apply theme at startup\napply_theme_to_app()\nself.setStyleSheet(generate_qss())'

if old_init_stylesheet in content:
    content = content.replace(old_init_stylesheet, new_init_stylesheet)
    print("Init stylesheet updated")
else:
    print("Init stylesheet pattern not found, trying alternative")
    # Try without the triple quotes
    old_init_stylesheet2 = b'self.setStyleSheet("""\n            QMainWindow {\n                background: qlineargradient(180deg, #0a0a0f, #1a1a2e);\n            }\n            \\* {\n                font-family: \'Segoe UI\', \'Inter\', sans-serif;\n            }\n        """')'
    if old_init_stylesheet2 in content:
        content = content.replace(old_init_stylesheet2, new_init_stylesheet)
        print("Init stylesheet updated (alternative)")
    else:
        print("Could not find init stylesheet pattern")

# 3. Update the title font from Arial to Segoe UI
old_title_font = b'title.setFont(QFont("Arial", 16, QFont.Weight.Bold))'
new_title_font = b'title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))'

if old_title_font in content:
    content = content.replace(old_title_font, new_title_font)
    print("Title font updated to Segoe UI")
else:
    print("Title font pattern not found")

# 4. Update header background to use theme-appropriate colors
old_header_bg = b'header.setStyleSheet("background: rgba(255,255,255,0.03); padding: 16px;")'
new_header_bg = b'header.setStyleSheet("background: rgba(255,255,255,0.03); padding: 16px;")'

# The header background is fine as-is for now - it's a very light transparent layer
# that works with both light and dark themes

# 5. Update status label color to use theme
old_state_label = b'self.state_label.setStyleSheet("color: #888;")'
new_state_label = b'self.state_label.setStyleSheet("color: #6b7280;")'  # gray-500

if old_state_label in content:
    content = content.replace(old_state_label, new_state_label)
    print("State label color updated")
else:
    print("State label color pattern not found")

# Write the modified content back
with open(filepath, "wb") as f:
    f.write(content)

print("\nInit method updates complete")