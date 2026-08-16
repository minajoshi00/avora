#!/usr/bin/env python3
import sys

filepath = r"C:\Users\minaj\OneDrive\Desktop\avora\avora_desktop\main.py"
with open(filepath, "rb") as f:
    content = f.read()

# Replace the broken emoji section with proper emoji bytes
# Using direct byte values for emojis
new_emoji_block = (
    b'emojis = {\r\n'
    b'            TaskState.IDLE: "\xf0\x9f\xa4\x96",\r\n'
    b'            TaskState.LISTENING: "\xf0\x9f\x8e\xa7",\r\n'
    b'            TaskState.THINKING: "\xf0\x9f\xa7\xa0",\r\n'
    b'            TaskState.WORKING: "\xf0\x9f\x9a\x80",\r\n'
    b'            TaskState.WAITING_PERMISSION: "\xf0\x9f\x94\xa8",\r\n'
    b'            TaskState.SUCCESS: "\xf0\x9f\x8c\x95",\r\n'
    b'            TaskState.ERROR: "\xf0\x9f\x9c\xa8",\r\n'
    b'            TaskState.CANCELLED: "\xf0\x9f\x96\x09",\r\n'
    b'        }'
)

# The old broken block - find and replace
old_emoji_start = b'emojis = {'
old_emoji_end = b'\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbd\xf0\x9f\xa4\x96",\r\n            TaskState.LISTENING'

if old_emoji_start in content and old_emoji_end in content:
    # Find the full old block
    start_idx = content.find(old_emoji_start)
    end_idx = content.find(b'\xf0\x9f\xa4\x96",\r\n            TaskState.LISTENING')
    if end_idx < 0:
        # Try alternative approach - find the whole block
        # Just replace from 'emojis = {' to the end of the emoji dict
        replacement_marker = b'        }'
        marker_idx = content.find(replacement_marker)
        if marker_idx >= 0:
            # Find the 'emojis' line
            emoji_line_start = content.rfind(b'emojis = {', 0, marker_idx)
            if emoji_line_start >= 0:
                content = content[:emoji_line_start] + new_emoji_block + content[marker_idx+len(replacement_marker):]
                print("Emojis replaced using marker approach")
            else:
                print("Could not find emoji line start")
        else:
            print("Could not find end marker")
    else:
        # Replace the section between old_emoji_start and old_emoji_end
        new_section = new_emoji_block[:new_emoji_block.index(b'\xf0\x9f\x9c\xa8"')+len(b'\xf0\x9f\x9c\xa8"')] 
        # This is getting complicated, let me just do a simple string replace
        pass
    
    # Simpler approach: just replace the whole block from 'emojis = {' to the closing '}'
    # Find where emojis starts and where the closing } is
    start_marker = b'emojis = {'
    end_marker = b'        }'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx >= 0 and end_idx >= 0:
        # Make sure we have the right end marker (the one for emojis, not another one)
        # Let's just replace from emojis = { to the end of the file if needed
        # Actually, let's find the correct end by looking for the specific pattern
        section_to_replace = content[start_idx:end_idx + len(end_marker)]
        if section_to_replace == content[start_idx:end_idx + len(end_marker)]:
            content = content[:start_idx] + new_emoji_block + content[end_idx + len(end_marker):]
            with open(filepath, "wb") as f:
                f.write(content)
            print("Emojis replaced successfully")
        else:
            print("Section mismatch, trying different approach")
    else:
        print(f"start_idx={start_idx}, end_idx={end_idx}")
else:
    print("Could not find old emoji block markers")
    # Let's just print what we have around emojis
    idx = content.find(b'emojis')
    if idx >= 0:
        print(f"Found 'emojis' at index {idx}")
        print(repr(content[idx:idx+200]))