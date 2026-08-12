"""
============================================================
                SECURE API KEY STORAGE
============================================================

This module provides encrypted storage for API keys as a fallback
when .env is not available. Keys are stored in the user's app data
directory with basic encryption.

Security features:
- Keys are never stored in plain text
- Only masked versions are displayed in logs/UI
- Automatic fallback from .env to encrypted storage
- Per-provider validation on startup
"""

from __future__ import annotations

import os
import sys
import json
import base64
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

from app_paths import APP_DATA_DIR

# Try to use cryptography library for encryption
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    # Fallback to base64 encoding (obfuscation, not true encryption)
    import secrets

# =============================================================
# CONSTANTS
# =============================================================

STORAGE_FILE = APP_DATA_DIR / "api_keys.enc"
KEY_HASH_FILE = APP_DATA_DIR / "api_keys.hash"
MAX_KEY_LENGTH = 200  # Sanity check for key lengths

# =============================================================
# ENCRYPTION HELPERS
# =============================================================

def _get_or_create_key() -> bytes:
    """
    Get or create an encryption key.
    In production, this should use a proper key management system.
    For now, we derive a key from machine-specific data.
    """
    if HAS_CRYPTO:
        # Use a combination of machine ID and app-specific salt
        # This is not perfectly secure but better than plaintext
        salt = b"avora_app_2024"  # App-specific salt
        
        # Try to get machine-specific identifier
        machine_id = _get_machine_id()
        
        # Derive a 32-byte key using PBKDF2
        key_material = (machine_id + salt).encode('utf-8')
        key = hashlib.pbkdf2_hmac('sha256', key_material, salt, 100000)
        
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        return base64.urlsafe_b64encode(key)
    else:
        # Fallback: use a simple obfuscation key
        return base64.urlsafe_b64encode(b"avora_obfuscation_key_2024!"[:32])

def _get_machine_id() -> str:
    """
    Get a machine-specific identifier.
    Falls back to a constant if unable to determine.
    """
    try:
        if sys.platform == "win32":
            # Windows: use registry or WMI
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography",
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                )
                machine_id, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                return machine_id
            except Exception:
                pass
            
            # Fallback: use environment variables
            return (
                os.environ.get("COMPUTERNAME", "unknown") +
                os.environ.get("USERNAME", "unknown")
            )
        
        elif sys.platform == "darwin":
            # macOS: use IOPlatformUUID
            try:
                import subprocess
                result = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        return line.split('=')[1].strip().strip('"')
            except Exception:
                pass
            return "macos_unknown"
        
        else:
            # Linux: use /etc/machine-id or /var/lib/dbus/machine-id
            machine_id_paths = [
                Path("/etc/machine-id"),
                Path("/var/lib/dbus/machine-id"),
            ]
            for path in machine_id_paths:
                if path.exists():
                    try:
                        return path.read_text().strip()
                    except Exception:
                        pass
            return "linux_unknown"
    
    except Exception:
        return "unknown_machine"

