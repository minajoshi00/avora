"""
===============================================================
                    VISION ENGINE
===============================================================

Screen capture and analysis engine for AVORA's Screen Awareness.

Features:
  - Screen capture using mss (fast, lightweight)
  - OCR for text recognition (pytesseract fallback)
  - Active window detection
  - Process detection
  - Intent inference (not just app detection)
  - Coding context detection (language, errors, git)
  - Study material detection
  - Gaming detection
  - Graceful degradation if vision libraries unavailable
  - All processing local by default

Privacy:
  - All analysis happens locally
  - No screenshots uploaded without explicit consent
  - Can operate with window-only mode (no screen capture)
===============================================================
"""

import time
import logging
import threading
import re
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("VisionEngine")

# Try to import vision libraries
try:
    import mss
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# =============================================================
# ACTIVITY TYPES
# =============================================================

class ActivityType(Enum):
    CODING = "coding"
    BROWSING = "browsing"
    GAMING = "gaming"
    STUDYING = "studying"
    WATCHING_VIDEOS = "watching_videos"
    WORKING = "working"
    READING = "reading"
    DESIGNING = "designing"
    CHATTING = "chatting"
    IDLE = "idle"
    UNKNOWN = "unknown"


# =============================================================
# DATA STRUCTURES
# =============================================================

@dataclass
class ScreenAnalysis:
    """Result of screen analysis."""
    timestamp: float = 0.0
    active_app: str = ""
    window_title: str = ""
    process_name: str = ""
    activity_type: str = "unknown"
    visible_text: str = ""
    is_gaming: bool = False
    is_idle: bool = False
    confidence: float = 0.0
    error: Optional[str] = None
    
    # Intent inference
    intent: str = "unknown"
    intent_confidence: float = 0.0
    
    # Coding context
    coding_language: str = ""
    coding_file: str = ""
    coding_project: str = ""
    has_error: bool = False
    error_type: str = ""
    
    # Study context
    study_subject: str = ""
    study_duration_minutes: float = 0.0
    
    # Gaming context
    game_name: str = ""
    
    # Work context
    work_type: str = ""


# =============================================================
# VISION ENGINE
# =============================================================

