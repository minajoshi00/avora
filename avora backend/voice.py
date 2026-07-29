import asyncio
import ctypes
import os
import tempfile
import threading
import time
from pathlib import Path

# ============================================================
# OPTIONAL IMPORTS
# ============================================================

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    import win32com.client
    import win32com
except ImportError:
    win32com = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

# ============================================================
# SETTINGS
# ============================================================

try:
    from settings import get_setting, is_voice_enabled
except Exception:
    def get_setting(key, default=None):
        return default

    def is_voice_enabled():
        return True

# ============================================================
# AI FRIEND — ADVANCED VOICE ENGINE
# ============================================================

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_PITCH = "+0Hz"

_audio_lock = threading.RLock()
_stop_event = threading.Event()

_current_audio_file = None
_current_thread = None
_is_speaking = False
_sapi_voice = None


# ============================================================
# SAPI VOICE
# ============================================================

def _get_sapi_voice():
    global _sapi_voice

    if _sapi_voice is None and win32com is not None:
        try:
            _sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as error:
            print("[SAPI INIT ERROR]", error)
            _sapi_voice = None

    return _sapi_voice


# ============================================================
# SETTINGS HELPERS
# ============================================================

def _get_voice_name():
    return get_setting(
        "voice.voice_name",
        DEFAULT_VOICE
    ) or DEFAULT_VOICE


def _get_volume():
    try:
        value = float(
            get_setting(
                "voice.volume",
                1.0
            )
        )

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    except Exception:
        return 1.0


def _get_speed():
    try:
        value = float(
            get_setting(
                "voice.speed",
                1.0
            )
        )

        return max(
            0.5,
            min(
                2.0,
                value
            )
        )

    except Exception:
        return 1.0


def _speed_to_edge_rate(speed):
    percentage = int(
        (speed - 1.0) * 100
    )

    if percentage >= 0:
        return f"+{percentage}%"

    return f"{percentage}%"


def _volume_to_edge_volume(volume):
    percentage = int(
        (volume - 1.0) * 100
    )

    if percentage >= 0:
        return f"+{percentage}%"

    return f"{percentage}%"


# ============================================================
# FILE MANAGEMENT
# ============================================================

def _create_audio_path():
    file = tempfile.NamedTemporaryFile(
        prefix="ai_friend_voice_",
        suffix=".mp3",
        delete=False
    )

    file.close()

    return Path(file.name)


def _delete_audio_file(path):
    if not path:
        return

    try:
        path = Path(path)

        if path.exists():
            for _ in range(5):

                try:
                    path.unlink()
                    break

                except OSError:
                    time.sleep(0.1)

    except Exception as error:
        print("[VOICE CLEANUP ERROR]", error)


# ============================================================
# WINDOWS MCI AUDIO PLAYER
# ============================================================

def _play_audio_mci(file_path):

    if os.name != "nt":
        return False

    try:

        winmm = ctypes.windll.winmm

        alias = "AIFriendVoice"

        path_str = str(
            file_path
        ).replace(
            '"',
            '\\"'
        )

        # Close old audio
        winmm.mciSendStringW(
            f"stop {alias}",
            None,
            0,
            0
        )

        winmm.mciSendStringW(
            f"close {alias}",
            None,
            0,
            0
        )

        # Open MP3
        open_result = winmm.mciSendStringW(
            f'open "{path_str}" type mpegvideo alias {alias}',
            None,
            0,
            0
        )

        if open_result != 0:
            print("[VOICE] Could not open audio file.")
            return False

        # Get duration
        buffer = ctypes.create_unicode_buffer(128)

        winmm.mciSendStringW(
            f"status {alias} length",
            buffer,
            128,
            0
        )

        try:
            duration_ms = int(
                buffer.value
            )

        except Exception:
            duration_ms = 0

        # Play
        play_result = winmm.mciSendStringW(
            f"play {alias}",
            None,
            0,
            0
        )

        if play_result != 0:

            winmm.mciSendStringW(
                f"close {alias}",
                None,
                0,
                0
            )

            return False

        start_time = time.time()

        while not _stop_event.is_set():

            if duration_ms > 0:

                elapsed = (
                    time.time() -
                    start_time
                ) * 1000

                if elapsed >= duration_ms + 300:
                    break

            else:

                status_buffer = ctypes.create_unicode_buffer(128)

                winmm.mciSendStringW(
                    f"status {alias} mode",
                    status_buffer,
                    128,
                    0
                )

                if status_buffer.value not in (
                    "playing",
                    "paused"
                ):
                    break

            time.sleep(0.05)

        # Stop and close
        winmm.mciSendStringW(
            f"stop {alias}",
            None,
            0,
            0
        )

        winmm.mciSendStringW(
            f"close {alias}",
            None,
            0,
            0
        )

        return True

    except Exception as error:

        print(
            "[MCI AUDIO ERROR]",
            error
        )

        return False


