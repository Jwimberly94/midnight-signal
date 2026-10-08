"""Main Qt window and controller logic for the Midnight Signal app.

This file defines the full user interface, schedule browser, and channel-control logic.
"""

# UI dependencies: Qt widgets and browser controls used across the main window.
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from channel_hopper.channels import CHANNELS
from channel_hopper.player import StreamPlayer
from channel_hopper.schedules import SCHEDULES


# Main application window: UI shell, channel switching, playback controls, and tabs.
class ChannelPlayer(QMainWindow):
    # Window setup: initialize state, build the interface, and attach keyboard shortcuts.
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Midnight Signal // Channel Hopper")
        self.resize(1120, 700)
        self.setMinimumSize(800, 520)

        self.current_channel = None
        self._was_maximized = False
        self._last_volume = 70
        self.channel_buttons = {}
        self._build_ui()

        self.stream_player = StreamPlayer(self)
        self.stream_player.status_changed.connect(self._on_player_status)
        self.play_button.setEnabled(self.stream_player.available)
        QTimer.singleShot(
            0,
            lambda: self.stream_player.attach_video_output(int(self.video_frame.winId())),
        )
        if self.stream_player.available:
            self.status_label.setText("SYSTEM READY // SELECT A FEED")
        else:
            self.status_label.setText("VLC MISSING // INSTALL PLAYER")
            self.live_label.setText("PLAYER MISSING")

        self._fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self._fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        self._escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self._escape_shortcut.activated.connect(self.exit_fullscreen)
        self._space_shortcut = QShortcut(QKeySequence("Space"), self)
        self._space_shortcut.activated.connect(self.toggle_playback)
        self._mute_shortcut = QShortcut(QKeySequence("M"), self)
        self._mute_shortcut.activated.connect(self.toggle_mute)
        self._quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self._quit_shortcut.activated.connect(self.close)

    # Layout builder: construct the sidebar, video panel, tabs, and styling.
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        brand = QLabel("MIDNIGHT SIGNAL")
        brand.setObjectName("appBrand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(brand)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(20, 24, 16, 20)
        side_layout.setSpacing(8)

        eyebrow = QLabel("AFTER DARK / ANIMATION FEED")
        eyebrow.setObjectName("eyebrow")
        side_layout.addWidget(eyebrow)
        side_layout.addSpacing(16)

        for index, channel in enumerate(CHANNELS, start=1):
            button = QPushButton(f"{index:02}  /  {channel.upper()}")
            button.setObjectName("channelButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=channel: self.play_channel(name))
            self.channel_buttons[channel] = button
            side_layout.addWidget(button)

        side_layout.addStretch(1)
        self.status_label = QLabel("SYSTEM READY // SELECT A FEED")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        side_layout.addWidget(self.status_label)

        player_page = QWidget()
        player_page.setObjectName("content")
        self.content_layout = QVBoxLayout(player_page)
        self.content_layout.setContentsMargins(26, 24, 26, 20)
        self.content_layout.setSpacing(16)

        self.heading_widget = QWidget()
        heading = QHBoxLayout(self.heading_widget)
        heading.setContentsMargins(0, 0, 0, 0)
        self.channel_title = QLabel("AWAITING SIGNAL")
        self.channel_title.setObjectName("channelTitle")
        self.live_label = QLabel("READY")
        self.live_label.setObjectName("liveLabel")
        heading.addWidget(self.channel_title)
        heading.addStretch(1)
        heading.addWidget(self.live_label)
        self.content_layout.addWidget(self.heading_widget)

        self.video_frame = QFrame()
        self.video_frame.setObjectName("videoFrame")
        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.video_frame.setMinimumSize(480, 270)
        self.content_layout.addWidget(self.video_frame, 1)

        controls = QHBoxLayout()
        controls.setSpacing(12)
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("playButton")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_button)

        volume_label = QLabel("VOLUME")
        volume_label.setObjectName("eyebrow")
        controls.addStretch(1)
        controls.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self._set_volume)
        controls.addWidget(self.volume_slider)

        self.fullscreen_button = QPushButton("FULLSCREEN")
        self.fullscreen_button.setObjectName("fullscreenButton")
        self.fullscreen_button.setToolTip("Toggle fullscreen (F11; Escape exits)")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        controls.addWidget(self.fullscreen_button)

        self.exit_button = QPushButton("EXIT APP")
        self.exit_button.setObjectName("exitButton")
        self.exit_button.setToolTip("Close the app (Ctrl+Q)")
        self.exit_button.clicked.connect(self.close)
        controls.addWidget(self.exit_button)
        self.content_layout.addLayout(controls)

        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("mainTabs")
        self.main_tabs.addTab(player_page, "ON AIR")
        self.main_tabs.addTab(self._build_help_page(), "HELP")
        self.main_tabs.addTab(self._build_schedule_page(), "SCHEDULES")
        self.main_tabs.addTab(self._build_rights_page(), "RIGHTS")
        self.main_tabs.currentChanged.connect(self._on_main_tab_changed)

        self.sidebar = sidebar
        self.brand_header = brand
        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.main_tabs, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(
            """
            QWidget#root {
                background: #10131a; color: #eee7d7;
                font-family: "DejaVu Sans Mono";
            }
            QLabel#appBrand {
                color: #e76554; background: #1a1e26; border-bottom: 1px solid #393c41;
                padding: 14px; font-size: 18px; font-weight: 900;
            }
            QWidget#sidebar { background: #1a1e26; border-right: 1px solid #393c41; }
            QWidget#content { background: #10131a; }
            QTabWidget#mainTabs::pane { border: none; background: #10131a; }
            QTabBar::tab {
                color: #aeb4b4; background: #1a1e26; border: none;
                border-bottom: 2px solid #393c41; padding: 10px 18px;
                font-size: 10px; font-weight: 800;
            }
            QTabBar::tab:selected { color: #f0cc79; border-bottom: 2px solid #e76554; }
            QTabBar::tab:hover:!selected { color: #77d8c8; }
            QWidget#schedulePage { background: #10131a; }
            QLabel#scheduleTitle { color: #f0cc79; font-size: 18px; font-weight: 900; }
            QLabel#scheduleStatus { color: #77d8c8; font-size: 10px; font-weight: 800; }
            QPushButton#scheduleSource, QPushButton#openSourceButton {
                color: #d8d5cc; background: #1a1e26; border: 1px solid #393c41;
                padding: 9px 12px; font-size: 10px; font-weight: 800;
            }
            QPushButton#scheduleSource:hover, QPushButton#openSourceButton:hover {
                color: #77d8c8; border-color: #77d8c8;
            }
            QPushButton#scheduleSource:checked {
                color: #1a1110; background: #e76554; border-color: #e76554;
            }
            QWebEngineView#scheduleBrowser { background: #05070b; border: 1px solid #4a4640; }
            QLabel#brand { color: #e76554; font-size: 16px; font-weight: 900; }
            QLabel#eyebrow { color: #dfb763; font-size: 10px; font-weight: 800; }
            QLabel#channelTitle { color: #f0cc79; font-size: 20px; font-weight: 800; }
            QLabel#liveLabel {
                color: #171513; background: #e76554; padding: 5px 9px;
                font-size: 10px; font-weight: 900;
            }
            QLabel#status { color: #aeb4b4; font-size: 10px; }
            QFrame#videoFrame { background: #05070b; border: 2px solid #dfb763; }
            QPushButton#channelButton {
                text-align: left; color: #d8d5cc; background: transparent;
                border: 1px solid transparent; border-bottom: 1px solid #30343a;
                padding: 12px 10px; font-size: 11px; font-weight: 700;
            }
            QPushButton#channelButton:hover { color: #77d8c8; background: #252a30; }
            QPushButton#channelButton:checked {
                color: #f0cc79; background: #302b2b; border-left: 3px solid #e76554;
            }
            QPushButton#playButton, QPushButton#fullscreenButton {
                color: #1a1110; background: #e76554; border: none;
                padding: 10px 24px; font-weight: 900;
            }
            QPushButton#playButton:hover, QPushButton#fullscreenButton:hover { background: #f17c64; }
            QPushButton#exitButton {
                color: #d8d5cc; background: #1a1e26; border: 1px solid #e76554;
                padding: 9px 14px; font-weight: 800;
            }
            QPushButton#exitButton:hover { color: #1a1110; background: #e76554; }
            QPushButton#playButton:disabled { color: #777b7a; background: #35383a; }
            QWidget#helpPage { background: #10131a; }
            QLabel#helpTitle { color: #f0cc79; font-size: 22px; font-weight: 900; }
            QLabel#helpSubtitle { color: #e76554; font-size: 10px; font-weight: 800; }
            QLabel#helpColumn { color: #77d8c8; font-size: 10px; font-weight: 800; }
            QLabel#helpKey {
                color: #f0cc79; background: #1a1e26; border: 1px solid #4a4640;
                padding: 8px 10px; font-size: 10px; font-weight: 800;
            }
            QLabel#helpAction {
                color: #d8d5cc; border-bottom: 1px solid #30343a;
                padding: 8px 4px; font-size: 11px;
            }
            QWidget#rightsPage { background: #10131a; }
            QLabel#rightsTitle { color: #f0cc79; font-size: 22px; font-weight: 900; }
            QLabel#rightsSubtitle { color: #e76554; font-size: 10px; font-weight: 800; }
            QLabel#rightsText { color: #d8d5cc; font-size: 12px; }
            QSlider::groove:horizontal { height: 4px; background: #42464a; }
            QSlider::sub-page:horizontal { background: #77d8c8; }
            QSlider::handle:horizontal {
                width: 12px; margin: -5px 0; background: #f0cc79; border-radius: 0;
            }
            """
        )

    # Help tab: explain the key bindings and UI actions for operators using the app.
    def _build_help_page(self):
        page = QWidget()
        page.setObjectName("helpPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 34, 40, 28)
        layout.setSpacing(14)

        title = QLabel("OPERATOR'S GUIDE")
        title.setObjectName("helpTitle")
        subtitle = QLabel("CONTROL DECK // QUICK REFERENCE")
        subtitle.setObjectName("helpSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        input_heading = QLabel("CONTROL / KEY")
        input_heading.setObjectName("helpColumn")
        action_heading = QLabel("ACTION")
        action_heading.setObjectName("helpColumn")
        grid.addWidget(input_heading, 0, 0)
        grid.addWidget(action_heading, 0, 1)

        help_rows = (
            ("CHANNEL RAIL", "Select a feed to tune it immediately."),
            ("PLAY / PAUSE", "Start or pause the selected feed."),
            ("SPACE", "Toggle playback. With no feed selected, starts Toonami East."),
            ("VOLUME SLIDER", "Set playback volume; M mutes and restores the last level."),
            ("F11", "Enter fullscreen or return to the window."),
            ("ESC", "Exit fullscreen and return to the player."),
            ("EXIT APP / CTRL+Q", "Close the app and stop the active stream."),
            ("FULLSCREEN", "Expand the video area; playback controls stay visible."),
        )
        for row_number, (key, action) in enumerate(help_rows, start=1):
            key_label = QLabel(key)
            key_label.setObjectName("helpKey")
            action_label = QLabel(action)
            action_label.setObjectName("helpAction")
            action_label.setWordWrap(True)
            grid.addWidget(key_label, row_number, 0)
            grid.addWidget(action_label, row_number, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)
        layout.addLayout(grid)
        layout.addStretch(1)
        return page

    # Schedule tab: choose a source and load its schedule into the embedded browser.
    def _build_schedule_page(self):
        self.schedule_page = QWidget()
        self.schedule_page.setObjectName("schedulePage")
        layout = QVBoxLayout(self.schedule_page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        heading = QHBoxLayout()
        self.schedule_title = QLabel("PROGRAM GUIDE")
        self.schedule_title.setObjectName("scheduleTitle")
        self.schedule_status = QLabel("SOURCE NOT LOADED")
        self.schedule_status.setObjectName("scheduleStatus")
        heading.addWidget(self.schedule_title)
        heading.addStretch(1)
        heading.addWidget(self.schedule_status)
        layout.addLayout(heading)

        source_row = QHBoxLayout()
        source_row.setSpacing(8)
        self.schedule_source_buttons = {}
        self.schedule_source_group = QButtonGroup(self.schedule_page)
        self.schedule_source_group.setExclusive(True)
        for source in SCHEDULES:
            button = QPushButton(source.upper())
            button.setObjectName("scheduleSource")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=source: self._load_schedule(name))
            self.schedule_source_group.addButton(button)
            self.schedule_source_buttons[source] = button
            source_row.addWidget(button)
        source_row.addStretch(1)

        self.open_source_button = QPushButton("OPEN SOURCE")
        self.open_source_button.setObjectName("openSourceButton")
        self.open_source_button.clicked.connect(self._open_schedule_source)
        source_row.addWidget(self.open_source_button)
        layout.addLayout(source_row)

        self.schedule_browser = QWebEngineView()
        self.schedule_browser.setObjectName("scheduleBrowser")
        self.schedule_browser.loadStarted.connect(
            lambda: self.schedule_status.setText("CONNECTING TO SCHEDULE")
        )
        self.schedule_browser.loadFinished.connect(self._on_schedule_loaded)
        layout.addWidget(self.schedule_browser, 1)
        self._schedule_initialized = False
        return self.schedule_page

    # Rights tab: display attribution and third-party source information for the app.
    def _build_rights_page(self):
        page = QWidget()
        page.setObjectName("rightsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 34, 40, 28)
        layout.setSpacing(14)

        title = QLabel("RIGHTS & CREDITS")
        title.setObjectName("rightsTitle")
        subtitle = QLabel("INDEPENDENT PLAYER // THIRD-PARTY SOURCES")
        subtitle.setObjectName("rightsSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        credits = QLabel(
            '<b>APP CREATOR</b><br>Joshua Wimberly<br><br>'
            '<b>TOONAMI AFTERMATH</b><br>'
            'Stream feeds and schedule: '
            '<a href="https://www.toonamiaftermath.com/">toonamiaftermath.com</a><br>'
            'Stream endpoint host: api.toonamiaftermath.com<br><br>'
            '<b>RETROBLAST</b><br>'
            'Stream: <a href="https://retroblast.tv/">retroblast.tv</a><br>'
            'Schedule: <a href="https://docs.google.com/spreadsheets/d/'
            '1JzGvY5st6Z8x0w5vh7L6vuzh34bZKjMl0zMi328xOT8/edit?gid=0#gid=0">'
            'public schedule sheet</a><br><br>'
            'All third-party names, marks, streams, schedules, and other content '
            'remain the property of their respective owners. Midnight Signal is '
            'an independent player and is not affiliated with or endorsed by '
            'these services.'
        )
        credits.setObjectName("rightsText")
        credits.setWordWrap(True)
        credits.setOpenExternalLinks(True)
        layout.addWidget(credits)
        layout.addStretch(1)
        return page

    # Tab handling: load the initial schedule when the schedule tab is selected.
    def _on_main_tab_changed(self, index):
        if (
            self.main_tabs.widget(index) is self.schedule_page
            and not self._schedule_initialized
        ):
            self._load_schedule("Toonami Aftermath")

    # Schedule loading: update the browser to show the chosen program guide.
    def _load_schedule(self, source):
        self._schedule_initialized = True
        self.schedule_title.setText(source.upper() + " // SCHEDULE")
        self.schedule_status.setText("CONNECTING TO SCHEDULE")
        self.schedule_source_buttons[source].setChecked(True)
        self.schedule_browser.setUrl(QUrl(SCHEDULES[source]))

    # Schedule state updates: reflect network and page status in the UI.
    def _on_schedule_loaded(self, succeeded):
        if succeeded:
            self.schedule_status.setText("SCHEDULE READY")
        else:
            self.schedule_status.setText("LOAD FAILED // OPEN SOURCE")

    # External portal: open the current schedule source in the default browser.
    def _open_schedule_source(self):
        url = self.schedule_browser.url()
        if url.isEmpty():
            url = QUrl(SCHEDULES["Toonami Aftermath"])
        QDesktopServices.openUrl(url)

    # Channel selection: tune the app to a specific live stream.
    def play_channel(self, channel):
        if not self.stream_player.available:
            return
        self.current_channel = channel
        for name, button in self.channel_buttons.items():
            button.setChecked(name == channel)
        self.channel_title.setText(channel)
        self._on_player_status("connecting")
        self.stream_player.play(CHANNELS[channel], self.volume_slider.value())
        self.play_button.setText("Pause")

    # Playback controls: start, pause, and toggle the current stream.
    def toggle_playback(self):
        if self.current_channel is None:
            self.play_channel("Toonami East")
            return
        self.stream_player.toggle()

    # Fullscreen mode: hide the chrome and focus the stream panel.
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
            return
        self.main_tabs.setCurrentIndex(0)
        self._was_maximized = self.isMaximized()
        self.brand_header.hide()
        self.sidebar.hide()
        self.heading_widget.hide()
        self.main_tabs.tabBar().hide()
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(8)
        self.fullscreen_button.setText("EXIT FULLSCREEN")
        self.showFullScreen()

    # Exit fullscreen: restore the standard app layout and any maximized state.
    def exit_fullscreen(self):
        if not self.isFullScreen():
            return
        self.showNormal()
        self.brand_header.show()
        self.sidebar.show()
        self.heading_widget.show()
        self.main_tabs.tabBar().show()
        self.content_layout.setContentsMargins(26, 24, 26, 20)
        self.content_layout.setSpacing(16)
        self.fullscreen_button.setText("FULLSCREEN")
        if self._was_maximized:
            self.showMaximized()

    # Audio muting: restore the previous volume level or silence the stream.
    def toggle_mute(self):
        if self.volume_slider.value() == 0:
            self.volume_slider.setValue(self._last_volume or 70)
        else:
            self._last_volume = self.volume_slider.value()
            self.volume_slider.setValue(0)

    # Volume updates: keep the slider and libVLC in sync.
    def _set_volume(self, volume):
        if volume > 0:
            self._last_volume = volume
        if hasattr(self, "stream_player"):
            self.stream_player.set_volume(volume)

    # Player status mapping: reflect stream and connection states in the UI labels.
    def _on_player_status(self, status):
        if status == "playing":
            self.live_label.setText("LIVE")
            self.status_label.setText(f"SIGNAL LOCKED // {self.current_channel.upper()}")
            self.play_button.setText("Pause")
        elif status == "connecting":
            self.live_label.setText("CONNECTING")
            self.status_label.setText(f"TUNING IN // {self.current_channel.upper()}")
            self.play_button.setText("Pause")
        elif status == "paused":
            self.live_label.setText("PAUSED")
            self.status_label.setText("SIGNAL PAUSED")
            self.play_button.setText("Play")
        elif status == "error":
            self.live_label.setText("STREAM ERROR")
            self.status_label.setText("SIGNAL LOST // CHECK FEED")
            self.play_button.setText("Play")

    # Window close: shut down the VLC player before exiting the application.
    def closeEvent(self, event):
        self.stream_player.close()
        event.accept()
