import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add VoiceInputWorker class after AIWorker class
worker_class = '''

class VoiceInputWorker(QThread):
    """
    Runs speech recognition in a background thread.
    Prevents the GUI from freezing while listening.
    """

    result = Signal(str)
    error = Signal(str)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_requested = False

    def run(self):
        try:
            text = listen(timeout=8, phrase_time_limit=15)
            if self._stop_requested:
                self.finished.emit()
                return
            if text:
                self.result.emit(str(text))
            else:
                self.error.emit("Could not understand audio.")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def request_stop(self):
        self._stop_requested = True
'''

# Insert after AIWorker class (before "# MAIN WINDOW")
content = content.replace(
    '\n\n# ============================================================\n# MAIN WINDOW',
    worker_class + '\n\n# ============================================================\n# MAIN WINDOW'
)

# 2. Add microphone button after send_button
mic_button_code = '''
        self.mic_button = QPushButton(
            "🎤"
        )

        self.mic_button.setObjectName(
            "MicButton"
        )

        self.mic_button.setFixedSize(
            48,
            42
        )

        self.mic_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.mic_button.clicked.connect(
            self.toggle_voice_input
        )

        self.voice_input_worker = None
        self.is_listening = False

        input_container_layout.addWidget(
            self.mic_button
        )
'''

# Insert after send_button.clicked.connect block
content = content.replace(
    '''        self.send_button.clicked.connect(
            self.send_message
        )

        input_container_layout.addWidget(
            self.user_input,
            1
        )

        input_container_layout.addWidget(
            self.send_button
        )''',
    '''        self.send_button.clicked.connect(
            self.send_message
        )

        input_container_layout.addWidget(
            self.user_input,
            1
        )

        input_container_layout.addWidget(
            self.send_button
        )
''' + mic_button_code
)

# 3. Add CSS for MicButton after SendButton CSS
css_mic = '''

            #MicButton {

                background-color: #20202D;

                border: 1px solid #303044;

                border-radius: 13px;

                color: #A0A0B5;

                font-size: 18px;
            }

            #MicButton:hover {

                background-color: #30304A;

                color: #FFFFFF;
            }

            #MicButton:listening {

                background-color: #FF4757;

                border-color: #FF4757;

                color: white;
            }
'''

content = content.replace(
    '''            #SendButton:disabled {

                background-color: #38364F;

                color: #888888;
            }''',
    '''            #SendButton:disabled {

                background-color: #38364F;

                color: #888888;
            }
''' + css_mic
)

# 4. Add toggle_voice_input and on_voice_input_finished methods
# Insert before "# CHARACTER VISIBILITY"
voice_methods = '''
    # ========================================================
    # VOICE INPUT (MICROPHONE)
    # ========================================================

    def toggle_voice_input(
        self,
    ):

        if self.is_listening:
            self.stop_voice_input()
            return

        if self.is_processing:
            return

        self.start_voice_input()

    def start_voice_input(
        self,
    ):

        self.is_listening = True

        self.mic_button.setText(
            "🔴"
        )

        self.mic_button.setProperty(
            "listening",
            True
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "thinking",
            "Listening...",
        )

        self.user_input.setPlaceholderText(
            "Listening... speak now"
        )

        self.voice_input_worker = VoiceInputWorker(
            self
        )

        self.voice_input_worker.result.connect(
            self.on_voice_input_finished
        )

        self.voice_input_worker.error.connect(
            self.on_voice_input_error
        )

        self.voice_input_worker.finished.connect(
            self.on_voice_input_worker_finished
        )

        self.voice_input_worker.start()

    def stop_voice_input(
        self,
    ):

        if self.voice_input_worker is not None:

            try:

                self.voice_input_worker.request_stop()

            except Exception:

                pass

        self.is_listening = False

        self.mic_button.setText(
            "🎤"
        )

        self.mic_button.setProperty(
            "listening",
            False
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "ready",
            "Ready",
        )

        self.user_input.setPlaceholderText(
            "Message your AI Friend..."
        )

    def on_voice_input_finished(
        self,
        text,
    ):

        self.is_listening = False

        self.mic_button.setText(
            "🎤"
        )

        self.mic_button.setProperty(
            "listening",
            False
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "ready",
            "Ready",
        )

        self.user_input.setPlaceholderText(
            "Message your AI Friend..."
        )

        if text:

            self.user_input.setText(
                str(text)
            )

            self.user_input.setFocus()

    def on_voice_input_error(
        self,
        error_msg,
    ):

        self.is_listening = False

        self.mic_button.setText(
            "🎤"
        )

        self.mic_button.setProperty(
            "listening",
            False
        )

        self.mic_button.style().unpolish(
            self.mic_button
        )

        self.mic_button.style().polish(
            self.mic_button
        )

        self.update_status(
            "ready",
            "Ready",
        )

        self.user_input.setPlaceholderText(
            "Message your AI Friend..."
        )

        QMessageBox.warning(
            self,
            "Microphone Error",
            str(error_msg),
        )

    def on_voice_input_worker_finished(
        self,
    ):

        self.voice_input_worker = None

'''

content = content.replace(
    '\n    # ========================================================\n    # CHARACTER VISIBILITY',
    voice_methods + '\n    # ========================================================\n    # CHARACTER VISIBILITY'
)

# 5. Update set_processing_state to also disable mic button
content = content.replace(
    '''        self.send_button.setEnabled(
            not self.is_processing
        )

        self.new_chat_button.setEnabled(
            not self.is_processing
        )''',
    '''        self.send_button.setEnabled(
            not self.is_processing
        )

        self.new_chat_button.setEnabled(
            not self.is_processing
        )

        if not self.is_processing:

            self.mic_button.setEnabled(
                True
            )'''
)

# 6. Update closeEvent to stop voice input
content = content.replace(
    '''        self.is_closing = True

        try:

            stop_speaking()''',
    '''        self.is_closing = True

        try:

            if self.voice_input_worker is not None:

                self.voice_input_worker.request_stop()

        except Exception:

            pass

        try:

            stop_speaking()'''
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py patched successfully")
