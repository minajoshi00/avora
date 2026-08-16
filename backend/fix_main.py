#!/usr/bin/env python3
"""Fix the broken create_ui structure in main.py"""
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the broken section: from footer addWidget to the HEADER comment
# that's inside the broken on_theme_changed method
pattern = r'''        sidebar_layout\.addWidget\(
            footer
        \)

        # ====================================================
        # SETTINGS LISTENER
        # ====================================================

        try:

            add_settings_listener\(
                self\.on_setting_changed
            \)

        except Exception as error:

            print\(
                "SETTINGS LISTENER ERROR:",
                error
            \)

        # ====================================================
        # THEME LISTENER
        # ====================================================

        try:

            add_theme_listener\(
                self\.on_theme_changed
            \)

        except Exception as error:

            print\(
                "THEME LISTENER ERROR:",
                error
            \)

    # ========================================================
    # THEME CHANGE
    # ========================================================

    def on_theme_changed\(
        self,
        theme,
    \):

        self\.setStyleSheet\(
            generate_qss\(\)
        \)

        # ====================================================
        # HEADER
        # ===================================================='''

replacement = '''        sidebar_layout.addWidget(
            footer
        )

        # ====================================================
        # RIGHT SIDE
        # ====================================================

        right_side = QFrame()

        right_side.setObjectName(
            "RightSide"
        )

        right_layout = QVBoxLayout(
            right_side
        )

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(
            0
        )

        # ====================================================
        # HEADER
        # ===================================================='''

new_content, count = re.subn(pattern, replacement, content)

if count > 0:
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"FIXED: Replaced {count} occurrence(s)")
else:
    print("ERROR: Pattern not found with regex")
    # Debug: show what's around the footer section
    idx = content.find('sidebar_layout.addWidget(\n            footer')
    if idx >= 0:
        print(f"Found footer at index {idx}")
        print("Content around it:")
        print(repr(content[idx:idx+500]))
    else:
        print("Could not find footer section at all")
