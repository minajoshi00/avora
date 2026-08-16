with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add USER_SPEAKING global state after _is_speaking
old_globals = """_is_speaking = False"""

new_globals = """_is_speaking = False

_user_speaking = False"""

if old_globals in content:
    content = content.replace(old_globals, new_globals)
    print("Added _user_speaking global state")
else:
    print("Global state pattern not found")

# Add _monitor_user_speaking function after is_speaking
# Find the is_speaking function
old_is_speaking = """def is_speaking(self=None) -> bool:
    global _is_speaking

    return _is_speaking"""


# Let me find it properly
import re
# Search for the function definition
match = re.search(r'def is_speaking\\(self=None\\) -> bool:.*?return _is_speaking', content, re.DOTALL)
if match:
    print("Found is_speaking function")
    # Add monitoring function after it
    new_monitor = \"\"\"\\n\\n\\ndef _monitor_user_speaking():\n    \"\"\"\n    Monitor microphone input to detect when user starts speaking.\n    Runs in a background thread during TTS playback.\n    \"\"\"\n    global _is_speaking, _user_speaking\n    \n    try:\n        import sounddevice as sd\n        \n        # Set up audio stream for input monitoring\n        try:\n            device_info = sd.query_devices(\n                sd.default.device[0],\n                kind='input'\n            )\n            samplerate = int(device_info.get('default_samplerate', 16000))\n            channels = min(2, max(1, device_info.get('max_channels', 1)))\n            \n            def callback(indata, frames, time, status):\n                global _user_speaking\n                # Calculate audio volume (RMS)\n                volume_norm = np.linalg.norm(indata) * 10\n                \n                # If volume exceeds threshold and AVORA is speaking,\n                # detect user as speaking\n                if volume_norm > 0.5 and _is_speaking:\n                    _user_speaking = True\n                elif _is_speaking:\n                    _user_speaking = False\n            \n            with sd.InputStream(\n                samplerate=samplerate,\n                blocksize=1024,\n                channels=channels,\n                callback=callback\n            ) as stream:\n                # Keep the stream open while _is_speaking is True\n                while _is_speaking and not _user_speaking:\n                    time.sleep(0.1)\n                \n                if _user_speaking:\n                    stop_speaking()\n                    _user_speaking = False\n                    _is_speaking = False\n        except Exception as e:\n            print(\"Voice monitoring error:\", e)\n    except ImportError:\n        pass\n\n\"""\"\"\"\n\n    # Insert after the is_speaking function\n    end_of_func = match.end()\n    # Find the next double newline or end\n    remaining = content[end_of_func:]\n    next_func = re.search(r'def ', remaining)\n    if next_func:\n        insert_pos = end_of_func + next_func.start()\n    else:\n        insert_pos = len(content)\n    \n    content = content[:insert_pos] + new_monitor + content[insert_pos:]\n    print("Added _monitor_user_speaking function")\nelse:
    print("is_speaking function not found with regex")

# Also add the voice_interruption setting check in the speak function
# Find the speak function and add interruption check
old_speak_start = \"\"\"def speak(\n    text,\n    on_start=None,\n    on_finish=None\"\"\"

new_speak_start = \"\"\"def speak(\n    text,\n    on_start=None,\n    on_finish=None\n):\n    global _user_speaking\n    _user_speaking = False\"\"\"

if old_speak_start in content:
    content = content.replace(old_speak_start, new_speak_start)
    print("Added _user_speaking reset in speak function")
else:
    print("speak function pattern not found")

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(\"Done\")