"""
===============================================================
                FALCON - ACTIVITY AWARENESS MONITOR
===============================================================

Privacy-controlled activity awareness that detects high-level
user activity (coding, browsing, gaming, studying, etc.)
without accessing screen, microphone, or private content.

Uses only active window title and process name via Windows API.

Lightweight: polls every 5 seconds, uses cooldowns, no AI calls.
===============================================================
"""

import time
import logging
import threading
from enum import Enum
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger("ActivityMonitor")


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
    IDLE = "idle"
    UNKNOWN = "unknown"


# =============================================================
# ACTIVITY KEYWORDS
# =============================================================

# These are matched against lowercase window titles and process names.
# No screen capture or content monitoring.

CODING_KEYWORDS = {
    "visual studio", "vscode", "code", "pycharm", "intellij", "webstorm",
    "sublime text", "atom", "notepad++", "vim", "neovim", "emacs",
    "xcode", "android studio", "eclipse", "netbeans", "clion",
    "rider", "goland", "phpstorm", "rubymine", "terminal", "cmd",
    "powershell", "git bash", "wsl", "python", "jupyter", "colab",
    "coding", "programming", "developing", "debugging", "compiler",
    "ide", "editor", "vs code", "cursor", "windsurf", "github desktop",
}

BROWSING_KEYWORDS = {
    "chrome", "firefox", "edge", "brave", "opera", "vivaldi",
    "browser", "tor browser", "arc", "chromium",
    "google chrome", "mozilla firefox", "microsoft edge",
}

GAMING_KEYWORDS = {
    "minecraft", "roblox", "fortnite", "valorant", "league of legends",
    "counter-strike", "cs:go", "cs2", "dota 2", "overwatch", "apex",
    "call of duty", "battlefield", "rocket league", "gta", "grand theft auto",
    "red dead", "cyberpunk", "the witcher", "skyrim", "fallout",
    "among us", "pubg", "fortnite", "destiny", "warframe", "path of exile",
    "world of warcraft", "wow", "final fantasy", "elden ring", "steam",
    "epic games", "battle.net", "origin", "uplay", "ubisoft connect",
    "xbox", "playstation", "nintendo", "emulator", "game", "gaming",
}

