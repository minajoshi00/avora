# AVORA

<div align="center">

![AVORA](https://img.shields.io/badge/AVORA-AI%20Companion-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![PySide6](https://img.shields.io/badge/PySide6-UI%20Framework-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Your intelligent AI companion that chats, assists, and grows with you.**

[Features](#features) • [Installation](#installation) • [Configuration](#configuration) • [Usage](#usage) • [Contributing](#contributing)

</div>

---

## About AVORA

AVORA is a sophisticated AI companion desktop application designed to be your personal assistant, friend, and productivity tool. Built with Python and PySide6, AVORA combines advanced AI capabilities with an intuitive graphical interface to create a seamless user experience.

AVORA goes beyond traditional chatbots by offering:
- **Persistent memory** that learns from your interactions
- **Voice interaction** with natural text-to-speech
- **System integration** for controlling your computer
- **Extensible skills system** for unlimited functionality
- **Emotional intelligence** with an animated character

Whether you need help with coding, want to manage your emails, control your computer with voice commands, or just have a friendly conversation, AVORA is designed to be your intelligent companion.

---

## Features

### Core Features
- **AI-Powered Conversations**: Advanced chat using Google Gemini and Groq AI with automatic fallback
- **Voice Assistant**: Natural voice interaction with edge-TTS and speech recognition
- **Animated Character**: Interactive AI companion with emotions and animations
- **Persistent Memory**: Long-term memory that remembers your preferences and important information
- **Smart Context**: Learns from conversations to provide personalized responses

### System Integration
- **System Control**: Shutdown, restart, sleep, lock your computer with voice commands
- **File Management**: Create, open, move, and organize files through conversation
- **Application Launcher**: Open any installed application by voice or text
- **Windows Integration**: Deep Windows OS integration with hotkeys and startup support

### Communication & Productivity
- **Gmail Integration**: Read, send, search, and manage emails (optional)
- **Smart Email Handling**: Automatic email checking and management
- **Calendar & Timers**: Set reminders and manage your schedule
- **Web Search**: Search Google, YouTube, and open websites

### Advanced Features
- **Skills System**: Modular architecture for extending functionality
- **Automation**: Automate repetitive tasks and workflows
- **Image Generation**: Create images with AI (Pollinations.ai)
- **Weather Integration**: Real-time weather information and forecasts
- **Multi-Provider AI**: Automatic fallback between AI providers for reliability
- **Privacy Controls**: Granular permission system for AI actions

### Customization
- **Multiple Personalities**: Choose from various AI personalities (Friendly Bro, Professional, Study Buddy, etc.)
- **Theme Support**: Dark and light modes with glassmorphism effects
- **Voice Selection**: Multiple neural voices for text-to-speech
- **Adjustable Behavior**: Fine-tune formality, emoji usage, slang, and proactivity

---

## Tech Stack

**Core Technologies:**
- Python 3.8+
- PySide6 (Qt for Python) - Desktop GUI Framework
- Google Gemini AI - Primary AI Provider
- Groq - Fallback AI Provider with LLaMA models

**Key Libraries:**
- **AI/ML**: google-genai, groq
- **Voice**: edge-tts, SpeechRecognition, sounddevice, soundfile
- **GUI**: PySide6, Qt
- **System**: psutil, pyautogui, pynput, pywin32 (Windows)
- **Integration**: google-api-python-client, google-auth-oauthlib (Gmail)
- **Utilities**: requests, python-dotenv, numpy, Pillow

**Architecture:**
- Modular skills system for extensibility
- Settings management with persistent JSON storage
- Thread-safe operations with safe error handling
- Event-driven UI with real-time updates

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (Windows-specific features)
- Git (for cloning)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/AVORA.git
   cd AVORA
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   # Copy the example environment file
   copy .env.example .env
   ```
   
   Edit `.env` and add your API keys (see [Configuration](#configuration))

4. **Run AVORA**
   ```bash
   python main.py
   ```

### Optional: Setup Gmail (Optional Feature)

Gmail integration is **completely optional**. To enable:
1. Open AVORA Settings
2. Navigate to Gmail section
3. Click "Connect Gmail Account"
4. Follow the OAuth login flow

---

## Configuration

### Environment Variables

AVORA uses environment variables for API keys. Copy `.env.example` to `.env` and fill in your keys:

**Required:**
- `GEMINI_API_KEY` - Get yours at [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional:**
- `GROQ_API_KEY` - Get yours at [Groq Console](https://console.groq.com/keys) (provides fallback AI)
- `POLLINATIONS_API_KEY` - Get yours at [Pollinations.ai](https://pollinations.ai/) (for image generation)
- `OPENWEATHER_API_KEY` - Get yours at [OpenWeatherMap](https://openweathermap.org/api) (for weather features)

**Model Configuration (Optional):**
- `GEMINI_MODEL` - Default: `gemini-2.5-flash`
- `GROQ_MODEL` - Default: `llama-3.3-70b-versatile`

**Note:** Only `GEMINI_API_KEY` is required for basic functionality. Other keys are optional and enable additional features.

### Settings

AVORA stores user preferences in `settings.json` (automatically created). Access settings through the Settings UI in the application.

---

## Usage

### Basic Commands

- **Chat**: Just type your message and AVORA will respond
- **Voice**: Click the microphone button to speak
- **Open Apps**: "Open Chrome", "Launch VS Code"
- **System Control**: "Shutdown computer", "Restart", "Lock my PC"
- **Files**: "Open Documents folder", "Create a file called notes.txt"
- **Weather**: "What's the weather in New York?"
- **Timers**: "Set a timer for 10 minutes"
- **Memory**: "Remember that my favorite color is blue"

### Email Commands (If Gmail Connected)

- "Check my emails"
- "Read my recent emails"
- "Search emails from John"
- "Send an email to john@example.com"

### Image Generation

- "Generate an image of a sunset over mountains"
- "Create a picture of a futuristic city"

---

## Project Structure

```
AVORA/
├── main.py                 # Application entry point
├── ai_logic.py            # AI engine and command routing
├── settings.py            # Settings management system
├── settings_ui.py         # Settings window UI
├── character.py           # Animated character system
├── voice.py               # Voice/TTS system
├── memory.py              # Long-term memory system
├── chat_sidebar.py        # Chat interface
├── skills/                # Modular skills system
│   ├── email.py          # Gmail integration
│   ├── files.py          # File operations
│   ├── image.py          # Image generation
│   ├── power.py          # System power controls
│   ├── system.py         # System information
│   ├── weather.py        # Weather integration
│   └── ...
├── templates/             # UI templates
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── settings.json         # User settings (auto-generated)
└── README.md            # This file
```

---

## Screenshots

<div align="center">

*Screenshots coming soon!*

![AVORA Screenshot](screenshots/main_window.png)

</div>

---

## Roadmap

### Planned Features
- [ ] Additional AI providers (OpenAI, Anthropic Claude)
- [ ] Plugin system for community extensions
- [ ] Multi-language support
- [ ] Mobile companion app
- [ ] Advanced automation workflows
- [ ] More animated character expressions
- [ ] Collaborative features
- [ ] Skill marketplace
- [ ] Voice customization with cloning
- [ ] Integration with more services (Calendar, Tasks, Notes)

### Improvements
- [ ] Enhanced memory with semantic search
- [ ] Better offline capabilities
- [ ] Performance optimizations
- [ ] Comprehensive test coverage
- [ ] Detailed documentation
- [ ] Video tutorials

---

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-new-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'Add some feature'`
5. **Push to the branch**: `git push origin feature/my-new-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AVORA.git
cd AVORA

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env
# Edit .env with your API keys

# Run AVORA
python main.py
```

### Code Guidelines

- Follow PEP 8 style guide
- Add comments for complex logic
- Update documentation for new features
- Test your changes thoroughly
- Update requirements.txt if adding dependencies

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Google Gemini** for powerful AI capabilities
- **Groq** for fast AI inference
- **PySide6** for the GUI framework
- **edge-tts** for natural text-to-speech
- **Pollinations.ai** for image generation
- All contributors and testers

---

## Support

If you encounter any issues or have questions:

1. Check the [documentation](https://github.com/YOUR_USERNAME/AVORA/wiki)
2. Search [existing issues](https://github.com/YOUR_USERNAME/AVORA/issues)
3. Create a new issue with detailed information

---

## Star History

If you find AVORA useful, please consider giving it a star ⭐

<div align="center">

Made with ❤️ by the AVORA Team

</div>
</parameter>
</write_to_file>