# ============================================================
# OFFLINE SAPI5 SPEECH
# ============================================================

def _speak_sapi5(text):

    sapi = _get_sapi_voice()

    if sapi is None:
        print(
            "[VOICE] SAPI5 is not available."
        )

        return False

    try:

        sapi.Volume = int(
            _get_volume() * 100
        )

        sapi.Rate = int(
            (_get_speed() - 1.0) * 10
        )

        # Async speech
        sapi.Speak(
            str(text),
            1
        )

        while True:

            if _stop_event.is_set():

                try:
                    sapi.Speak(
                        "",
                        2
                    )

                except Exception:
                    pass

                break

            try:

                if sapi.Status.RunningState != 2:
                    break

            except Exception:
                break

            time.sleep(0.05)

        return True

    except Exception as error:

        print(
            "[SAPI5 ERROR]",
            error
        )

        return False


# ============================================================
# EDGE TTS GENERATION
# ============================================================

async def generate_voice(
    text,
    output_file
):

    if not text:
        return False

    if not str(text).strip():
        return False

    if edge_tts is None:

        print(
            "[VOICE] edge-tts is not installed."
        )

        return False

    try:

        communicate = edge_tts.Communicate(

            text=str(text),

            voice=_get_voice_name(),

            rate=_speed_to_edge_rate(
                _get_speed()
            ),

            volume=_volume_to_edge_volume(
                _get_volume()
            ),

            pitch=DEFAULT_PITCH
        )

        await communicate.save(
            str(output_file)
        )

        return True

    except Exception as error:

        print(
            "[EDGE-TTS ERROR]",
            error
        )

        return False


# ============================================================
# STOP SPEAKING
# ============================================================

def stop_speaking():

    global _current_audio_file
    global _is_speaking

    _stop_event.set()

    # Stop MCI
    try:

        if os.name == "nt":

            winmm = ctypes.windll.winmm

            winmm.mciSendStringW(
                "stop AIFriendVoice",
                None,
                0,
                0
            )

            winmm.mciSendStringW(
                "close AIFriendVoice",
                None,
                0,
                0
            )

    except Exception:
        pass

    # Stop SAPI
    try:

        sapi = _get_sapi_voice()

        if sapi:

            sapi.Speak(
                "",
                2
            )

    except Exception:
        pass

    # Delete current file
    with _audio_lock:

        audio_file = _current_audio_file

        _current_audio_file = None

    if audio_file:

        _delete_audio_file(
            audio_file
        )

    _is_speaking = False


# ============================================================
# STATUS
# ============================================================

def is_speaking():

    return _is_speaking


# ============================================================
# CALLBACK
# ============================================================

def safe_invoke_callback(callback):

    if not callback:
        return

    if not callable(callback):
        return

    try:

        callback()

    except Exception as error:

        print(
            "[VOICE CALLBACK ERROR]",
            error
        )


# ============================================================
# MAIN SPEAK FUNCTION
# ============================================================

