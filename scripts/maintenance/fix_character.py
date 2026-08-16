with open('C:\Users\minaj\OneDrive\Desktop\avora\avora_backend\character.py', 'r') as f:
    content = f.read()

# Replace set_talking to add activity tracking
old_talking = """        self.talking = bool(
            talking
        )

        if self.talking:
"""

new_talking = """        self.talking = bool(
            talking
        )

        # Log activity timeline
        if self.talking:
            add_activity_entry('speaking', success=True)
        else:
            add_activity_entry('stopped_speaking', success=True)

        if self.talking:
"""

if old_talking in content:
    content = content.replace(old_talking, new_talking)
    print("Replaced set_talking old part")
else:
    print("Old set_talking part not found")

# Write back
with open('C:\Users\minaj\OneDrive\Desktop\avora\avora_backend\character.py', 'w') as f:
    f.write(content)

print("Done writing character.py")