class VisionEngine:
    """
    Screen capture and analysis engine.
    Uses mss for capture, pytesseract for OCR.
    Gracefully falls back to window-only mode if vision unavailable.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._mss = None
        self._pytesseract = None
        self._pil = None
        self._available = False
        self._window_only = False
        self._error_message: Optional[str] = None
        
        # Cached results
        self._last_analysis: Optional[ScreenAnalysis] = None
        self._last_analysis_time: float = 0.0
        self._cache_duration: float = 2.0
        
        # Content hash for change detection
        self._last_content_hash: str = ""
        self._change_threshold: float = 0.15  # 15% change required
        
        # Activity tracking for intent inference
        self._activity_history: list = []
        self._max_history: int = 20
        
        # Coding detection patterns
        self._coding_keywords = {
            "visual studio", "vscode", "code", "pycharm", "intellij", "webstorm",
            "sublime text", "atom", "notepad++", "vim", "neovim", "emacs",
            "xcode", "android studio", "eclipse", "netbeans", "clion",
            "rider", "goland", "phpstorm", "rubymine", "terminal", "cmd",
            "powershell", "git bash", "wsl", "python", "jupyter", "colab",
            "coding", "programming", "developing", "debugging", "compiler",
            "ide", "editor", "vs code", "cursor", "windsurf", "github desktop",
        }
        
        # Language detection from file extensions and titles
        self._language_patterns = {
            "python": [r"\.py$", r"python", r"\.ipynb$"],
            "javascript": [r"\.js$", r"javascript", r"\.jsx$"],
            "typescript": [r"\.ts$", r"typescript", r"\.tsx$"],
            "java": [r"\.java$", r"java"],
            "cpp": [r"\.cpp$", r"\.c$", r"\.h$", r"c\+\+"],
            "csharp": [r"\.cs$", r"c#"],
            "go": [r"\.go$", r"golang"],
            "rust": [r"\.rs$", r"rust"],
            "ruby": [r"\.rb$", r"ruby"],
            "php": [r"\.php$", r"php"],
            "swift": [r"\.swift$", r"swift"],
            "kotlin": [r"\.kt$", r"kotlin"],
            "html": [r"\.html$", r"\.htm$"],
            "css": [r"\.css$", r"\.scss$", r"\.sass$"],
            "sql": [r"\.sql$", r"sql"],
            "markdown": [r"\.md$", r"readme"],
        }
        
        # Error patterns
        self._error_patterns = {
            "python_traceback": r"traceback \(most recent call last\)",
            "python_exception": r"^\w+Error:",
            "javascript_error": r"uncaught \w+Error",
            "typescript_error": r"error TS\d+:",
            "java_exception": r"Exception in thread",
            "compiler_error": r"error:\s*\w+",
            "git_conflict": r"<<<<<<<|>>>>>>>|=======",
            "build_failed": r"build failed|compilation failed",
        }
        
        # Gaming keywords
        self._gaming_keywords = {
            "minecraft", "roblox", "fortnite", "valorant", "league of legends",
            "counter-strike", "cs:go", "cs2", "dota 2", "overwatch", "apex",
            "call of duty", "battlefield", "rocket league", "gta", "grand theft auto",
            "red dead", "cyberpunk", "the witcher", "skyrim", "fallout",
            "among us", "pubg", "fortnite", "destiny", "warframe", "path of exile",
            "world of warcraft", "wow", "final fantasy", "elden ring", "steam",
            "epic games", "battle.net", "origin", "uplay", "ubisoft connect",
            "xbox", "playstation", "nintendo", "emulator", "game", "gaming",
        }
        
        # Studying keywords
        self._studying_keywords = {
            "pdf", "acrobat", "reader", "ebook", "kindle", "epub",
            "notion", "onenote", "evernote", "bear", "roam research",
            "obsidian", "logseq", "anki", "quizlet", "duolingo",
            "coursera", "udemy", "edx", "khan academy", "brilliant",
            "study", "learning", "course", "lecture", "tutorial",
            "textbook", "notes", "flashcard", "homework", "assignment",
            "wikipedia", "dictionary", "thesaurus", "class", "school",
            "college", "university", "exam", "test", "practice",
            "microsoft word", "word", "google docs", "docs",
            "microsoft teams", "zoom", "google meet", "webex",
            "scholar", "research", "paper", "thesis", "dissertation",
        }
        
        # Video keywords
        self._video_keywords = {
            "youtube", "netflix", "hulu", "disney+", "disney plus",
            "amazon prime", "prime video", "hbo", "max", "hbo max",
            "crunchyroll", "funimation", "vimeo", "twitch", "kodi",
            "vlc", "mpv", "media player", "plex", "emby", "jellyfin",
            "spotify", "tidal", "apple music", "music", "podcast",
            "streaming", "video", "movie", "anime", "tv show",
            "binge", "watching", "listen", "playing",
        }
        
        # Browsing keywords
        self._browsing_keywords = {
            "chrome", "firefox", "edge", "brave", "opera", "vivaldi",
            "browser", "tor browser", "arc", "chromium",
            "google chrome", "mozilla firefox", "microsoft edge",
        }
        
        # Design keywords
        self._design_keywords = {
            "photoshop", "illustrator", "figma", "sketch", "xd",
            "blender", "maya", "3ds max", "cinema 4d", "after effects",
            "premiere", "da vinci", "canva", "procreate", "clip studio",
            "design", "graphic", "ui/ux", "prototype",
        }
        
        # Chat keywords
        self._chat_keywords = {
            "discord", "slack", "teams", "whatsapp", "telegram",
            "messenger", "signal", "zoom", "skype", "line",
            "chat", "message", "conversation",
        }
        
        # Try to initialize
        self._initialize()

    def _initialize(self):
        """Try to initialize vision libraries."""
        try:
            import mss
            self._mss = mss
            logger.info("mss initialized successfully")
        except ImportError:
            logger.warning("mss not available - install with: pip install mss")
            self._error_message = "Screen capture library (mss) not available"
        
        try:
            import pytesseract
            self._pytesseract = pytesseract
            logger.info("pytesseract initialized successfully")
        except ImportError:
            logger.warning("pytesseract not available - OCR disabled")
        
        try:
            from PIL import Image
            self._pil = Image
            logger.info("PIL initialized successfully")
        except ImportError:
            logger.warning("PIL not available - image processing disabled")
        
        # Determine if we have full vision or window-only mode
        if self._mss and self._pil and self._pytesseract:
            self._available = True
            self._window_only = False
        elif self._mss:
            self._available = True
            self._window_only = True  # Can capture but not OCR
        else:
            self._available = False
            self._window_only = True  # Window detection only

    def is_available(self) -> bool:
        """Check if vision engine is available."""
        return self._available or self._window_only

    def get_error(self) -> Optional[str]:
        """Get initialization error message if any."""
        return self._error_message

    def get_capabilities(self) -> Dict[str, bool]:
        """Get vision capabilities."""
        return {
            "screen_capture": self._mss is not None,
            "ocr": self._pytesseract is not None,
            "image_processing": self._pil is not None,
            "available": self._available,
            "window_only": self._window_only,
        }

    def capture_screen(self) -> Optional[Any]:
        """
        Capture current screen.
        Returns PIL Image or None on failure.
        """
        if not self._mss:
            return None
        
        try:
            with self._mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                # Convert to PIL Image
                img = self._pil.frombytes('RGB', screenshot.size, screenshot.rgb)
                return img
        except Exception as e:
            logger.debug(f"Screen capture error: {e}")
            return None

    def extract_text(self, image) -> str:
        """
        Extract text from image using OCR.
        Returns empty string if OCR unavailable.
        """
        if not self._pytesseract or not image:
            return ""
        
        try:
            text = self._pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.debug(f"OCR error: {e}")
            return ""

    def get_active_window_info(self) -> Tuple[str, str]:
        """
        Get active window title and process name.
        Returns (title, process) or ("", "") on failure.
        """
        try:
            import ctypes
            import ctypes.wintypes
            
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", ""
            
            # Get window title
            length = user32.GetWindowTextLengthW(hwnd) + 1
            title_buffer = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, title_buffer, length)
            title = title_buffer.value or ""
            
            # Get process name
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            process_name = ""
            try:
                handle = kernel32.OpenProcess(
                    0x0400 | 0x0010,  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
                    False,
                    pid.value
                )
                if handle:
                    exe_buffer = ctypes.create_unicode_buffer(260)
                    size = ctypes.wintypes.DWORD(260)
                    if ctypes.windll.psapi.GetModuleBaseNameW(handle, None, exe_buffer, size):
                        process_name = exe_buffer.value or ""
                    kernel32.CloseHandle(handle)
            except Exception:
                pass
            
            return title.strip(), process_name.strip()
            
        except Exception as e:
            logger.debug(f"Window detection error: {e}")
            return "", ""

    def _detect_coding_context(self, title: str, process: str, text: str) -> Tuple[str, str, str, bool, str]:
        """
        Detect coding-specific context.
        Returns (language, file, project, has_error, error_type).
        """
        language = ""
        file_name = ""
        project = ""
        has_error = False
        error_type = ""
        
        combined = (title + " " + process + " " + text).lower()
        
        # Detect programming language
        for lang, patterns in self._language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined):
                    language = lang
                    break
            if language:
                break
        
        # Extract file name from title
        file_match = re.search(r"([^\\/:*?\"<>|]+\.(py|js|ts|java|cpp|c|h|go|rs|rb|php|swift|kt|html|css|sql|md))", title, re.IGNORECASE)
        if file_match:
            file_name = file_match.group(1)
        
        # Extract project folder
        project_match = re.search(r"([^\\/:*?\"<>|]+)\s*[-–—]\s*(?:visual studio|vscode|code)", title, re.IGNORECASE)
        if project_match:
            project = project_match.group(1).strip()
        
        # Detect errors
        for error_name, pattern in self._error_patterns.items():
            if re.search(pattern, combined, re.IGNORECASE):
                has_error = True
                error_type = error_name
                break
        
        # Check for terminal/error indicators in text
        if "traceback" in combined or "exception" in combined:
            has_error = True
            error_type = "python_exception"
        
        return language, file_name, project, has_error, error_type

    def _infer_intent(self, activity: str, title: str, process: str, text: str) -> Tuple[str, float]:
        """
        Infer user intent from activity, title, process, and visible text.
        Returns (intent, confidence).
        """
        combined = (title + " " + process + " " + text).lower()
        
        # Start with base activity
        intent = activity
        confidence = 0.6
        
        # Refine intent based on context
        if activity == "coding":
            # Check for specific coding intents
            if any(kw in combined for kw in ["git", "github", "gitlab", "bitbucket"]):
                intent = "reviewing_code"
                confidence = 0.85
            elif any(kw in combined for kw in ["debug", "debugging", "traceback", "exception"]):
                intent = "debugging"
                confidence = 0.9
            elif any(kw in combined for kw in ["test", "testing", "pytest", "jest"]):
                intent = "testing"
                confidence = 0.85
            elif any(kw in combined for kw in ["review", "pr", "pull request"]):
                intent = "code_review"
                confidence = 0.85
            else:
                intent = "coding"
                confidence = 0.75
        
        elif activity == "browsing":
            if "youtube" in combined:
                intent = "watching_videos"
                confidence = 0.9
            elif "github" in combined:
                intent = "reviewing_code"
                confidence = 0.8
            elif any(kw in combined for kw in ["amazon", "ebay", "shop", "store"]):
                intent = "shopping"
                confidence = 0.85
            elif any(kw in combined for kw in ["news", "article", "blog"]):
                intent = "reading_news"
                confidence = 0.8
            else:
                intent = "browsing"
                confidence = 0.6
        
        elif activity == "studying":
            if "pdf" in combined or "document" in combined:
                intent = "reading_material"
                confidence = 0.85
            elif any(kw in combined for kw in ["quiz", "flashcard", "test"]):
                intent = "taking_quiz"
                confidence = 0.9
            elif any(kw in combined for kw in ["video", "lecture", "course"]):
                intent = "watching_lecture"
                confidence = 0.85
            else:
                intent = "studying"
                confidence = 0.75
        
        elif activity == "gaming":
            intent = "gaming"
            confidence = 0.9
        
        elif activity == "working":
            if "excel" in combined:
                intent = "data_analysis"
                confidence = 0.85
            elif "word" in combined:
                intent = "writing"
                confidence = 0.85
            elif "powerpoint" in combined or "presentation" in combined:
                intent = "creating_presentation"
                confidence = 0.85
            elif "email" in combined or "outlook" in combined:
                intent = "email"
                confidence = 0.9
            else:
                intent = "working"
                confidence = 0.7
        
        elif activity == "watching_videos":
            intent = "entertainment"
            confidence = 0.85
        
        elif activity == "designing":
            intent = "designing"
            confidence = 0.9
        
        elif activity == "chatting":
            intent = "communicating"
            confidence = 0.85
        
        return intent, confidence

    def classify_activity(self, title: str, process: str, visible_text: str = "") -> Tuple[ActivityType, float]:
        """
        Classify activity from window info and visible text.
        Returns (activity_type, confidence).
        """
        if not title and not process:
            return ActivityType.UNKNOWN, 0.0
        
        combined = (title + " " + process + " " + visible_text).lower()
        confidence = 0.5
        
        # Check for gaming
        if any(kw in combined for kw in self._gaming_keywords):
            return ActivityType.GAMING, 0.9
        
        # Check for coding
        if any(kw in combined for kw in self._coding_keywords):
            return ActivityType.CODING, 0.9
        
        # Check for studying
        if any(kw in combined for kw in self._studying_keywords):
            return ActivityType.STUDYING, 0.85
        
        # Check for videos
        if any(kw in combined for kw in self._video_keywords):
            return ActivityType.WATCHING_VIDEOS, 0.9
        
        # Check for browsing
        if any(kw in combined for kw in self._browsing_keywords):
            return ActivityType.BROWSING, 0.8
        
        # Check for designing
        if any(kw in combined for kw in self._design_keywords):
            return ActivityType.DESIGNING, 0.85
        
        # Check for chatting
        if any(kw in combined for kw in self._chat_keywords):
            return ActivityType.CHATTING, 0.8
        
        # Check for reading indicators in text
        if visible_text and len(visible_text) > 100:
            return ActivityType.READING, 0.6
        
        return ActivityType.UNKNOWN, 0.3

    def analyze(self, force: bool = False) -> ScreenAnalysis:
        """
        Perform screen analysis.
        Returns ScreenAnalysis with detected context.
        """
        now = time.time()
        
        # Use cache if recent
        if not force and self._last_analysis and (now - self._last_analysis_time) < self._cache_duration:
            return self._last_analysis
        
        analysis = ScreenAnalysis(timestamp=now)
        
        try:
            # Get window info
            title, process = self.get_active_window_info()
            analysis.window_title = title
            analysis.process_name = process
            
            # Extract app name from process
            if process:
                analysis.active_app = process.lower().replace(".exe", "")
            
            # Get visible text if available
            visible_text = ""
            if self._mss and self._pil:
                img = self.capture_screen()
                if img:
                    visible_text = self.extract_text(img)
            analysis.visible_text = visible_text[:500] if visible_text else ""  # Limit text length
            
            # Classify activity
            activity_type, confidence = self.classify_activity(
                title, process, visible_text
            )
            analysis.activity_type = activity_type.value
            analysis.confidence = confidence
            
            # Infer intent
            intent, intent_confidence = self._infer_intent(
                activity_type.value, title, process, visible_text
            )
            analysis.intent = intent
            analysis.intent_confidence = intent_confidence
            
            # Detect coding context
            if activity_type == ActivityType.CODING:
                lang, file, project, has_error, error_type = self._detect_coding_context(
                    title, process, visible_text
                )
                analysis.coding_language = lang
                analysis.coding_file = file
                analysis.coding_project = project
                analysis.has_error = has_error
                analysis.error_type = error_type
            
            # Detect gaming
            analysis.is_gaming = activity_type == ActivityType.GAMING
            if analysis.is_gaming:
                # Extract game name
                for game in self._gaming_keywords:
                    if game in (title + " " + process).lower():
                        analysis.game_name = game
                        break
            
            # Detect idle (no window title or process)
            analysis.is_idle = not title and not process
            
        except Exception as e:
            analysis.error = str(e)
            logger.debug(f"Analysis error: {e}")
        
        # Cache result
        with self._lock:
            self._last_analysis = analysis
            self._last_analysis_time = now
        
        return analysis

    def get_last_analysis(self) -> Optional[ScreenAnalysis]:
        """Get last analysis result."""
        with self._lock:
            return self._last_analysis

    def clear_cache(self):
        """Clear analysis cache."""
        with self._lock:
            self._last_analysis = None
            self._last_analysis_time = 0.0
            self._last_content_hash = ""