def speak(
    text,
    on_start=None,
    on_finish=None
):

    global _current_thread
    global _current_audio_file
    global _is_speaking

    if not text:
        return

    if not str(text).strip():
        return

    # Voice disabled
    if not is_voice_enabled():
        return

    # Stop previous voice
    if get_setting(
        "voice.auto_stop_previous",
        True
    ):

        stop_speaking()

    _stop_event.clear()

    def run():

        global _current_audio_file
        global _is_speaking

        audio_file = None

        try:

            _is_speaking = True

            # Create temporary file
            audio_file = _create_audio_path()

            with _audio_lock:

                _current_audio_file = audio_file

            success = False

            # Try Edge TTS
            if edge_tts is not None:

                try:

                    success = asyncio.run(
                        generate_voice(
                            text,
                            audio_file
                        )
                    )

                except Exception as error:

                    print(
                        "[VOICE ASYNC ERROR]",
                        error
                    )

                    success = False

            # Stop requested
            if _stop_event.is_set():
                return

            # Play Edge TTS
            if (

                success

                and audio_file.exists()

                and audio_file.stat().st_size > 0

            ):

                safe_invoke_callback(
                    on_start
                )

                played = _play_audio_mci(
                    audio_file
                )

                # Fallback to SAPI
                if not played:

                    _speak_sapi5(
                        text
                    )

            else:

                # Direct SAPI fallback
                safe_invoke_callback(
                    on_start
                )

                _speak_sapi5(
                    text
                )

        except Exception as error:

            print(
                "[VOICE ERROR]",
                error
            )

        finally:

            safe_invoke_callback(
                on_finish
            )

            _delete_audio_file(
                audio_file
            )

            with _audio_lock:

                if (
                    _current_audio_file
                    == audio_file
                ):

                    _current_audio_file = None

            _is_speaking = False

    _current_thread = threading.Thread(

        target=run,

        daemon=True,

        name="AIFriendVoice"

    )

    _current_thread.start()


# ============================================================
# TEST VOICE
# ============================================================

def test_voice():

    text = get_setting(

        "voice.test_voice_text",

        "Hey brooo, this is a test of my AI Friend voice."

    )

    speak(text)


# ============================================================
# CHANGE VOICE
# ============================================================

def set_voice(voice_name):

    from settings import set_setting

    if not voice_name:
        return False

    return set_setting(
        "voice.voice_name",
        voice_name
    )


# ============================================================
# AVAILABLE VOICES
# ============================================================

AVAILABLE_VOICES = {

    "Aria":
        "en-US-AriaNeural",

    "Jenny":
        "en-US-JennyNeural",

    "Guy":
        "en-US-GuyNeural",

    "Christopher":
        "en-US-ChristopherNeural",

    "Sonia":
        "en-GB-SoniaNeural",

    "Ryan":
        "en-GB-RyanNeural",

    "Neerja":
        "en-IN-NeerjaNeural",

    "Prabhat":
        "en-IN-PrabhatNeural",

}


# ============================================================
# CONTINUOUS MICROPHONE RECORDING (ChatGPT-Style)
# ============================================================

_continuous_audio_buffer: list = []
_continuous_stream = None
_continuous_recording = False
_continuous_sample_rate = 16000


def _audio_callback(
    indata,
    frames,
    time_info,
    status,
):
    """Callback for sounddevice InputStream - accumulates audio data."""
    if status:
        print("[VOICE] Stream status:", status)
    _continuous_audio_buffer.append(indata.copy())


