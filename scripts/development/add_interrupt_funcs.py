with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add interrupt_speaking and resume_listening after STATUS section, before CALLBACK section
# Find the STATUS section and the CALLBACK section
status_idx = content.find('# ========================================================\n# STATUS')
callback_idx = content.find('# ========================================================\n# CALLBACK')

if status_idx >= 0 and callback_idx >= 0:
    # Insert interrupt functions between STATUS and CALLBACK
    interrupt_section = '\n\n# ========================================================\n# VOICE INTERRUPTION\n# ========================================================\n\ndef interrupt_speaking():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    stop_speaking()\n    _is_speaking = False\n\ndef resume_listening():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    _is_speaking = False\n'
    content = content[:status_idx + len('# ========================================================\n# STATUS\n')] + interrupt_section + content[status_idx + len('# ========================================================\n# STATUS'):callback_idx]
    print('Added interrupt_speaking and resume_listening functions')
else:
    print(f'status_idx: {status_idx}, callback_idx: {callback_idx}')
    # Try to find any good insertion point
    # Just append at the end if we can't find the right place
    interrupt_section = '\n\n# ========================================================\n# VOICE INTERRUPTION\n# ========================================================\n\ndef interrupt_speaking():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    stop_speaking()\n    _is_speaking = False\n\ndef resume_listening():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    _is_speaking = False\n'
    if 'def interrupt_speaking' not in content:
        content += interrupt_section
        print('Added interrupt functions at end of file')
    else:
        print('interrupt functions already exist')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')