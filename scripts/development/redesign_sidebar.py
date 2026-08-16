with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# =================================================
# REPLACE THE SIDEBAR SECTION
# =================================================

# Find the sidebar section
sidebar_mark = "        # ===================================================="
sidebar_mark += "\n        # SIDEBAR"
sidebar_idx = content.find(sidebar_mark)

if sidebar_idx >= 0:
    # Find the "RIGHT SIDE" marker to know where the sidebar ends
    right_side_mark = "        # ===================================================="
    right_side_idx = content.find(right_side_mark, sidebar_idx + 100)
    
    if right_side_idx >= 0:
        # The new sidebar HTML
        new_sidebar = '''
        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "Sidebar"
        )

        self.sidebar.setMinimumWidth(
            60
        )

        self.sidebar.setMaximumWidth(
            200
        )

        self.sidebar.setStyleSheet("""
            #Sidebar {
                background-color: rgba(10, 10, 15, 230);
                border-right: 1px solid rgba(128, 128, 128, 0.2);
                border-radius: 0px 0px 0px 12px;
            }
        """)
        
        self.apply_shadow(
            self.sidebar,
            blur=12,
            offset=0,
            alpha=80,
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        sidebar_layout.setSpacing(
            10
        )

        # ====================================================
        # AVORA BRAND
        # ====================================================

        brand_label = QLabel()
        brand_label.setPixmap(
            QPixmap(":/avora_logo_white.png").scaled(32, 32, Qt.KeepAspectRatioByHeight)
        )
        brand_label.setAlignment(Qt.AlignCenter)

        brand_text = QLabel("<b>AVORA</b>")
        brand_text.setObjectName("SidebarBrand")
        brand_text.setStyleSheet("""
            color: #F9FAFB;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-top: 8px;
        """)

        sidebar_layout.addWidget(brand_label)
        sidebar_layout.addWidget(brand_text)
        sidebar_layout.addSpacing(24)

        # ====================================================
        # NEW CHAT BUTTON
        # ====================================================

        self.new_chat_button = QPushButton("+")
        self.new_chat_button.setObjectName("NewChatButton")

        self.new_chat_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.new_chat_button.clicked.connect(
            self.create_new_chat
        )

        self.new_chat_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B7AFF, stop:1 #6C63FF);
                border: none;
                border-radius: 10px;
                padding: 12px;
                color: #FFFFFF;
                font-size: 20px;
                font-weight: 600;
                min-width: 36px;
                min-height: 36px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9E91FF, stop:1 #817AFF);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C63FF, stop:1 #5149D8);
            }
        """)

        sidebar_layout.addWidget(
            self.new_chat_button,
            0,
            Qt.AlignCenter
        )

        sidebar_layout.addSpacing(12)

        # ====================================================
        # VOICE TOGGLE
        # ====================================================

        self.voice_button = QPushButton()
        self.voice_button.setObjectName("VoiceButton")

        self.voice_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.voice_button.clicked.connect(
            self.toggle_voice
        )

        self.update_voice_button()

        sidebar_layout.addWidget(
            self.voice_button,
            0,
            Qt.AlignCenter
        )

        sidebar_layout.addSpacing(12)

        # ====================================================
        # SETTINGS BUTTON
        # ====================================================

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("SettingsButton")

        self.settings_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        self.settings_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8B7AFF;
                font-size: 18px;
                font-weight: 500;
                padding: 4px;
            }
            QPushButton:hover {
                color: #A78BFA;
            }
        """)

        sidebar_layout.addWidget(
            self.settings_button,
            0,
            Qt.AlignCenter
        )

        sidebar_layout.addStretch()

        # ====================================================
        # MINI CHARACTER CONTAINER
        # ====================================================

        self.mini_character = Character(parent=self.sidebar)
        self.mini_character.setFixedSize(40, 50)
        self.mini_character.hide()

        sidebar_layout.addWidget(
            self.mini_character,
            0,
            Qt.AlignCenter
        )

        # Store reference to full character for toggling
        self.mini_character_mode = True

'''
        # Replace the old sidebar section with the new one
        # Find the exact position to insert
        right_side_marker = "        # ===================================================="
        right_side_idx = content.find(right_side_marker, sidebar_idx + 100)
        
        if right_side_idx >= 0:
            content = content[:sidebar_idx] + new_sidebar + content[right_side_idx:]
            print("Replaced sidebar section")
        else:
            print("Could not find right side marker")
    else:
        print("Could not find sidebar section")
else:
    print("Could not find sidebar section")

# Write the modified content back
with open('C:\\Users\\minaj\\OneDrive\\Desktop\\avora\\avora backend\\main.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print("Sidebar redesign complete")