def listen_start():
    """
    Start continuous microphone recording using sounddevice InputStream.
    Records until listen_stop() is called.
    Does NOT require PyAudio.
    """
    global _continuous_audio_buffer
    global _continuous_stream
    global _continuous_recording

    if sd is None:
        print("[VOICE] sounddevice is not installed.")
        return False

    if _continuous_recording:
        print("[VOICE] Already recording.")
        return False

    try:
        _continuous_audio_buffer = []
        _continuous_recording = True

        _continuous_stream = sd.InputStream(
            samplerate=_continuous_sample_rate,
            channels=1,
            dtype="int16",
            callback=_audio_callback,
        )

        _continuous_stream.start()
        print("[VOICE] Continuous recording started.")
        return True

    except Exception as error:
        print("[VOICE] Failed to start recording:", error)
        _continuous_recording = False
        _continuous_stream = None
        return False


def listen_stop():
    """
    Stop continuous microphone recording and recognize the speech.
    Returns recognized text or None on failure.
    """
    global _continuous_audio_buffer
    global _continuous_stream
    global _continuous_recording

    if not _continuous_recording:
        print("[VOICE] Not recording.")
        return None

    # Stop and close stream
    _continuous_recording = False

    if _continuous_stream is not None:
        try:
            _continuous_stream.stop()
            _continuous_stream.close()
        except Exception as error:
            print("[VOICE] Stream close error:", error)
        _continuous_stream = None

    # Check if we have audio data
    if not _continuous_audio_buffer:
        print("[VOICE] No audio data captured.")
        _continuous_audio_buffer = []
        return None

    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        print("[VOICE] numpy or soundfile not installed.")
        _continuous_audio_buffer = []
        return None

    if sr is None:
        print("[VOICE] SpeechRecognition is not installed.")
        _continuous_audio_buffer = []
        return None

    try:
        # Concatenate all audio chunks
        import numpy as np
        audio_data = np.concatenate(_continuous_audio_buffer, axis=0)
        _continuous_audio_buffer = []

        print("[VOICE] Recording complete. Total samples:", len(audio_data))

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:
            audio_path = temp_file.name

        sf.write(audio_path, audio_data, _continuous_sample_rate)

        # Read audio with SpeechRecognition
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        # Delete temporary file
        try:
            os.remove(audio_path)
        except Exception:
            pass

        print("[VOICE] Recognizing...")

        text = recognizer.recognize_google(audio)

        if text:
            print("[VOICE] Recognized:", text)
            return str(text).strip()

        return None

    except sr.UnknownValueError:
        print("[VOICE] Could not understand audio.")
        return None

    except sr.RequestError as error:
        print("[VOICE RECOGNITION ERROR]", error)
        return None

    except Exception as error:
        print("[VOICE LISTEN ERROR]", error)
        return None

    finally:
        _continuous_audio_buffer = []


def is_recording():
    """Check if continuous recording is active."""
    return _continuous_recording


# ============================================================
# SPEECH-TO-TEXT (Original one-shot)
# ============================================================
def listen(
    timeout=8,
    phrase_time_limit=15
):
    """
    Microphone speech-to-text using sounddevice.

    Does NOT require PyAudio.
    """

    if sr is None:
        print(
            "[VOICE] SpeechRecognition is not installed."
        )
        return None

    if sd is None:
        print(
            "[VOICE] sounddevice is not installed."
        )
        return None

    try:
        import soundfile as sf
    except ImportError:
        print(
            "[VOICE] soundfile is not installed."
        )
        return None

    try:

        print(
            "[VOICE] Listening..."
        )

        sample_rate = 16000

        # Record audio
        audio_data = sd.rec(
            int(
                phrase_time_limit
                * sample_rate
            ),

            samplerate=sample_rate,

            channels=1,

            dtype="int16",

            blocking=True
        )

        sd.wait()

        print(
            "[VOICE] Recording complete."
        )

        # Temporary WAV file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:

            audio_path = temp_file.name

        # Save recording
        sf.write(
            audio_path,
            audio_data,
            sample_rate
        )

        # Read audio with SpeechRecognition
        recognizer = sr.Recognizer()

        with sr.AudioFile(
            audio_path
        ) as source:

            audio = recognizer.record(
                source
            )

        # Delete temporary file
        try:

            os.remove(
                audio_path
            )

        except Exception:

            pass

        print(
            "[VOICE] Recognizing..."
        )

        text = recognizer.recognize_google(
            audio
        )

        if text:

            print(
                "[VOICE] Recognized:",
                text
            )

            return str(
                text
            ).strip()

        return None

    except sr.UnknownValueError:

        print(
            "[VOICE] Could not understand audio."
        )

        return None

    except sr.RequestError as error:

        print(
            "[VOICE RECOGNITION ERROR]",
            error
        )

        return None

    except Exception as error:

        print(
            "[VOICE LISTEN ERROR]",
            error
        )

        return None
