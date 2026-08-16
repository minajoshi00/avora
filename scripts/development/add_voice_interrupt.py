with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add USER_SPEAKING global state after _is_speaking
old_globals = """_is_speaking = False"""

new_globals = """_is_speaking = False

_user_speaking = False

# Voice interruption settings
_voice_interruption_enabled = True"""

if old_globals in content:
    content = content.replace(old_globals, new_globals)
    print("Added voice interruption global state")
else:
    print("Global state pattern not found")

# Add the _monitor_user_speaking function after is_speaking function
old_is_speaking_end = """def is_speaking(self=None) -> bool:
    global _is_speaking

    return _is_speaking"""


new_is_speaking_end = """def is_speaking(self=None) -> bool:
    global _is_speaking

    return _is_speaking"""


# Actually, let me find the exact is_speaking function and add after it
# Let me search for the is_speaking function definition
functions_start = content.find('def is_speaking(')
if functions_start >= 0:
    # Find the end of this function
    func_end = content.find('\\n\\n', functions_start)
    if func_end >= 0:
        func_body = content[functions_start:func_end]
        # Add _monitor_user_speaking after is_speaking
        new_func_body = func_body + \"\"\"\n\n\
def _monitor_user_speaking():\n    \"\"\"\n    Monitor microphone input to detect when user starts speaking.\n    Runs in a background thread during TTS playback.\n    \"\"\"\n    global _is_speaking, _user_speaking, _voice_interruption_enabled\n    \n    try:\n        import sounddevice as sd\n        \n        # Check if sounddevice is available\n        if not sd:\n            return\n        \n        # Set up audio stream for input monitoring\n        try:\n            device_info = sd.query_devices(\n                sd.default.device[0],\n                kind='input'\n            )\n            samplerate = int(device_info.get('default_samplerate', 16000))\n            channels = min(2, max(1, device_info.get('max_channels', 1)))\n            \n            def callback(indata, frames, time, status):\n                global _user_speaking\n                # Calculate audio volume (RMS)\n                volume_norm = np.linalg.norm(indata) * 10\n                \n                # If volume exceeds threshold and AVORA is speaking,\n                # detect user as speaking\n                if volume_norm > 0.5 and _is_speaking:\n                    _user_speaking = True\n                elif _is_speaking:\n                    _user_speaking = False\n            \n            with sd.InputStream(\n                samplerate=samplerate,\n                blocksize=1024,\n                channels=channels,\n                callback=callback\n            ) as stream:\n                # Keep the stream open while _is_speaking is True\n                while _is_speaking and not _user_speaking:\n                    time.sleep(0.1)\n                \n                if _user_speaking:\n                    stop_speaking()\n                    _user_speaking = False\n                    global _is_speaking\n                    _is_speaking = False\n        except Exception as e:\n            print(\"Voice monitoring error:\", e)\n    except ImportError:\n        # sounddevice not available - use simpler check\n        pass\n\n\"""\"\"\"\n\n        # Write the modified function body\n        content = content[:functions_start] + new_func_body + content[func_end + 1:]\n        print("Added _monitor_user_speaking function")
else:
    print("is_speaking function not found")

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(\"Done\")
"