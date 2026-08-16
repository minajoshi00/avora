with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace set_thinking True with set_state "thinking"
content = content.replace(
    'self.character_call("set_thinking", True)',
    'self.character_call("set_state", "thinking")'
)

# Replace set_thinking False with set_state "idle"  
content = content.replace(
    'self.character_call("set_thinking", False)',
    'self.character_call("set_state", "idle")'
)

# Replace set_expression "idle" with set_state "idle" where appropriate
# But be careful - some set_expression "idle" are in different contexts
# Let me replace specific patterns

# Replace set_expression "idle" after thinking stops
# Pattern: set_expression "idle" after set_thinking False
# Actually, let me just replace the specific known patterns

# Replace set_expression "sad" with set_state "error" in error contexts
# But some "sad" are legitimate sadness from emotion detection

# Let me be more targeted - replace the specific lines we know

# Line 2764: set_expression "idle" 
content = content.replace(
    '''self.character_call("set_expression", "idle")''',
    '''self.character_call("set_state", "idle")'''
).replace(
    # Only replace specific occurrences - let me check which ones
)

# Actually, let me just replace the exact patterns we identified
patterns_to_replace = [
    (2764, 'self.character_call("set_expression", "idle")'),
    (2778, 'self.character_call("set_expression", "sad")'),
    (2881, 'self.character_call("set_thinking", True)'),  # already handled
    (2908, 'self.character_call("set_thinking", False)'),
    (2933, 'self.character_call("set_thinking", False)'),
    (2934, 'self.character_call("set_expression", "sad")'),
    (2959, 'self.character_call("set_thinking", False)'),
    (2960, 'self.character_call("set_expression", "idle")'),
]

# Let me just do targeted replacements
replacements = {
    'self.character_call("set_thinking", True)': 'self.character_call("set_state", "thinking")',
    'self.character_call("set_thinking", False)': 'self.character_call("set_state", "idle")',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacements done")
"