# ============================================================
# WAKE WORD DETECTION
# ============================================================

_wake_word = None
_wake_callback = None
_wake_thread = None
_wake_running = False
_wake_lock = threading.RLock()


def _get_wake_word():
    """Get the configured wake word."""
    word = get_setting(
        "voice_extended.wake_word",
        "hey avora"
    )
    return str(word).lower().strip()


def _detect_wake_word(text):
    """Check if the wake word is present in the recognized text."""
    if not text:
        return False

    wake_word = _get_wake_word()
    text_lower = str(text).lower().strip()

    # Check for exact wake word
    if wake_word in text_lower:
        return True

    # Check for simplified versions
    simplified = wake_word.replace("hey ", "").strip()
    if simplified and simplified in text_lower:
        return True

    # Check for just "avora"
    if "avora" in text_lower:
        return True

    return False


def _wake_word_loop():
    """Background thread that continuously listens for the wake word."""
    global _wake_word

    while _wake_running:
        try:
            if not get_setting(
                "voice_extended.continuous_listening",
                False
            ):
                time.sleep(1)
                continue

            # Listen for a short phrase (2 seconds)
            try:
                text = listen(
                    phrase_time_limit=2
                )
            except Exception as listen_error:
                print("[WAKE WORD LISTEN ERROR]", listen_error)
                time.sleep(0.5)
                continue

            if text and _detect_wake_word(text):
                _wake_word = text
                print(
                    "[WAKE WORD] Detected:",
                    text
                )

                if _wake_callback:
                    try:
                        _wake_callback(text)
                    except Exception as error:
                        print(
                            "[WAKE WORD CALLBACK ERROR]",
                            error
                        )

                # Cooldown to prevent multiple triggers
                time.sleep(1)

        except Exception as error:
            print("[WAKE WORD ERROR]", error)
            time.sleep(0.5)


def start_wake_word(callback=None):
    """Start the wake word detection thread."""
    global _wake_thread, _wake_running, _wake_callback

    with _wake_lock:
        if _wake_running:
            return True

        if sr is None or sd is None:
            print(
                "[WAKE WORD] SpeechRecognition or "
                "sounddevice not installed."
            )
            return False

        _wake_callback = callback
        _wake_running = True
        _wake_thread = threading.Thread(
            target=_wake_word_loop,
            daemon=True,
            name="AvoraWakeWord",
        )
        _wake_thread.start()
        print("[WAKE WORD] Listening for 'Hey Avora'...")
        return True


def stop_wake_word():
    """Stop the wake word detection thread."""
    global _wake_thread, _wake_running, _wake_callback

    with _wake_lock:
        _wake_running = False
        _wake_thread = None
        _wake_callback = None


def is_wake_word_running():
    """Check if wake word detection is active."""
    return _wake_running


def get_wake_word():
    """Get the last detected wake word phrase."""
    return _wake_word


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    "speak",

    "stop_speaking",

    "is_speaking",

    "test_voice",

    "generate_voice",

    "set_voice",

    "listen",

    "listen_start",

    "listen_stop",

    "is_recording",

    "AVAILABLE_VOICES",

    "start_wake_word",

    "stop_wake_word",

    "is_wake_word_running",

    "get_wake_word",

    "AVAILABLE_VOICES",

]
