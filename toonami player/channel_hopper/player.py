"""VLC-backed playback controller for the Midnight Signal app.

This file owns the libVLC media player integration, stream state tracking, and volume/playback toggles.
"""

# Playback integration: initialize libVLC and expose a lightweight media controller to the UI.
import sys

import vlc
from PySide6.QtCore import QObject, QTimer, Signal


class StreamPlayer(QObject):
    """Wrap the underlying media player and emit status updates for the UI."""

    status_changed = Signal(str)

    # Player setup: initialize VLC, create the player instance, and start state polling.
    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = None
        self._player = None
        self._paused = False
        self._status = "unavailable"
        self._state_timer = QTimer(self)
        self._state_timer.setInterval(1000)
        self._state_timer.timeout.connect(self._refresh_state)

        try:
            self._instance = vlc.Instance("--no-video-title-show")
            if self._instance is None:
                raise RuntimeError("VLC could not be initialized")
            self._player = self._instance.media_player_new()
            self._status = "ready"
        except Exception as error:
            print(f"Could not initialize VLC: {error}", file=sys.stderr)

    # Playback availability: true when the underlying libVLC player instance exists.
    @property
    def available(self):
        return self._player is not None

    # Video output wiring: attach VLC to the Qt frame used for the stream preview.
    def attach_video_output(self, window_id):
        if self._player is not None:
            self._player.set_xwindow(window_id)

    # Stream launching: open the selected feed and begin playback with the current volume.
    def play(self, url, volume):
        if self._player is None:
            return False
        try:
            media = self._instance.media_new(url)
            self._player.set_media(media)
            self._player.audio_set_volume(volume)
            if self._player.play() == -1:
                raise RuntimeError("VLC could not start the stream")
        except Exception as error:
            print(f"Could not play stream: {error}", file=sys.stderr)
            self._set_status("error")
            return False

        self._paused = False
        self._set_status("connecting")
        self._state_timer.start()
        return True

    # Playback toggle: pause or resume the active stream without leaving the current channel.
    def toggle(self):
        if self._player is None:
            return
        if self._paused:
            self._player.play()
            self._paused = False
            self._set_status("connecting")
        elif self._player.is_playing():
            self._player.pause()
            self._paused = True
            self._set_status("paused")

    # Volume control: send the selected slider value directly to libVLC.
    def set_volume(self, volume):
        if self._player is not None:
            self._player.audio_set_volume(volume)

    # State polling: update the UI when VLC reports an error or successful playback.
    def _refresh_state(self):
        if self._player is None:
            return
        state = self._player.get_state()
        if state == vlc.State.Error:
            self._state_timer.stop()
            self._set_status("error")
        elif state == vlc.State.Playing:
            self._set_status("playing")

    # Status signal: emit app-visible state changes for the main window to react to.
    def _set_status(self, status):
        if self._status != status:
            self._status = status
            self.status_changed.emit(status)

    # Cleanup: stop the stream and release VLC objects before the app exits.
    def close(self):
        self._state_timer.stop()
        if self._player is not None:
            self._player.stop()
            self._player.release()
            self._player = None
        if self._instance is not None:
            self._instance.release()
            self._instance = None