STUDYING_KEYWORDS = {
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

WATCHING_VIDEOS_KEYWORDS = {
    "youtube", "netflix", "hulu", "disney+", "disney plus",
    "amazon prime", "prime video", "hbo", "max", "hbo max",
    "crunchyroll", "funimation", "vimeo", "twitch", "kodi",
    "vlc", "mpv", "media player", "plex", "emby", "jellyfin",
    "spotify", "tidal", "apple music", "music", "podcast",
    "streaming", "video", "movie", "anime", "tv show",
    "binge", "watching", "listen", "playing",
}

WORKING_KEYWORDS = {
    "excel", "microsoft excel", "sheets", "google sheets",
    "powerpoint", "slides", "microsoft powerpoint",
    "outlook", "microsoft outlook", "thunderbird",
    "slack", "discord", "telegram", "whatsapp", "signal",
    "microsoft word", "word", "google docs", "docs",
    "notion", "todoist", "trello", "asana", "jira",
    "confluence", "basecamp", "clickup", "monday.com",
    "office", "microsoft 365", "libreoffice", "openoffice",
    "calculator", "calendar", "clock", "alarm",
    "working", "work", "business", "presentation",
    "spreadsheet", "document", "report", "invoice",
}


# =============================================================
# WINDOWS ACTIVE WINDOW DETECTION (ctypes, no external deps)
# =============================================================

class _WindowInfo:
    """Cached window info to avoid repeated API calls."""
    __slots__ = ("title", "process", "timestamp")


def _get_active_window_info() -> tuple[str, str]:
    """
    Get the active window title and process name using ctypes.
    No external dependencies needed.
    Returns (title, process_name) or ("", "") on failure.
    """
    try:
        import ctypes
        import ctypes.wintypes
        
        # Get foreground window handle
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
        
        # Get process ID
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Get process name from PID
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


# =============================================================
# ACTIVITY CLASSIFIER
# =============================================================

def classify_activity(title: str, process: str) -> ActivityType:
    """
    Classify the current activity based on window title and process name.
    Only uses keyword matching - no content monitoring.
    """
    if not title and not process:
        return ActivityType.UNKNOWN
    
    combined = (title + " " + process).lower()
    
    # Check in order of specificity
    if any(kw in combined for kw in CODING_KEYWORDS):
        return ActivityType.CODING
    if any(kw in combined for kw in GAMING_KEYWORDS):
        return ActivityType.GAMING
    if any(kw in combined for kw in STUDYING_KEYWORDS):
        return ActivityType.STUDYING
    if any(kw in combined for kw in WATCHING_VIDEOS_KEYWORDS):
        return ActivityType.WATCHING_VIDEOS
    if any(kw in combined for kw in BROWSING_KEYWORDS):
        return ActivityType.BROWSING
    if any(kw in combined for kw in WORKING_KEYWORDS):
        return ActivityType.WORKING
    
    return ActivityType.UNKNOWN


# =============================================================
# PROACTIVE MESSAGES BY ACTIVITY AND PERSONALITY
# =============================================================

PROACTIVE_MESSAGES = {
    "coding": {
        "friendly": [
            "Brooo, you've been coding for a while! 😅 Need any help debugging?",
            "That code looking good bro? 👨‍💻 Need a fresh pair of eyes?",
            "You're on fire today! 🔥 Want me to review that logic?",
            "Code crunch time! 💻 Need a break reminder?",
            "Building something epic? 🚀 I can help if you get stuck!",
        ],
        "professional": [
            "I notice you're deep in development. Would you like assistance with debugging or code review?",
            "You've been programming for some time. Shall I help optimize that code?",
            "Your focus on coding is impressive. Need a second opinion on any logic?",
        ],
        "funny": [
            "You coding or creating a masterpiece? 🎨 Either way, I'm impressed!",
            "Are you programming the Matrix? 🤯 Don't forget to take a break, Neo!",
            "I see you're typing... a lot. Writing a novel or breaking production? 😂",
        ],
        "calm": [
            "You're deep in code. Remember to breathe and take breaks.",
            "Coding steadily I see. I'm here if you need anything.",
        ],
        "friendly_bro": [
            "Brooo, you've been coding for a long time 😭 Need help?",
            "Yo! That code looking clean or do you need a hand? 💪",
        ],
    },
    "browsing": {
        "friendly": [
            "Doing some research? 🧐 Want me to help summarize anything?",
            "Browsing the web? 🌐 Let me know if you need info!",
            "Found anything interesting? 👀 I'm great at research!",
        ],
        "professional": [
            "I see you're browsing. Would you like me to take notes or summarize content?",
            "If you need quick information extraction, I'm here to help.",
        ],
        "funny": [
            "Deep rabbit hole on the internet? 🐇 I got snacks!",
            "Wikipedia spiral or serious research? 🤔 No judgment here!",
        ],
        "calm": [
            "Taking some time to browse. I'm here for whatever you need.",
        ],
    },
    "gaming": {
        "friendly": [
            "Gaming time! 🎮 Getting those wins?",
            "How's the game going? Need any tips or strategies?",
            "Gamer mode activated! 😎 Want me to track your play time?",
        ],
        "professional": [
            "I see you're gaming. I can track session time if needed.",
        ],
        "funny": [
            "GOD MODE ACTIVATED! 🎮 Just kidding, but how's the K/D ratio? 😂",
            "Is that a new high score I sense? Or just respawn #47? 🔄",
        ],
        "calm": [
            "Enjoying your game. I'm here if you need anything.",
        ],
    },
    "studying": {
        "friendly": [
            "Studying hard! 📚 Want me to quiz you or explain something?",
            "Learning mode! 🧠 Need help understanding a topic?",
            "Great job studying! 📖 Want me to help summarize notes?",
        ],
        "professional": [
            "I see you're studying. I can help explain concepts or create study aids.",
            "Your dedication to learning is commendable. Need assistance with any topic?",
        ],
        "funny": [
            "Brain expanding time! 🧠💥 Need a study buddy? *raises hand*",
            "Crushing those study goals! 📚 Want me to test you? I promise not to make it too hard 😉",
        ],
        "calm": [
            "Studying peacefully. Let me know if you need explanations or summaries.",
        ],
    },
    "watching_videos": {
        "friendly": [
            "Watching something good? 🎬 Want me to take notes?",
            "Video time! 🍿 Let me know if you need info about what you're watching!",
        ],
        "funny": [
            "Binge-watching? 🍿 No judgment, I'd do the same!",
            "Is that educational or entertainment? 🤔 Either way, I support it!",
        ],
        "calm": [
            "Enjoying your content. I'm here if you need anything.",
        ],
    },
    "working": {
        "friendly": [
            "Getting work done! 💼 Need help with anything?",
            "Productivity mode! 📊 I can help organize your tasks.",
            "Working hard! Want me to set a focus timer?",
        ],
        "professional": [
            "I see you're working productively. Can I assist with task management?",
            "Your work session is progressing well. Need any support?",
        ],
        "funny": [
            "Adulting hard today? 💼 Want me to pretend to take notes in a meeting? 😂",
            "Look at you being productive! 👔 I'm basically your tiny desk assistant now.",
        ],
        "calm": [
            "Working steadily. I'm here to help whenever you need.",
        ],
    },
    "idle": {
        "friendly": [
            "Hey brooo! 👋 Back from your break?",
            "Welcome back! 😄 What do you want to do?",
        ],
        "professional": [
            "Welcome back. How can I assist you?",
        ],
        "funny": [
            "You're back! I was starting to think you ghosted me 👻",
            "Welcome back, stranger! 👋 Ready for round 2?",
        ],
        "calm": [
            "Good to see you. I'm here whenever you need.",
        ],
    },
}


# =============================================================
# ACTIVITY MONITOR
# =============================================================

class ActivityMonitor:
    """
    Lightweight activity monitor that polls the active window
    every N seconds. Detects high-level activity types and
    notifies listeners of changes.
    """
    
    def __init__(
        self,
        check_interval: float = 5.0,
        idle_threshold_minutes: float = 3.0,
    ):
        self._check_interval = check_interval
        self._idle_threshold = idle_threshold_minutes * 60.0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._listeners: list[Callable] = []
        
        # State
        self._current_activity: ActivityType = ActivityType.UNKNOWN
        self._previous_activity: ActivityType = ActivityType.UNKNOWN
        self._activity_start_time: float = time.time()
        self._session_start_time: float = time.time()
        self._last_activity_time: float = time.time()
        self._last_window_title: str = ""
        self._last_process: str = ""
        
        # Cached to avoid unnecessary processing
        self._cached_title: str = ""
        self._cached_process: str = ""
        self._cached_activity: ActivityType = ActivityType.UNKNOWN
        self._cache_time: float = 0
        self._cache_duration: float = 10.0
    
    # =========================================================
    # LIFECYCLE
    # =========================================================
    
    def start(self):
        """Start the activity monitor thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="ActivityMonitor",
            )
            self._thread.start()
            logger.info("Activity monitor started")
    
    def stop(self):
        """Stop the activity monitor thread."""
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("Activity monitor stopped")
    
    def add_listener(self, callback: Callable[[ActivityType, str], None]):
        """
        Add a listener that's called when activity changes.
        Callback receives (ActivityType, window_title).
        """
        with self._lock:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)
    
    # =========================================================
    # PROPERTIES
    # =========================================================
    
    @property
    def current_activity(self) -> ActivityType:
        return self._current_activity
    
    @property
    def activity_duration_minutes(self) -> float:
        """How long the current activity has been going on."""
        return (time.time() - self._activity_start_time) / 60.0
    
    @property
    def session_duration_minutes(self) -> float:
        """Total session duration."""
        return (time.time() - self._session_start_time) / 60.0
    
    @property
    def idle_minutes(self) -> float:
        """Minutes since last activity."""
        return (time.time() - self._last_activity_time) / 60.0
    
    @property
    def is_idle(self) -> bool:
        return self.idle_minutes >= (self._idle_threshold / 60.0)
    
    @property
    def window_title(self) -> str:
        return self._last_window_title
    
    @property
    def process_name(self) -> str:
        return self._last_process
    
    def get_activity_description(self) -> str:
        """Get a human-readable description of current activity."""
        mapping = {
            ActivityType.CODING: "coding",
            ActivityType.BROWSING: "browsing",
            ActivityType.GAMING: "gaming",
            ActivityType.STUDYING: "studying",
            ActivityType.WATCHING_VIDEOS: "watching videos",
            ActivityType.WORKING: "working",
            ActivityType.IDLE: "idle",
            ActivityType.UNKNOWN: "doing something",
        }
        return mapping.get(self._current_activity, "doing something")
    
    # =========================================================
    # PROACTIVE MESSAGE GENERATION
    # =========================================================
    
    def get_proactive_message(self, personality: str = "friendly") -> Optional[str]:
        """
        Get a context-aware proactive message based on current activity.
        Returns None if no message is appropriate.
        """
        activity = self.current_activity
        activity_name = activity.value
        
        # Get personality-specific messages for this activity
        messages_for_activity = PROACTIVE_MESSAGES.get(activity_name, {})
        
        # Try specific personality first, then fall through
        personality_keys = [personality, "friendly", "friendly_bro", "calm"]
        for key in personality_keys:
            msgs = messages_for_activity.get(key)
            if msgs:
                import random
                return random.choice(msgs)
        
        # Default fallback
        defaults = {
            ActivityType.CODING: "Need any help with your code?",
            ActivityType.BROWSING: "Need help researching?",
            ActivityType.GAMING: "How's the game going?",
            ActivityType.STUDYING: "Need help understanding something?",
            ActivityType.WATCHING_VIDEOS: "Enjoying the content?",
            ActivityType.WORKING: "Need a hand with anything?",
            ActivityType.IDLE: "Hey! Need anything?",
            ActivityType.UNKNOWN: "Let me know if you need help!",
        }
        return defaults.get(activity, "Hey! How can I help?")
    
    # =========================================================
    # INTERNAL
    # =========================================================
    
    def _run_loop(self):
        """Main monitor loop."""
        while True:
            with self._lock:
                if not self._running:
                    break
            
            try:
                self._check_activity()
            except Exception as e:
                logger.debug(f"Activity check error: {e}")
            
            time.sleep(self._check_interval)
    
    def _check_activity(self):
        """Check current activity and notify on change."""
        now = time.time()
        
        # Rate limit window detection
        if now - self._cache_time < self._cache_duration:
            return
        
        # Get active window info
        title, process = _get_active_window_info()
        
        self._cache_time = now
        self._cached_title = title
        self._cached_process = process
        
        # Update last activity time
        if title:
            self._last_activity_time = now
        
        # Check for idle
        if self.is_idle:
            new_activity = ActivityType.IDLE
        else:
            new_activity = classify_activity(title, process)
        
        # Store window info
        self._last_window_title = title
        self._last_process = process
        
        # Check if activity changed
        if new_activity != self._current_activity:
            self._previous_activity = self._current_activity
            self._current_activity = new_activity
            self._activity_start_time = now
            
            # Notify listeners
            self._notify_listeners(new_activity, title)
    
    def _notify_listeners(self, activity: ActivityType, title: str):
        """Notify all listeners of activity change."""
        listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(activity, title)
            except Exception as e:
                logger.error(f"Activity listener error: {e}")
