import sys
import traceback

results = []

# Check dependencies
deps = ['PySide6', 'dotenv', 'google.genai', 'groq', 'requests', 'psutil', 'pyautogui', 'edge_tts', 'win32com.client', 'google.oauth2.credentials', 'google_auth_oauthlib', 'googleapiclient.discovery']
for dep in deps:
    try:
        __import__(dep)
        results.append(f'OK   {dep}')
    except ImportError as e:
        results.append(f'MISS {dep}: {e}')
    except Exception as e:
        results.append(f'ERR  {dep}: {type(e).__name__}: {e}')

# Check project modules
modules = ['settings', 'app_utils', 'memory', 'voice', 'character', 'ai_logic', 'main']
for mod in modules:
    try:
        __import__(mod)
        results.append(f'OK   {mod}')
    except Exception as e:
        results.append(f'FAIL {mod}: {type(e).__name__}: {e}')

# Check skills
skills = ['skills.email', 'skills.files', 'skills.image', 'skills.power', 'skills.system', 'skills.weather', 'skills.reminders', 'skills.study', 'skills.windows_settings']
for mod in skills:
    try:
        __import__(mod)
        results.append(f'OK   {mod}')
    except Exception as e:
        results.append(f'FAIL {mod}: {type(e).__name__}: {e}')

# Check specific functions
checks = [
    ('skills.email', 'search_emails'),
    ('skills.system', 'get_full_system_status'),
    ('skills.files', 'get_file_info'),
    ('skills.files', 'move_file'),
    ('skills.files', 'rename_file'),
    ('skills.email', 'send_email'),
    ('skills.email', 'reply_to_email'),
    ('skills.email', 'delete_email'),
    ('skills.email', 'archive_email'),
    ('skills.email', 'create_draft'),
    ('skills.email', 'get_email'),
    ('skills.email', 'star_email'),
    ('skills.email', 'mark_email_read'),
]
for mod_name, func_name in checks:
    try:
        mod = __import__(mod_name, fromlist=[func_name])
        if hasattr(mod, func_name):
            results.append(f'OK   {mod_name}.{func_name}')
        else:
            results.append(f'MISS {mod_name}.{func_name}')
    except Exception as e:
        results.append(f'FAIL {mod_name}.{func_name}: {type(e).__name__}: {e}')

with open('import_check_results.txt', 'w') as f:
    f.write('\n'.join(results))

print('\n'.join(results))
