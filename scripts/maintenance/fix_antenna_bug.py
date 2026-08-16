#!/usr/bin/env python3
import sys

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora backend\character.py"
with open(filepath, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Add target_antenna_pulse and target_core_pulse initialization in setup_state
# Find the line with "self.target_shake = 0.0" and add after it
old_pattern = "self.target_shake = 0.0\n\n        # -----------"

new_pattern = "self.target_shake = 0.0\n\n        # Target antenna pulse for smooth animation\n        self.target_antenna_pulse = 0.0\n        # Target core pulse for smooth animation\n        self.target_core_pulse = 0.0\n\n        # -----------"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open(filepath, "w", encoding="utf-8", errors="replace") as f:
        f.write(content)
    print("Fixed: added target_antenna_pulse and target_core_pulse initialization")
else:
    print("Pattern not found, searching alternative...")
    # Try to find target_shake initialization
    if "self.target_shake = 0.0" in content:
        idx = content.index("self.target_shake = 0.0")
        # Print context
        start = max(0, idx - 50)
        end = min(len(content), idx + 100)
        print(f"Found at index {idx}:")
        print(repr(content[start:end]))
    else:
        print("target_shake not found either")