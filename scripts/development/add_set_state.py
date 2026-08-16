with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'r') as f:
    content = f.read()

# Add set_state method before the ACTIVITY section
activity_marker = "# ---------------- ACTIVITY ----------------"
activity_idx = content.find(activity_marker)

if activity_idx >= 0:
    set_state_method = """

    def set_state(self, state):
        valid_states = ["idle", "thinking", "working", "success",
                        "error", "listening", "speaking", "sleepy"]
        if state not in valid_states:
            state = "idle"
        self.state = state
        state_to_expression = {
            "idle": "idle",
            "thinking": "thinking",
            "working": "thinking",
            "success": "excited",
            "error": "error",
            "listening": "happy",
            "speaking": "happy",
            "sleepy": "sleepy",
        }
        expression = state_to_expression.get(state, "idle")
        if state == "speaking":
            self.set_talking(True)
        else:
            self.set_talking(False)
        self.update()"""

    content = content[:activity_idx] + set_state_method + content[activity_idx:]
    print('Added set_state method before ACTIVITY section')
else:
    print('Could not find ACTIVITY section')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')