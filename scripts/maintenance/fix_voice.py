with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: remove the incorrectly nested functions and add them at the proper module level
# Find the is_speaking function and fix it
# The is_speaking function should just be: def is_speaking(): return _is_speaking

# Let me find and fix the is_speaking function
# It currently starts at 'def is_speaking():'
idx = content.find('def is_speaking():')
if idx >= 0:
    # Find the return statement
    return_idx = content.find('return _is_speaking', idx)
    if return_idx >= 0:
        # Find the end of the function (next def or end of file)
        next_def = content.find('\n\ndef ', return_idx)
        if next_def >= 0:
            # Get the content between return and next function
            between = content[return_idx:next_def]
            # Check if it's just the return line and some blank lines
            lines = between.split('\n')
            # Keep only the return and blank lines, remove resume_listening
            fixed_lines = []
            for line in lines:
                if 'resume_listening' not in line and 'global _is_speaking, _user_speaking' not in line:
                    fixed_lines.append(line)
            fixed_between = '\n'.join(fixed_lines)
            content = content[:return_idx] + fixed_between + content[next_def:]
            print('Fixed is_speaking function')
        else:
            print('Could not find next function definition')
    else:
        print('Could not find return statement')
else:
    print('is_speaking function not found')

# Now add interrupt_speaking and resume_listening at the module level (at the end, before any trailing content)
# Find a good spot - after the STATUS section or at the end
# Let me look for a good insertion point

# Try to find the CALLBACK section or similar
callback_idx = content.find('# ========================================================\n# CALLBACK')
if callback_idx >= 0:
    # Insert interrupt functions before the CALLBACK section
    interrupt_section = '\n\n# ========================================================\n# VOICE INTERRUPTION\n# ========================================================\n\ndef interrupt_speaking():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    stop_speaking()\n    _is_speaking = False\n\ndef resume_listening():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    _is_speaking = False\n'
    content = content[:callback_idx] + interrupt_section + content[callback_idx:]
    print('Added interrupt section before CALLBACK')
else:
    # Just append at the very end of the file
    interrupt_section = '\n\n# ========================================================\n# VOICE INTERRUPTION\n# ========================================================\n\ndef interrupt_speaking():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    stop_speaking()\n    _is_speaking = False\n\ndef resume_listening():\n    global _is_speaking, _user_speaking\n    _user_speaking = False\n    _is_speaking = False\n'
    # Make sure we don't add duplicate _is_speaking references if already there
    if '_is_speaking' in content:
        # The globals are already declared, just add the functions
        if 'def interrupt_speaking' not in content:
            content += interrupt_section
            print('Added interrupt section at end of file')
        else:
            print('interrupt section already exists')
    else:
        print('_is_speaking not in content')

with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\voice.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')