def _encrypt_value(value: str) -> str:
    """Encrypt a string value."""
    if not value:
        return ""
    
    key = _get_or_create_key()
    
    if HAS_CRYPTO:
        fernet = Fernet(key)
        encrypted = fernet.encrypt(value.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    else:
        # Fallback: simple obfuscation (NOT secure, but better than plaintext)
        # XOR with key-derived bytes
        key_bytes = hashlib.sha256(key).digest()
        value_bytes = value.encode('utf-8')
        obfuscated = bytes([
            value_bytes[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(value_bytes))
        ])
        return base64.urlsafe_b64encode(obfuscated).decode('utf-8')

def _decrypt_value(encrypted_value: str) -> str:
    """Decrypt a string value."""
    if not encrypted_value:
        return ""
    
    key = _get_or_create_key()
    
    try:
        if HAS_CRYPTO:
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        else:
            # Fallback: reverse obfuscation
            key_bytes = hashlib.sha256(key).digest()
            obfuscated = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted = bytes([
                obfuscated[i] ^ key_bytes[i % len(key_bytes)]
                for i in range(len(obfuscated))
            ])
            return decrypted.decode('utf-8')
    except Exception:
        return ""

# =============================================================
# SECURE STORAGE CLASS
# =============================================================

class SecureAPIKeyStorage:
    """
    Secure storage for API keys with encryption at rest.
    """
    
    def __init__(self):
        self.storage_file = STORAGE_FILE
        self.hash_file = KEY_HASH_FILE
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the storage directory exists."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[SecureStorage] Could not create directory: {e}")
    
    def save_keys(self, keys: Dict[str, str]) -> bool:
        """
        Save API keys with encryption.
        
        Args:
            keys: Dictionary of provider_name -> api_key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt each key
            encrypted_keys = {}
            for provider, key in keys.items():
                if key:
                    encrypted_keys[provider] = _encrypt_value(key.strip())
            
            # Save to file
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_keys, f, indent=2)
            
            # Save hash for integrity verification
            self._save_hash()
            
            return True
        
        except Exception as e:
            print(f"[SecureStorage] Failed to save keys: {e}")
            return False
    
    def load_keys(self) -> Dict[str, str]:
        """
        Load and decrypt API keys.
        
        Returns:
            Dictionary of provider_name -> api_key
        """
        try:
            # Verify integrity first
            if not self._verify_hash():
                print("[SecureStorage] Warning: Storage file integrity check failed")
            
            if not self.storage_file.exists():
                return {}
            
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                encrypted_keys = json.load(f)
            
            # Decrypt each key
            decrypted_keys = {}
            for provider, encrypted_key in encrypted_keys.items():
                decrypted_key = _decrypt_value(encrypted_key)
                if decrypted_key:
                    decrypted_keys[provider] = decrypted_key
            
            return decrypted_keys
        
        except Exception as e:
            print(f"[SecureStorage] Failed to load keys: {e}")
            return {}
    
    def get_key(self, provider: str) -> Optional[str]:
        """
        Get a single API key.
        
        Args:
            provider: Provider name (e.g., 'gemini', 'groq', 'openai')
        
        Returns:
            Decrypted API key or None
        """
        keys = self.load_keys()
        return keys.get(provider)
    
    def set_key(self, provider: str, key: str) -> bool:
        """
        Set a single API key.
        
        Args:
            provider: Provider name
            key: API key value
        
        Returns:
            True if successful
        """
        keys = self.load_keys()
        keys[provider] = key
        return self.save_keys(keys)
    
    def delete_key(self, provider: str) -> bool:
        """Delete a specific API key."""
        keys = self.load_keys()
        if provider in keys:
            del keys[provider]
            return self.save_keys(keys)
        return True
    
    def clear_all_keys(self) -> bool:
        """Delete all stored API keys."""
        try:
            if self.storage_file.exists():
                self.storage_file.unlink()
            if self.hash_file.exists():
                self.hash_file.unlink()
            return True
        except Exception as e:
            print(f"[SecureStorage] Failed to clear keys: {e}")
            return False
    
    def has_keys(self) -> bool:
        """Check if any keys are stored."""
        try:
            return self.storage_file.exists() and self.storage_file.stat().st_size > 0
        except Exception:
            return False
    
    def _save_hash(self):
        """Save hash of encrypted file for integrity verification."""
        try:
            if not self.storage_file.exists():
                return
            
            content = self.storage_file.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            
            with open(self.hash_file, 'w', encoding='utf-8') as f:
                json.dump({"hash": file_hash}, f)
        
        except Exception as e:
            print(f"[SecureStorage] Failed to save hash: {e}")
    
    def _verify_hash(self) -> bool:
        """Verify integrity of encrypted file."""
        try:
            if not self.storage_file.exists() or not self.hash_file.exists():
                return True  # No file to verify
            
            # Read current hash
            with open(self.hash_file, 'r', encoding='utf-8') as f:
                hash_data = json.load(f)
            stored_hash = hash_data.get("hash")
            
            # Calculate current hash
            content = self.storage_file.read_bytes()
            current_hash = hashlib.sha256(content).hexdigest()
            
            return stored_hash == current_hash
        
        except Exception:
            return False


# =============================================================
# SINGLETON INSTANCE
# =============================================================

_storage = None

def get_secure_storage() -> SecureAPIKeyStorage:
    """Get the singleton secure storage instance."""
    global _storage
    if _storage is None:
        _storage = SecureAPIKeyStorage()
    return _storage


# =============================================================
# HELPER FUNCTIONS
# =============================================================

def mask_key(key: str) -> str:
    """
    Mask an API key for safe display.
    Shows first 6 and last 4 characters only.
    """
    if not key:
        return "***MISSING***"
    
    key = key.strip()
    
    if len(key) < 10:
        return key[:6] + "****"
    
    return key[:6] + "..." + key[-4:]


def validate_key_format(provider: str, key: str) -> tuple[bool, str]:
    """
    Validate API key format.
    
    Args:
        provider: Provider name ('gemini', 'groq', 'openai')
        key: API key to validate
    
    Returns:
        (is_valid, message)
    """
    if not key or not key.strip():
        return False, "API key is empty"
    
    key = key.strip()
    
    # Length check
    if len(key) < 20:
        return False, f"API key too short ({len(key)} chars, expected >= 20)"
    
    if len(key) > MAX_KEY_LENGTH:
        return False, f"API key too long ({len(key)} chars, expected <= {MAX_KEY_LENGTH})"
    
    # Provider-specific validation
    if provider == "gemini":
        if not (key.startswith("AI") or key.startswith("AQ")):
            return False, "Gemini API key should start with 'AI' or 'AQ'"
        if len(key) < 39:
            return False, f"Gemini API key length suspicious ({len(key)} chars, expected ~39)"
    
    elif provider == "groq":
        if not key.startswith("gsk_"):
            return False, "Groq API key should start with 'gsk_'"
        if len(key) < 50:
            return False, f"Groq API key length suspicious ({len(key)} chars, expected ~56)"
    
    elif provider == "openai":
        if not key.startswith("sk-"):
            return False, "OpenAI API key should start with 'sk-'"
        if len(key) < 50:
            return False, f"OpenAI API key length suspicious ({len(key)} chars, expected ~51)"
    
    return True, "Format looks valid"


def test_provider_connection(provider: str, api_key: str) -> tuple[bool, str]:
    """
    Test connection to an AI provider.
    
    Args:
        provider: Provider name ('gemini', 'groq', 'openai')
        api_key: API key to test
    
    Returns:
        (success, message)
    """
    if not api_key:
        return False, "No API key provided"
    
    try:
        if provider == "gemini":
            return _test_gemini(api_key)
        elif provider == "groq":
            return _test_groq(api_key)
        elif provider == "openai":
            return _test_openai(api_key)
        else:
            return False, f"Unknown provider: {provider}"
    
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"


def _test_gemini(api_key: str) -> tuple[bool, str]:
    """Test Gemini API connection."""
    try:
        from google import genai
        
        client = genai.Client(api_key=api_key)
        
        # Try a simple request with minimal tokens
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hi",
            config={"max_output_tokens": 5},
            request_options={"timeout": 10},
        )
        
        if response.text:
            return True, "Connection successful!"
        else:
            return False, "No response from API"
    
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg or "401" in error_msg:
            return False, "Authentication failed - invalid API key"
        elif "quota" in error_msg or "rate limit" in error_msg:
            return False, "Quota/rate limit exceeded"
        elif "timeout" in error_msg:
            return False, "Connection timeout"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check internet connection"
        else:
            return False, f"Error: {str(e)}"


def _test_groq(api_key: str) -> tuple[bool, str]:
    """Test Groq API connection."""
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key)
        
        # Try a simple request
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            timeout=10,
        )
        
        if response.choices[0].message.content:
            return True, "Connection successful!"
        else:
            return False, "No response from API"
    
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg or "401" in error_msg:
            return False, "Authentication failed - invalid API key"
        elif "quota" in error_msg or "rate limit" in error_msg:
            return False, "Quota/rate limit exceeded"
        elif "timeout" in error_msg:
            return False, "Connection timeout"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check internet connection"
        else:
            return False, f"Error: {str(e)}"


def _test_openai(api_key: str) -> tuple[bool, str]:
    """Test OpenAI API connection."""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        # Try a simple request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            timeout=10,
        )
        
        if response.choices[0].message.content:
            return True, "Connection successful!"
        else:
            return False, "No response from API"
    
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg or "401" in error_msg:
            return False, "Authentication failed - invalid API key"
        elif "quota" in error_msg or "rate limit" in error_msg:
            return False, "Quota/rate limit exceeded"
        elif "timeout" in error_msg:
            return False, "Connection timeout"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check internet connection"
        else:
            return False, f"Error: {str(e)}"