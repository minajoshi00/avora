with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add STATE tracking to setup_state
old_setup_state = """    def setup_state(self):

        # ---------------- EMOTION ----------------"""

new_setup_state = """    def setup_state(self):

        # ---------------- STATE ----------------
        self.state = "idle"  # idle, thinking, working, success, error, listening, speaking, sleepy

        # ---------------- EMOTION ----------------"""

if old_setup_state in content:
    content = content.replace(old_setup_state, new_setup_state)
    print("Added state constant to setup_state")
else:
    print("setup_state pattern not found")

# Add state-to-expression mapping in set_expression
old_set_expression_start = """    def set_expression(
        self,
        expression,
    ):

        if not self.emotions_enabled():

            expression = "idle"

        valid_expressions = [

            "idle",
            "thinking",
            "happy",
            "sad",
            "angry",
            "excited",
            "sleepy",
            "surprised",
            "confused",
            "curious",
            "error",

        ]"""

new_set_expression_start = """    def set_expression(
        self,
        expression,
    ):

        if not self.emotions_enabled():

            expression = "idle"

        # Map AVORA states to character expressions
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

        # If expression is an AVORA state, map it
        if expression in state_to_expression:
            expression = state_to_expression[expression]

        valid_expressions = [

            "idle",
            "thinking",
            "happy",
            "sad",
            "angry",
            "excited",
            "sleepy",
            "surprised",
            "confused",
            "curious",
            "error",

        ]"""

if old_set_expression_start in content:
    content = content.replace(old_set_expression_start, new_set_expression_start)
    print("Added state-to-expression mapping in set_expression")
else:
    print("set_expression pattern not found")

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\character.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")