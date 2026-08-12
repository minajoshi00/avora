"""Test imports and diagnose AI connection issues."""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("="*60)
print("TESTING IMPORTS AND AI CONNECTION")
print("="*60)

# Test 1: Check if .env exists
print("\n[1] Checking .env file...")
env_file = backend_dir / ".env"
print(f"  .env exists: {env_file.exists()}")
if env_file.exists():
    print(f"  Location: {env_file}")
else:
    print(f"  WARNING: .env not found at {env_file}")

# Test 2: Check dotenv
print("\n[2] Checking python-dotenv...")
try:
    from dotenv import load_dotenv
    print("  [OK] python-dotenv is installed")
except ImportError as e:
    print(f"  ✗ python-dotenv NOT installed: {e}")
    sys.exit(1)

# Test 3: Check secure_storage module
print("\n[3] Checking secure_storage module...")
try:
    from secure_storage import get_secure_storage, mask_key, validate_key_format, test_provider_connection
    print("  [OK] secure_storage module imported successfully")
    storage = get_secure_storage()
    print(f"  [OK] Secure storage initialized: {storage}")
except Exception as e:
    print(f"  ✗ Failed to import secure_storage: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check settings module
print("\n[4] Checking settings module...")
try:
    from settings import get_setting, set_setting
    print("  [OK] settings module imported successfully")
except Exception as e:
    print(f"  ✗ Failed to import settings: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check ai_logic module
print("\n[5] Checking ai_logic module...")
try:
    import ai_logic
    print("  [OK] ai_logic module imported successfully")
    print(f"  GEMINI_KEY exists: {bool(ai_logic.GEMINI_KEY)}")
    print(f"  GROQ_KEY exists: {bool(ai_logic.GROQ_KEY)}")
    if ai_logic.GEMINI_KEY:
        print(f"  GEMINI_KEY masked: {ai_logic._mask_key(ai_logic.GEMINI_KEY)}")
    if ai_logic.GROQ_KEY:
        print(f"  GROQ_KEY masked: {ai_logic._mask_key(ai_logic.GROQ_KEY)}")
except Exception as e:
    print(f"  ✗ Failed to import ai_logic: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check Google Generative AI
print("\n[6] Checking Google Generative AI...")
try:
    from google import genai
    print("  [OK] google.generativeai module available")
except ImportError as e:
    print(f"  ✗ google.generativeai NOT installed: {e}")

# Test 7: Check Groq
print("\n[7] Checking Groq...")
try:
    from groq import Groq
    print("  [OK] groq module available")
except ImportError as e:
    print(f"  ✗ groq NOT installed: {e}")

print("\n" + "="*60)
print("DIAGNOSTICS COMPLETE")
print("="*60)