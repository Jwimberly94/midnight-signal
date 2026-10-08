"""Application entry point for the Midnight Signal desktop player.

This file boots the Qt application, applies the Wayland/X11 compatibility fix,
and launches the main ChannelPlayer window.
"""

# Platform compatibility: use X11 for QtWebEngine/VLC when running under Wayland.
import os
import sys

if (
    os.environ.get("XDG_SESSION_TYPE") == "wayland"
    and os.environ.get("DISPLAY")
    and os.environ.get("QT_QPA_PLATFORM") not in {"offscreen", "minimal"}
):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Qt application bootstrap.
from PySide6.QtWidgets import QApplication

from channel_hopper.main_window import ChannelPlayer


# Main startup function: create the app, show the main window, and run the event loop.
def main():
    app = QApplication(sys.argv)
    window = ChannelPlayer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
